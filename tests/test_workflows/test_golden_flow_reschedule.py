# -*- coding: utf-8 -*-
"""
Golden Flow 2: Reschedule Appointment (End-to-End)
Tests rescheduling flow: request -> auth -> reschedule -> confirmation
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
    async def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None, **kwargs):
        return ModelResponse(content="Okay, I rescheduled that for you.", model="mock")

    async def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        prompt_lower = prompt.lower()
        if "reschedule" in prompt_lower or "move" in prompt_lower:
            return {"intent": "RescheduleAppointment", "entities": {}}
        if "schedule" in prompt_lower or "appointment" in prompt_lower or "book" in prompt_lower:
            return {"intent": "ScheduleAppointment", "entities": {}}
        if "lab" in prompt_lower or "result" in prompt_lower:
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
async def test_reschedule_full_flow(dialogue_manager):
    """
    Reschedule flow:
    1. User requests reschedule -> System prompts for auth
    2. User provides credentials -> System authenticates
    3. User provides appointment id + new slot -> System reschedules
    """
    state = ConversationState()

    # Turn 1: User requests reschedule (unauthenticated)
    result1 = await dialogue_manager.execute({"utterance": "I need to reschedule my appointment", "state": state})
    assert result1.metadata.get("auth_prompted") == True
    prompt_text = result1.output.get("text", "").lower()
    assert "full name" in prompt_text and "date of birth" in prompt_text

    # Turn 2: Provide auth credentials
    state1 = ConversationState.from_dict(result1.output["state"])
    result2 = await dialogue_manager.execute({
        "utterance": "Alicia Thompson April 12, 1985",
        "state": state1,
        "patient_name": "Alicia Thompson",
        "dob": "1985-04-12",
    })

    state2 = ConversationState.from_dict(result2.output.get("state"))
    assert state2.patient_id == "P-1001"

    # Turn 3: Reschedule appointment A-501 to S-200-2
    result3 = await dialogue_manager.execute({
        "utterance": "Please reschedule my appointment to the next available slot",
        "state": state2,
        "appointment_id": "A-501",
        "new_slot": "S-200-2",
    })

    assert result3.status == AgentStatus.SUCCESS
    assert "appointment" in result3.output
    assert result3.output["appointment"]["slot_id"] == "S-200-2"

    print("✓ Golden Flow 2: Reschedule appointment - PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
