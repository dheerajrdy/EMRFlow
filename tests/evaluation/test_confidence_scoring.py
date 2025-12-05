import pytest

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.agents.dialogue_manager import DialogueManager
from src.models.model_client import ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState


class StubModelClient(ModelClient):
    """Model client that returns a predetermined confidence score."""

    def __init__(self, score: float):
        self.score = score

    async def generate(self, *args, **kwargs):
        return ModelResponse(content=str(self.score), model="stub")

    async def generate_structured(self, *args, **kwargs):
        return {"intent": "Other", "entities": {}}


class StubNLUAgent(BaseAgent):
    def __init__(self, intent: str, confidence: float, model_client):
        super().__init__(model_client)
        self.intent = intent
        self.confidence = confidence

    async def execute(self, input_data):
        return self._create_success_result(
            {"intent": self.intent, "entities": {}, "confidence": self.confidence}
        )


class DummyAgent(BaseAgent):
    async def execute(self, input_data):
        return AgentResult(
            status=AgentStatus.SUCCESS,
            output={"text": "Acknowledged."},
        )


class SimpleDialogueManager(DialogueManager):
    """DialogueManager subclass with deterministic routing for tests."""

    async def _route_intent(self, intent, utterance, state, input_data) -> AgentResult:  # type: ignore[override]
        return self._create_success_result({"text": "Acknowledged."})


@pytest.fixture
def flagged_log_tmp(tmp_path, monkeypatch):
    log_file = tmp_path / "flagged.jsonl"
    monkeypatch.setenv("FLAGGED_RESPONSES_LOG", str(log_file))
    return log_file


def _build_dm(model_client: ModelClient, intent: str = "FAQ", confidence: float = 1.0) -> DialogueManager:
    nlu = StubNLUAgent(intent=intent, confidence=confidence, model_client=model_client)
    dummy = DummyAgent(model_client=model_client)
    return SimpleDialogueManager(
        model_client=model_client,
        nlu_agent=nlu,
        scheduling_agent=dummy,
        records_agent=dummy,
        knowledge_agent=dummy,
    )


@pytest.mark.asyncio
async def test_confidence_scoring_not_flagged(flagged_log_tmp):
    dm = _build_dm(StubModelClient(0.92))
    result = await dm.execute({"utterance": "Help me schedule", "state": ConversationState(), "session_id": "sess-1"})

    assert result.metadata.get("confidence_score", 0) > 0.9
    assert dm.flagged_responses == []
    assert "Note: This response will be reviewed" not in result.output["text"]


@pytest.mark.asyncio
async def test_confidence_scoring_flags_low_score(flagged_log_tmp):
    dm = _build_dm(StubModelClient(0.35))
    result = await dm.execute({"utterance": "unclear request", "state": ConversationState(), "session_id": "sess-2"})

    assert result.metadata.get("flagged_for_review") is True
    assert dm.flagged_responses, "Low confidence response should be tracked"
    assert dm.flagged_responses[0]["session_id"] == "sess-2"
    assert "review" in result.output["text"].lower()


@pytest.mark.asyncio
async def test_confidence_scoring_can_be_disabled(flagged_log_tmp):
    dm = _build_dm(StubModelClient(0.2))
    dm.enable_confidence_scoring = False
    dm.confidence_scorer = None

    result = await dm.execute({"utterance": "unclear query", "state": ConversationState()})

    assert "confidence_score" not in result.metadata
    assert dm.flagged_responses == []

