#!/usr/bin/env python3
"""
Test natural response generation with real Gemini model.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.agents.dialogue_manager import DialogueManager
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.nlu_agent import NLUAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.models.model_client import GoogleModelClient
from src.utils.conversation_state import ConversationState


async def test_natural_responses():
    """Test complete conversation with natural response generation."""

    print("=" * 80)
    print("TESTING NATURAL RESPONSE GENERATION WITH GEMINI")
    print("=" * 80)

    # Setup with REAL Gemini model
    try:
        model = GoogleModelClient()
        print("✅ Gemini model initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini: {e}")
        return False

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

    # Track state
    state = None

    # === TURN 1: User requests appointment ===
    print("\n" + "=" * 80)
    print("[TURN 1] User: 'I want to schedule an appointment'")
    print("=" * 80)

    result1 = await dm.execute({
        "utterance": "I want to schedule an appointment",
        "state": state,
    })

    response1 = result1.output.get("text", "")
    print(f"\n[ASSISTANT]: {response1}\n")
    print(f"Status: {result1.status}")
    print(f"Auth prompted: {result1.metadata.get('auth_prompted', False)}")

    state = ConversationState.from_dict(result1.output.get("state", {}))

    # === TURN 2: User provides credentials ===
    print("\n" + "=" * 80)
    print("[TURN 2] User: 'My name is Alicia Thompson, born April 12, 1985'")
    print("=" * 80)

    result2 = await dm.execute({
        "utterance": "My name is Alicia Thompson, born April 12, 1985",
        "patient_name": "Alicia Thompson",
        "dob": "1985-04-12",
        "state": state,
    })

    response2 = result2.output.get("text", "")
    print(f"\n[ASSISTANT]: {response2}\n")
    print(f"Status: {result2.status}")
    print(f"Patient authenticated: {result2.output.get('state', {}).get('patient_id')}")

    state = ConversationState.from_dict(result2.output.get("state", {}))

    # Check if response mentions slot options
    has_natural_response = len(response2) > 50  # Natural responses are longer
    print(f"\nNatural response generated: {'✅' if has_natural_response else '❌'}")
    print(f"Response length: {len(response2)} chars")

    # === TURN 3: Select slot ===
    print("\n" + "=" * 80)
    print("[TURN 3] User: 'I'll take the first one'")
    print("=" * 80)

    available_slots = scheduling.find_available_slots(doctor="Dr. Maya Singh")
    if available_slots:
        first_slot = available_slots[0]

        result3 = await dm.execute({
            "utterance": "I'll take the first one",
            "slot_id": first_slot["slot_id"],
            "state": state,
        })

        response3 = result3.output.get("text", "")
        print(f"\n[ASSISTANT]: {response3}\n")
        print(f"Status: {result3.status}")

        # Check if confirmation is natural
        has_details = any(word in response3.lower() for word in ["december", "room", "reminder", "perfect"])
        print(f"\nNatural confirmation generated: {'✅' if has_details else '❌'}")
        print(f"Response length: {len(response3)} chars")

    print("\n" + "=" * 80)
    print("✅ NATURAL RESPONSE TEST COMPLETE!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_natural_responses())
    sys.exit(0 if success else 1)
