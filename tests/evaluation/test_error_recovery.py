import pytest

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.agents.dialogue_manager import DialogueManager
from src.models.model_client import ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState


class StubModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="stub")

    async def generate_structured(self, *args, **kwargs):
        return {"intent": "Other", "entities": {}}


class SequenceNLUAgent(BaseAgent):
    """Returns a sequence of confidences to drive retry logic."""

    def __init__(self, intents, confidences, model_client):
        super().__init__(model_client)
        self.intents = intents
        self.confidences = confidences

    async def execute(self, input_data):
        intent = self.intents.pop(0) if self.intents else "Other"
        confidence = self.confidences.pop(0) if self.confidences else 1.0
        return self._create_success_result(
            {"intent": intent, "entities": {}, "confidence": confidence}
        )


class DummyAgent(BaseAgent):
    async def execute(self, input_data):
        return AgentResult(status=AgentStatus.SUCCESS, output={"text": "Handled."})


class FixedDialogueManager(DialogueManager):
    """DialogueManager with deterministic routing."""

    async def _route_intent(self, intent, utterance, state, input_data) -> AgentResult:  # type: ignore[override]
        return self._create_success_result({"text": f"Intent {intent} handled."})


def build_dm(intents, confidences) -> DialogueManager:
    model = StubModelClient()
    nlu = SequenceNLUAgent(intents=intents, confidences=confidences, model_client=model)
    dummy = DummyAgent(model_client=model)
    return FixedDialogueManager(
        model_client=model,
        nlu_agent=nlu,
        scheduling_agent=dummy,
        records_agent=dummy,
        knowledge_agent=dummy,
        enable_confidence_scoring=False,
    )


@pytest.mark.asyncio
async def test_graduated_fallback_full_sequence():
    dm = build_dm(
        intents=["Other", "Other", "Other"],
        confidences=[0.3, 0.3, 0.3],
    )
    state = ConversationState()

    response1 = await dm.execute({"utterance": "I need that thing", "state": state})
    assert response1.status == AgentStatus.PARTIAL
    state = ConversationState.from_dict(response1.output["state"])
    assert state.retry_count == 1
    assert "help" in response1.output["text"].lower()

    response2 = await dm.execute({"utterance": "yeah that", "state": state})
    assert response2.status == AgentStatus.PARTIAL
    state = ConversationState.from_dict(response2.output["state"])
    assert state.retry_count == 2
    assert "1." in response2.output["text"] or "menu" in response2.output["text"].lower()

    response3 = await dm.execute({"utterance": "just do it", "state": state})
    assert response3.status == AgentStatus.PARTIAL
    state = ConversationState.from_dict(response3.output["state"])
    assert state.retry_count == 0  # Reset after escalation
    assert "team member" in response3.output["text"].lower() or "call" in response3.output["text"].lower()


@pytest.mark.asyncio
async def test_clarification_resolves_on_retry():
    dm = build_dm(
        intents=["Other", "ScheduleAppointment"],
        confidences=[0.4, 0.9],
    )
    state = ConversationState()

    response1 = await dm.execute({"utterance": "I need an appointment", "state": state})
    assert state.retry_count == 1
    state = ConversationState.from_dict(response1.output["state"])

    response2 = await dm.execute(
        {"utterance": "Schedule with Dr. Singh next Tuesday 2pm", "state": state}
    )
    assert response2.status == AgentStatus.SUCCESS
    assert ConversationState.from_dict(response2.output["state"]).retry_count == 0


@pytest.mark.asyncio
async def test_menu_selection_resets_retry():
    dm = build_dm(
        intents=["Other", "ScheduleAppointment"],
        confidences=[0.4, 0.95],
    )
    state = ConversationState()

    response1 = await dm.execute({"utterance": "help me", "state": state})
    state = ConversationState.from_dict(response1.output["state"])
    assert state.retry_count == 1

    response2 = await dm.execute({"utterance": "option 1", "state": state})
    assert response2.status == AgentStatus.SUCCESS
    assert ConversationState.from_dict(response2.output["state"]).retry_count == 0


def test_retry_counter_resets_on_high_confidence():
    dm = build_dm(intents=["FAQ"], confidences=[1.0])
    state = ConversationState(retry_count=1, max_retries=2)

    dm.check_and_reset_retry_on_success(confidence=0.9, state=state)
    assert state.retry_count == 0
