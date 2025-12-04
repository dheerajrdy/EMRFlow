import pytest

from src.agents.base_agent import AgentResult, BaseAgent
from src.models.model_client import ModelClient, ModelResponse
from src.orchestration.voice_workflow import VoiceWorkflow
from src.utils.conversation_state import ConversationState


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


class FakeASRAgent(BaseAgent):
    def __init__(self, transcript: str):
        super().__init__(MockModelClient())
        self.transcript = transcript

    async def execute(self, input_data):
        return self._create_success_result({"transcript": self.transcript})


class FakeDialogueManager(BaseAgent):
    def __init__(self, response_text: str):
        super().__init__(MockModelClient())
        self.response_text = response_text

    async def execute(self, input_data):
        state = input_data.get("state") or ConversationState()
        return self._create_success_result({"text": self.response_text, "state": state.to_dict()})


class FakeTTSAgent(BaseAgent):
    def __init__(self):
        super().__init__(MockModelClient())

    async def execute(self, input_data):
        return self._create_success_result({"path": input_data.get("output_path")})


@pytest.mark.asyncio
async def test_voice_workflow_runs_turn(tmp_path):
    workflow = VoiceWorkflow(
        asr_agent=FakeASRAgent("hello"),
        dialogue_manager=FakeDialogueManager("hi there"),
        tts_agent=FakeTTSAgent(),
    )

    result = await workflow.run_turn(audio_path=str(tmp_path / "audio.wav"), state=ConversationState())

    assert result["transcript"] == "hello"
    assert result["response"] == "hi there"
    assert result["audio_path"].endswith("turn.mp3")
