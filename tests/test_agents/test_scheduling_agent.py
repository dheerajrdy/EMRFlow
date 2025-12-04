import pytest

from src.agents.scheduling_agent import SchedulingAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


@pytest.fixture
def scheduling_agent():
    return SchedulingAgent(model_client=MockModelClient())


def test_find_available_slots(scheduling_agent):
    slots = scheduling_agent.find_available_slots(
        doctor="Dr. Maya Singh",
        date_range=("2025-12-14", "2025-12-23")
    )
    assert slots
    slot_ids = {slot["slot_id"] for slot in slots}
    assert "S-200-1" not in slot_ids  # already booked


def test_book_appointment_updates_state(scheduling_agent):
    appointment = scheduling_agent.book_appointment(
        patient_id="P-1004",
        slot="S-200-2"
    )
    assert appointment["slot_id"] == "S-200-2"
    patient = scheduling_agent._require_patient("P-1004")
    assert any(appt["slot_id"] == "S-200-2" for appt in patient["appointments"])

    doctor, slot = scheduling_agent._find_slot("S-200-2")
    assert slot["status"] == "booked"
    assert slot["patient_id"] == "P-1004"


def test_reschedule_moves_slot_and_frees_old(scheduling_agent):
    updated = scheduling_agent.reschedule_appointment(
        appointment_id="A-502",
        new_slot="S-210-2"
    )
    assert updated["slot_id"] == "S-210-2"
    _, new_slot = scheduling_agent._find_slot("S-210-2")
    assert new_slot["status"] == "booked"
    assert new_slot["patient_id"] == "P-1002"

    old_slot = scheduling_agent._find_slot_by_id("S-210-1")
    assert old_slot["status"] == "available"
    assert "patient_id" not in old_slot


def test_cancel_appointment(scheduling_agent):
    canceled = scheduling_agent.cancel_appointment("A-503")
    assert canceled["status"] == "canceled"
    slot = scheduling_agent._find_slot_by_id("S-220-1")
    assert slot["status"] == "available"
    assert "patient_id" not in slot


def test_double_booking_prevention(scheduling_agent):
    with pytest.raises(ValueError):
        scheduling_agent.book_appointment(patient_id="P-1004", slot="S-210-1")
