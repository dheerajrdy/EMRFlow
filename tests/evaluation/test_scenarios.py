import pytest

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.models.model_client import ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState
from tests.evaluation.eval_runner import run_eval_suite


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


class FakeDialogueManager(BaseAgent):
    """Deterministic DM for scenario evaluation."""

    def __init__(self):
        super().__init__(MockModelClient())

    async def execute(self, input_data):
        state = input_data.get("state") or ConversationState()
        utterance = input_data.get("utterance", "").lower()
        state.add_turn("user", utterance)

        if "wrong dob" in utterance or "unrecognized" in utterance:
            return AgentResult(
                status=AgentStatus.FAILURE,
                output={"text": "Authentication failed", "state": state.to_dict()},
                errors=["Auth failed"],
            )

        # Check more specific conditions first to avoid substring matches
        if "unavailable" in utterance or "11 pm" in utterance or "after hours" in utterance:
            return AgentResult(
                status=AgentStatus.PARTIAL,
                output={"text": "That time is not available. Here are some alternatives.", "state": state.to_dict(), "options": ["slot1", "slot2"]},
                warnings=["Unavailable"],
            )
        elif "show me all" in utterance or "all available times" in utterance:
            text = "Here are multiple available slots."
            options = ["slot1", "slot2", "slot3"]
            return AgentResult(
                status=AgentStatus.SUCCESS,
                output={"text": text, "state": state.to_dict(), "options": options},
                metadata={"intent": "ScheduleAppointment"},
            )
        elif "actually" in utterance and "book" in utterance:
            # Context switch from FAQ to booking
            state.set_intent("ScheduleAppointment")
            text = "Sure, let me help you book an appointment."
            return AgentResult(
                status=AgentStatus.SUCCESS,
                output={"text": text, "state": state.to_dict()},
                metadata={"intent": "ScheduleAppointment"},
            )
        elif "tuesday" in utterance or "2pm" in utterance or "dr. singh" in utterance:
            # Collecting incomplete info across turns
            slots = state.slots or {}
            if "tuesday" in utterance:
                slots["day"] = "Tuesday"
            if "2pm" in utterance or "2 pm" in utterance:
                slots["time"] = "2pm"
            if "dr. singh" in utterance or "singh" in utterance:
                slots["doctor"] = "Dr. Singh"

            state.update_slots(**slots)

            # If all slots filled, book
            if slots.get("day") and slots.get("time") and slots.get("doctor"):
                text = "Great! I've booked your appointment for Tuesday at 2pm with Dr. Singh."
                return AgentResult(
                    status=AgentStatus.SUCCESS,
                    output={"text": text, "state": state.to_dict(), "appointment": {"booked": True}},
                    metadata={"intent": "ScheduleAppointment"},
                )
            else:
                text = "Got it. What else do you need to specify?"
                return AgentResult(
                    status=AgentStatus.PARTIAL,
                    output={"text": text, "state": state.to_dict()},
                    metadata={"intent": "ScheduleAppointment"},
                )
        elif "reschedule" in utterance:
            text = "Appointment rescheduled to new slot."
        elif "cancel" in utterance:
            text = "Appointment canceled and slot freed."
        elif "lab" in utterance and "schedule" not in utterance:
            text = "Here are your lab results. Based on these, I recommend a follow-up."
            state.set_step("awaiting_followup_confirm")
            return AgentResult(
                status=AgentStatus.SUCCESS,
                output={"text": text, "state": state.to_dict(), "follow_up_prompt": "Would you like to schedule a follow-up?"},
                metadata={"intent": "InfoQuery", "follow_up_suggested": True},
            )
        elif state.step == "awaiting_followup_confirm" and ("yes" in utterance or "schedule" in utterance):
            state.set_step(None)
            text = "Great! I've booked your follow-up appointment."
            return AgentResult(
                status=AgentStatus.SUCCESS,
                output={"text": text, "state": state.to_dict(), "appointment": {"booked": True}},
                metadata={"intent": "ScheduleAppointment"},
            )
        elif "hours" in utterance:
            text = "We are open 8 AM to 6 PM."
        elif "follow-up" in utterance:
            text = "Booked your follow-up."
        elif "schedule" in utterance or "appointment" in utterance:
            text = "Booked your appointment."
        elif "need info" in utterance:
            state.set_step("awaiting_details")
            text = "Need more details."
        elif "details" in utterance and state.step == "awaiting_details":
            state.set_step(None)
            text = "Completed after follow-up question."
        else:
            text = "OK."

        if not state.patient_id:
            state.set_patient("P-TEST")

        state.add_turn("assistant", text)
        return AgentResult(
            status=AgentStatus.SUCCESS,
            output={"text": text, "state": state.to_dict()},
            metadata={"intent": "mock"},
        )


def build_scenarios():
    return [
        {
            "name": "New appointment booking",
            "utterances": ["I need to schedule an appointment"],
            "assertion": lambda result, state: "Booked" in result.output["text"] or "booked" in result.output["text"],
        },
        {
            "name": "Reschedule appointment",
            "utterances": ["I need to reschedule my appointment"],
            "assertion": lambda result, state: "rescheduled" in result.output["text"].lower(),
        },
        {
            "name": "Cancel appointment",
            "utterances": ["Please cancel my appointment"],
            "assertion": lambda result, state: "canceled" in result.output["text"].lower(),
        },
        {
            "name": "Lab result plus follow-up",
            "utterances": ["What were my lab results?", "Can I schedule a follow-up?"],
            "assertion": lambda result, state: "booked" in result.output["text"].lower(),
        },
        {
            "name": "Clinic hours FAQ",
            "utterances": ["What are your hours?"],
            "assertion": lambda result, state: "open" in result.output["text"].lower(),
        },
        {
            "name": "Unrecognized patient",
            "utterances": ["wrong dob provided"],
            "assertion": lambda result, state: result.status == AgentStatus.FAILURE,
        },
        {
            "name": "Unavailable time slot",
            "utterances": ["The requested time is unavailable"],
            "assertion": lambda result, state: result.status == AgentStatus.PARTIAL,
        },
        {
            "name": "Multi-turn follow-up",
            "utterances": ["need info", "providing details now"],
            "assertion": lambda result, state: state.step is None and "completed" in result.output["text"].lower(),
        },
        # NEW SCENARIOS (Day 5)
        {
            "name": "Multiple slot selection",
            "utterances": ["Show me all available times for Dr. Singh"],
            "assertion": lambda result, state: "options" in result.output and len(result.output.get("options", [])) >= 2,
        },
        {
            "name": "Context switch FAQ to booking",
            "utterances": ["What are your hours?", "Actually, I want to book an appointment instead"],
            "assertion": lambda result, state: state.current_intent == "ScheduleAppointment",
        },
        {
            "name": "Incomplete booking info",
            "utterances": ["I want Tuesday", "2pm please", "Dr. Singh"],
            "assertion": lambda result, state: "appointment" in result.output or "booked" in result.output.get("text", "").lower(),
        },
        {
            "name": "Invalid time request",
            "utterances": ["I want an appointment at 11 PM"],
            "assertion": lambda result, state: "not available" in result.output.get("text", "").lower() or result.status == AgentStatus.PARTIAL,
        },
        {
            "name": "Lab query with proactive followup",
            "utterances": ["What were my lab results?", "Yes, schedule the follow-up"],
            "assertion": lambda result, state: ("booked" in result.output.get("text", "").lower() or "appointment" in result.output) and state.step != "awaiting_followup_confirm",
        },
    ]


@pytest.mark.asyncio
async def test_eval_runner_covers_scenarios():
    dm = FakeDialogueManager()
    scenarios = build_scenarios()
    results = await run_eval_suite(dm, scenarios)

    assert all(r["passed"] for r in results)
