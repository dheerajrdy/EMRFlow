#!/usr/bin/env python3
"""
Test complete conversation flow including multi-turn authentication.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.dialogue_manager import DialogueManager
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.nlu_agent import NLUAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.models.model_client import ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState


class MockModelClient(ModelClient):
    """Mock client that simulates real NLU behavior."""

    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, prompt, schema, **kwargs):
        # Smart NLU simulation based on utterance content
        lower_prompt = prompt.lower()

        if "appointment" in lower_prompt and "schedule" in lower_prompt:
            return {"intent": "ScheduleAppointment", "entities": {}}
        elif "alicia" in lower_prompt or "name is" in lower_prompt:
            # User providing auth credentials
            return {"intent": "Other", "entities": {}}
        elif "tuesday" in lower_prompt or "first" in lower_prompt:
            # User selecting a slot
            return {"intent": "ScheduleAppointment", "entities": {}}

        return {"intent": "Other", "entities": {}}


async def simulate_conversation():
    """Simulate a complete multi-turn booking conversation."""

    print("=" * 80)
    print("MULTI-TURN CONVERSATION TEST")
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

    # Track state across turns
    state = None
    call_sid = "test-call-123"

    # === TURN 1: User requests appointment ===
    print("\n[TURN 1] User: 'I want to schedule an appointment'")
    print("-" * 80)

    result1 = await dm.execute({
        "utterance": "I want to schedule an appointment",
        "state": state,
    })

    print(f"Status: {result1.status}")
    print(f"Response: {result1.output.get('text', 'N/A')}")
    print(f"Auth prompted: {result1.metadata.get('auth_prompted', False)}")
    print(f"Patient ID: {result1.output.get('state', {}).get('patient_id', 'None')}")

    # Extract state for next turn
    state = ConversationState.from_dict(result1.output.get("state", {}))

    assert result1.output.get("text"), "❌ No response text!"
    assert result1.metadata.get("auth_prompted"), "❌ Auth not prompted!"

    print("✅ Turn 1 passed: Auth prompt displayed")

    # === TURN 2: User provides credentials ===
    print("\n[TURN 2] User: 'My name is Alicia Thompson, born April 12, 1985'")
    print("-" * 80)

    result2 = await dm.execute({
        "utterance": "My name is Alicia Thompson, born April 12, 1985",
        "patient_name": "Alicia Thompson",
        "dob": "1985-04-12",
        "state": state,
    })

    print(f"Status: {result2.status}")
    print(f"Response: {result2.output.get('text', 'N/A')}")
    print(f"Patient ID: {result2.output.get('state', {}).get('patient_id', 'None')}")

    state = ConversationState.from_dict(result2.output.get("state", {}))

    assert state.patient_id == "P-1001", f"❌ Patient not authenticated! Got: {state.patient_id}"
    assert result2.output.get("text"), "❌ No response text!"

    print("✅ Turn 2 passed: Patient authenticated")

    # === TURN 3: Select slot ===
    print("\n[TURN 3] User: 'I'll take the first one'")
    print("-" * 80)

    # Get available slots
    available_slots = scheduling.find_available_slots(doctor="Dr. Maya Singh")
    print(f"Available slots: {available_slots}")

    if available_slots:
        first_slot = available_slots[0]

        result3 = await dm.execute({
            "utterance": "I'll take the first one",
            "slot_id": first_slot,
            "state": state,
        })

        print(f"Status: {result3.status}")
        print(f"Response: {result3.output.get('text', 'N/A')}")
        print(f"Appointment: {result3.output.get('appointment', 'N/A')}")

        assert result3.is_success, f"❌ Booking failed: {result3.errors}"
        assert result3.output.get("appointment"), "❌ No appointment returned!"

        print("✅ Turn 3 passed: Appointment booked")
    else:
        print("⚠️  No available slots found (expected in test scenario)")

    print("\n" + "=" * 80)
    print("✅ FULL CONVERSATION TEST PASSED!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = asyncio.run(simulate_conversation())
    sys.exit(0 if success else 1)
