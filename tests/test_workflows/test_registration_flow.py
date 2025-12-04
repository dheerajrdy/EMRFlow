"""
End-to-end tests for new patient registration flow.

Tests the complete registration flow including:
- Explicit registration intent
- Auto-offer after failed authentication
- Duplicate detection
- Registration -> booking flow
"""

import pytest
from src.agents.dialogue_manager import DialogueManager
from src.agents.nlu_agent import NLUAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.agents.records_agent import RecordsAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.models.model_client import ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState
from src.utils.data_loader import DataLoader


class FakeModelClient(ModelClient):
    """Fake model client for testing."""

    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="fake")

    async def generate_structured(self, *args, **kwargs):
        # Raise exception to trigger NLU fallback rules
        raise Exception("Fake model - use fallback")


@pytest.fixture
def dialogue_manager_with_temp_data(tmp_path):
    """Create DialogueManager with temporary data directory."""
    # Set up temp data loader
    data_loader = DataLoader(data_dir=tmp_path)

    # Copy mock data to temp directory
    import json
    import shutil
    from pathlib import Path

    src_data_dir = Path(__file__).resolve().parent.parent.parent / "src" / "data"
    for filename in ["patients.json", "schedule.json", "faq.json"]:
        shutil.copy(src_data_dir / filename, tmp_path / filename)

    # Create agents with temp data
    model = FakeModelClient()
    nlu_agent = NLUAgent(model_client=model)
    records_agent = RecordsAgent(model_client=model, data_loader=data_loader)
    scheduling_agent = SchedulingAgent(model_client=model, data_loader=data_loader)
    knowledge_agent = KnowledgeAgent(model_client=model, data_loader=data_loader)

    dm = DialogueManager(
        model_client=model,
        nlu_agent=nlu_agent,
        scheduling_agent=scheduling_agent,
        records_agent=records_agent,
        knowledge_agent=knowledge_agent,
    )

    return dm, tmp_path


@pytest.mark.asyncio
async def test_explicit_registration_full_flow(dialogue_manager_with_temp_data):
    """Test explicit registration from start to finish."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()

    # Turn 1: User explicitly requests registration
    result1 = await dm.execute({"utterance": "I'm a new patient and need to register", "state": state})
    assert "full name" in result1.output["text"].lower()
    state1 = ConversationState.from_dict(result1.output["state"])
    assert state1.step == "registration_collecting_name"

    # Turn 2: Provide name
    result2 = await dm.execute({"utterance": "Sarah Johnson", "state": state1, "patient_name": "Sarah Johnson"})
    assert "date of birth" in result2.output["text"].lower()
    state2 = ConversationState.from_dict(result2.output["state"])
    assert state2.step == "registration_collecting_dob"
    assert state2.get_registration_field("name") == "Sarah Johnson"

    # Turn 3: Provide DOB
    result3 = await dm.execute({"utterance": "March 15, 1990", "state": state2, "dob": "1990-03-15"})
    assert "phone" in result3.output["text"].lower()
    state3 = ConversationState.from_dict(result3.output["state"])
    assert state3.step == "registration_collecting_phone"
    assert state3.get_registration_field("dob") == "1990-03-15"

    # Turn 4: Provide phone
    result4 = await dm.execute({"utterance": "4155550199", "state": state3})
    assert "email" in result4.output["text"].lower()
    state4 = ConversationState.from_dict(result4.output["state"])
    assert state4.step == "registration_collecting_email"
    assert state4.get_registration_field("phone") == "+1-415-555-0199"

    # Turn 5: Provide email - should complete registration
    result5 = await dm.execute({"utterance": "sarah@example.com", "state": state4})
    assert "registered" in result5.output["text"].lower()
    state5 = ConversationState.from_dict(result5.output["state"])
    assert state5.patient_id is not None
    assert state5.patient_id.startswith("P-")
    assert state5.step is None  # Registration complete

    # Verify patient was saved to file
    import json
    with open(tmp_path / "patients.json", "r") as f:
        data = json.load(f)
        assert len(data["patients"]) == 5  # 4 original + 1 new
        new_patient = data["patients"][-1]
        assert new_patient["name"] == "Sarah Johnson"
        assert new_patient["dob"] == "1990-03-15"
        assert new_patient["contact"]["phone"] == "+1-415-555-0199"
        assert new_patient["contact"]["email"] == "sarah@example.com"


@pytest.mark.asyncio
async def test_auto_offer_registration_after_failed_auth(dialogue_manager_with_temp_data):
    """Test system offers registration when patient not found during auth."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()

    # Simulate being in the middle of auth for ScheduleAppointment
    state.set_intent("ScheduleAppointment")

    # User provides complete credentials (name + DOB) that don't exist
    result = await dm.execute({
        "utterance": "schedule appointment",
        "state": state,
        "patient_name": "Marcus Chen",
        "dob": "1988-06-08"
    })

    # System should offer registration (patient not found)
    assert "register" in result.output["text"].lower() or "new patient" in result.output["text"].lower()
    state_after = ConversationState.from_dict(result.output["state"])
    assert state_after.step == "registration_offered"
    assert state_after.get_registration_field("name") == "Marcus Chen"
    assert state_after.get_registration_field("dob") == "1988-06-08"

    # User accepts registration
    result2 = await dm.execute({"utterance": "Yes please", "state": state_after})
    # Should skip name/DOB (already collected) and go to phone
    assert "phone" in result2.output["text"].lower()
    state2 = ConversationState.from_dict(result2.output["state"])
    assert state2.step == "registration_collecting_phone"

    # Provide phone
    result3 = await dm.execute({"utterance": "6505550123", "state": state2})
    assert "email" in result3.output["text"].lower()

    # Provide email - complete registration
    state3 = ConversationState.from_dict(result3.output["state"])
    result4 = await dm.execute({"utterance": "marcus@example.com", "state": state3})
    assert "registered" in result4.output["text"].lower()
    state4 = ConversationState.from_dict(result4.output["state"])
    assert state4.patient_id is not None
    assert state4.patient_id.startswith("P-")


@pytest.mark.asyncio
async def test_duplicate_detection_during_registration(dialogue_manager_with_temp_data):
    """Test system detects duplicate when existing patient tries to register."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()

    # Start registration flow
    state.set_step("registration_collecting_dob")
    state.set_registration_field("name", "Alicia Thompson")  # Existing patient

    result = await dm.execute({
        "utterance": "April 12, 1985",
        "state": state,
        "dob": "1985-04-12"  # Matches P-1001
    })

    # Should detect duplicate and authenticate instead
    assert "already registered" in result.output["text"].lower()
    state_after = ConversationState.from_dict(result.output["state"])
    assert state_after.patient_id == "P-1001"
    assert state_after.step is None


@pytest.mark.asyncio
async def test_registration_decline(dialogue_manager_with_temp_data):
    """Test user declines registration offer."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()

    # Simulate registration offered
    state.set_step("registration_offered")
    state.set_registration_field("name", "John Doe")
    state.set_registration_field("dob", "1990-01-01")

    result = await dm.execute({"utterance": "No thanks", "state": state})

    assert "call" in result.output["text"].lower()  # Offers phone number
    state_after = ConversationState.from_dict(result.output["state"])
    assert state_after.step is None
    assert state_after.get_registration_field("name") is None  # Cleared


@pytest.mark.asyncio
async def test_validation_error_invalid_phone(dialogue_manager_with_temp_data):
    """Test validation error handling for invalid phone."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()

    state.set_step("registration_collecting_phone")
    state.set_registration_field("name", "Test User")
    state.set_registration_field("dob", "1990-01-01")

    # Provide invalid phone
    result = await dm.execute({"utterance": "123", "state": state})

    assert result.is_failure
    assert "10-digit" in result.output["text"].lower()
    state_after = ConversationState.from_dict(result.output["state"])
    assert state_after.step == "registration_collecting_phone"  # Still on phone step


@pytest.mark.asyncio
async def test_validation_error_invalid_email(dialogue_manager_with_temp_data):
    """Test validation error handling for invalid email."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()

    state.set_step("registration_collecting_email")
    state.set_registration_field("name", "Test User")
    state.set_registration_field("dob", "1990-01-01")
    state.set_registration_field("phone", "+1-415-555-0199")

    # Provide invalid email
    result = await dm.execute({"utterance": "invalid", "state": state})

    assert result.is_failure
    assert "valid email" in result.output["text"].lower()
    state_after = ConversationState.from_dict(result.output["state"])
    assert state_after.step == "registration_collecting_email"  # Still on email step


@pytest.mark.asyncio
async def test_registration_then_booking(dialogue_manager_with_temp_data):
    """Test registration completes and patient can proceed to book."""
    dm, tmp_path = dialogue_manager_with_temp_data
    state = ConversationState()
    state.current_intent = "ScheduleAppointment"  # User's original intent

    # Complete registration
    state.set_step("registration_collecting_email")
    state.set_registration_field("name", "Emma Wilson")
    state.set_registration_field("dob", "1995-05-20")
    state.set_registration_field("phone", "+1-650-555-0123")

    result = await dm.execute({"utterance": "emma@example.com", "state": state})

    # Should complete registration successfully
    assert "registered" in result.output["text"].lower()
    state_after = ConversationState.from_dict(result.output["state"])
    assert state_after.patient_id is not None
    assert state_after.patient_id.startswith("P-")
    # Patient is now authenticated and can proceed with booking
    assert state_after.step is None  # Registration flow complete
