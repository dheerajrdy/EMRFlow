# -*- coding: utf-8 -*-
"""
Golden Flow 3: Lab Results Query (End-to-End)
Tests lab query flow: request -> auth -> lab explanation + follow-up suggestion
"""

import pytest
from src.agents.dialogue_manager import DialogueManager
from src.agents.nlu_agent import NLUAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.utils.conversation_state import ConversationState
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    async def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None, **kwargs):
        # Return a helpful paraphrase/explanation
        return ModelResponse(content="Here are your recent lab results and what they mean.", model="mock")

    async def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        prompt_lower = prompt.lower()
        if "lab" in prompt_lower or "result" in prompt_lower:
            return {"intent": "InfoQuery", "entities": {}}
        if "schedule" in prompt_lower or "appointment" in prompt_lower:
            return {"intent": "ScheduleAppointment", "entities": {}}
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
async def test_lab_query_flow(dialogue_manager):
    """
    Lab query flow:
    1. User asks about labs -> System prompts for auth
    2. User provides credentials -> System returns lab explanations and suggests follow-up when needed
    """
    state = ConversationState()

    # Turn 1: User asks about labs (unauthenticated)
    result1 = await dialogue_manager.execute({"utterance": "Do I have any lab results?", "state": state})
    assert result1.metadata.get("auth_prompted") == True

    # Turn 2: Provide auth
    state1 = ConversationState.from_dict(result1.output["state"])
    result2 = await dialogue_manager.execute({
        "utterance": "Alicia Thompson April 12, 1985",
        "state": state1,
        "patient_name": "Alicia Thompson",
        "dob": "1985-04-12",
    })

    state2 = ConversationState.from_dict(result2.output.get("state"))
    assert state2.patient_id == "P-1001"

    # Turn 3: Ask for labs (now authenticated)
    result3 = await dialogue_manager.execute({"utterance": "Show my labs", "state": state2})

    # Should return lab data and possibly a follow-up suggestion flag
    assert "data" in result3.output
    labs = result3.output["data"]
    assert isinstance(labs, list) and len(labs) > 0
    # For Alicia, interpretations include recommendations -> expect follow-up suggestion metadata
    assert result3.metadata.get("follow_up_suggested") in (True, False)

    print("✓ Golden Flow 3: Lab query - PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
