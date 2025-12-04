import pytest

from src.agents.asr_agent import ASRAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


class FakeSpeechClient:
    def __init__(self, transcript="hello world", confidence=0.9):
        self.transcript = transcript
        self.confidence = confidence
        self.last_path = None

    def transcribe_file(self, path):
        self.last_path = path
        return self.transcript, self.confidence

    def transcribe_content(self, content):
        return self.transcript, self.confidence


@pytest.mark.asyncio
async def test_asr_agent_from_path(tmp_path):
    fake_audio = tmp_path / "audio.wav"
    fake_audio.write_bytes(b"audio")

    agent = ASRAgent(model_client=MockModelClient(), speech_client=FakeSpeechClient())
    result = await agent.execute({"audio_path": str(fake_audio)})

    assert result.is_success
    assert result.output["transcript"] == "hello world"


@pytest.mark.asyncio
async def test_asr_agent_missing_audio():
    agent = ASRAgent(model_client=MockModelClient(), speech_client=FakeSpeechClient())
    result = await agent.execute({})
    assert result.is_failure
