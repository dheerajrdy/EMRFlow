from src.utils.conversation_state import ConversationState


def test_conversation_state_updates_and_serialization():
    state = ConversationState()
    state.add_turn("user", "hello")
    state.set_intent("FAQ")
    state.set_patient("P-1")
    state.update_slots(date="2025-12-15", doctor="Dr. Singh")
    state.set_step("awaiting_confirmation")

    data = state.to_dict()
    restored = ConversationState.from_dict(data)

    assert restored.current_intent == "FAQ"
    assert restored.patient_id == "P-1"
    assert restored.slots["doctor"] == "Dr. Singh"
    assert restored.history[0]["text"] == "hello"
    assert restored.step == "awaiting_confirmation"
