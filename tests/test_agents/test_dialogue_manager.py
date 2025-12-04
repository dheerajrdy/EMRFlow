import pytest

from src.agents.dialogue_manager import DialogueManager
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.agents.base_agent import AgentResult, BaseAgent
from src.models.model_client import ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


class StubNLUAgent(BaseAgent):
    def __init__(self, intent: str, model_client):
        super().__init__(model_client)
        self.intent = intent

    async def execute(self, input_data):
        return self._create_success_result({"intent": self.intent, "entities": {}})


@pytest.fixture
def dialogue_manager_factory():
    def _build(intent: str):
        model = MockModelClient()
        nlu = StubNLUAgent(intent=intent, model_client=model)
        records = RecordsAgent(model_client=model)
        scheduling = SchedulingAgent(model_client=model)
        knowledge = KnowledgeAgent(model_client=model)
        return DialogueManager(
            model_client=model,
            nlu_agent=nlu,
            scheduling_agent=scheduling,
            records_agent=records,
            knowledge_agent=knowledge,
        )

    return _build


@pytest.mark.asyncio
async def test_schedule_with_auth(dialogue_manager_factory):
    dm = dialogue_manager_factory("ScheduleAppointment")
    state = ConversationState()
    result = await dm.execute(
        {
            "utterance": "I need to book an appointment",
            "patient_name": "Alicia Thompson",
            "dob": "1985-04-12",
            "slot_id": "S-200-2",
            "state": state,
        }
    )

    assert result.is_success
    assert result.output["appointment"]["slot_id"] == "S-200-2"
    assert result.output["state"]["patient_id"] == "P-1001"


@pytest.mark.asyncio
async def test_faq_no_auth_needed(dialogue_manager_factory):
    dm = dialogue_manager_factory("FAQ")
    result = await dm.execute({"utterance": "What are your hours?"})

    assert result.is_success
    assert "answer" in result.output


@pytest.mark.asyncio
async def test_auth_failure(dialogue_manager_factory):
    """Test auth flow when patient credentials are wrong (now offers registration)."""
    dm = dialogue_manager_factory("ScheduleAppointment")
    result = await dm.execute(
        {"utterance": "schedule", "patient_name": "Wrong Name", "dob": "1900-01-01"}
    )

    assert result.is_failure
    # New behavior: offers registration when patient not found
    assert "register" in result.errors[0].lower()
    assert "text" in result.output  # Response text should be present
    assert "state" in result.output  # State should be in output
    # Check registration was offered
    state = result.output.get("state", {})
    assert state.get("step") == "registration_offered"


@pytest.mark.asyncio
async def test_reschedule_flow(dialogue_manager_factory):
    dm = dialogue_manager_factory("RescheduleAppointment")
    result = await dm.execute(
        {
            "utterance": "reschedule me",
            "patient_name": "Brandon Lee",
            "dob": "1979-08-22",
            "appointment_id": "A-502",
            "new_slot": "S-210-2",
        }
    )

    assert result.is_success
    assert result.output["appointment"]["slot_id"] == "S-210-2"
