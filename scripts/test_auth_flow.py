#!/usr/bin/env python3
"""
Test script to debug the authentication flow issue.
Simulates the exact flow from the Twilio call logs.
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.dialogue_manager import DialogueManager
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.nlu_agent import NLUAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    """Mock client for testing without real API calls."""

    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, prompt, schema, **kwargs):
        # Simulate NLU classification for "I want to make an appointment"
        if "appointment" in prompt.lower():
            return {"intent": "ScheduleAppointment", "entities": {}}
        return {"intent": "Other", "entities": {}}


async def test_call_flow():
    """Simulate the exact flow from the Twilio logs."""

    print("=" * 80)
    print("SIMULATING TWILIO CALL FLOW")
    print("=" * 80)

    # Setup
    model = MockModelClient()
    nlu = NLUAgent(model_client=model)
    records = RecordsAgent(model_client=model)
    scheduling = SchedulingAgent(model_client=model)
    knowledge = KnowledgeAgent(model_client=model)

    dm = DialogueManager(
        model_client=model,
        nlu_agent=nlu,
        scheduling_agent=scheduling,
        records_agent=records,
        knowledge_agent=knowledge,
    )

    # Simulate Turn 1: User says "I want to make an appointment"
    print("\n[TURN 1] User: 'I want to make an appointment'")
    print("-" * 80)

    utterance = "I want to make an appointment"
    input_data = {
        "utterance": utterance,
        "state": None,
        # No patient_name or dob provided yet
    }

    result = await dm.execute(input_data)

    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Errors: {result.errors}")
    print(f"Metadata: {result.metadata}")

    # Extract response text (same logic as voice_server.py line 196)
    response_text = (
        result.output.get("text")
        or result.output.get("answer")
        or "I didn't catch that. Could you repeat?"
    )

    print(f"\n[SYSTEM RESPONSE]: {response_text}")

    # Check if auth_prompted
    auth_prompted = result.metadata.get("auth_prompted", False)
    print(f"Auth prompted: {auth_prompted}")

    # Check hang-up logic (voice_server.py line 206)
    should_end = ("goodbye" in utterance.lower() or
                  (result.status.value == "failure" and not auth_prompted))
    print(f"Should end call: {should_end}")

    print("\n" + "=" * 80)

    if should_end:
        print("❌ CALL WOULD HANG UP HERE (BUG!)")
    else:
        print("✅ CALL CONTINUES (CORRECT)")

    print("=" * 80)

    return result


if __name__ == "__main__":
    result = asyncio.run(test_call_flow())

    # Return exit code based on whether bug is present
    sys.exit(0 if result.metadata.get("auth_prompted") else 1)
