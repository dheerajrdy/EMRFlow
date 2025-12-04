# -*- coding: utf-8 -*-
"""
Golden Flow 1: New Appointment Booking (End-to-End)
Tests complete booking flow: request -> auth -> slot selection -> confirmation
"""

import pytest
from src.agents.dialogue_manager import DialogueManager
from src.agents.nlu_agent import NLUAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.utils.conversation_state import ConversationState
from src.agents.base_agent import AgentStatus
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    """Mock model client that returns realistic responses for booking flow."""

    async def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None, **kwargs):
        # Return realistic booking confirmation
        return ModelResponse(content="Great! I've scheduled your appointment.", model="mock")

    async def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        # Detect intent from prompt
        prompt_lower = prompt.lower()
        if "schedule" in prompt_lower or "appointment" in prompt_lower or "book" in prompt_lower:
            return {"intent": "ScheduleAppointment", "entities": {}}
        elif "reschedule" in prompt_lower or "move" in prompt_lower:
            return {"intent": "RescheduleAppointment", "entities": {}}
        elif "cancel" in prompt_lower:
            return {"intent": "CancelAppointment", "entities": {}}
        elif "lab" in prompt_lower or "result" in prompt_lower:
            return {"intent": "InfoQuery", "entities": {}}
        return {"intent": "Other", "entities": {}}


@pytest.fixture
def dialogue_manager():
    model_client = MockModelClient()
    return DialogueManager(
        model_client=model_client,
        nlu_agent=NLUAgent(model_client=model_client),
        scheduling_agent=SchedulingAgent(model_client=model_client),
        records_agent=RecordsAgent(model_client=model_client),
        knowledge_agent=KnowledgeAgent(model_client=model_client),
    )


@pytest.mark.asyncio
async def test_new_appointment_booking_full_flow(dialogue_manager):
    """
    Complete new appointment booking flow:
    1. User requests appointment -> System prompts for auth
    2. User provides credentials -> System authenticates and offers slots
    3. User selects slot -> System confirms booking
    """
    state = ConversationState()

    # Turn 1: User requests appointment (unauthenticated)
    result1 = await dialogue_manager.execute({
        "utterance": "I need to schedule an appointment",
        "state": state
    })

    assert result1.metadata.get("auth_prompted") == True, "Should prompt for authentication"
    prompt_text = result1.output.get("text", "").lower()
    assert "full name" in prompt_text and "date of birth" in prompt_text

    # Turn 2: User provides auth credentials
    state1 = ConversationState.from_dict(result1.output["state"])
    result2 = await dialogue_manager.execute({
        "utterance": "Alicia Thompson April 12, 1985",
        "state": state1,
        "patient_name": "Alicia Thompson",
        "dob": "1985-04-12"
    })

    state2 = ConversationState.from_dict(result2.output.get("state"))
    assert state2.patient_id == "P-1001", f"Should authenticate patient, got {state2.patient_id}"
    assert "options" in result2.output, "Should offer appointment slots"
    assert len(result2.output["options"]) > 0, "Should have available slots"

    # Turn 3: User selects slot
    slots = result2.output["options"]
    selected_slot_id = slots[0]["slot_id"]

    result3 = await dialogue_manager.execute({
        "utterance": "The first one works for me",
        "state": state2,
        "slot_id": selected_slot_id
    })

    assert result3.status == AgentStatus.SUCCESS, "Booking should succeed"
    assert "appointment" in result3.output, "Should return appointment data"
    assert result3.output["appointment"]["status"] == "scheduled"
    assert result3.output["appointment"]["slot_id"] == selected_slot_id

    print("✓ Golden Flow 1: New appointment booking - PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
