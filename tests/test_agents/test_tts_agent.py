import pytest

from src.agents.tts_agent import TTSAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


class FakeTTSClient:
    def synthesize_to_file(self, text, output_path):
        path = output_path
        with open(path, "wb") as f:
            f.write(text.encode("utf-8"))
        return path


@pytest.mark.asyncio
async def test_tts_agent_writes_file(tmp_path):
    output_path = tmp_path / "out.mp3"
    agent = TTSAgent(model_client=MockModelClient(), tts_client=FakeTTSClient())
    result = await agent.execute({"text": "Hello", "output_path": str(output_path)})

    assert result.is_success
    assert output_path.exists()
    assert output_path.read_bytes() == b"Hello"


@pytest.mark.asyncio
async def test_tts_agent_requires_text(tmp_path):
    agent = TTSAgent(model_client=MockModelClient(), tts_client=FakeTTSClient())
    result = await agent.execute({"output_path": str(tmp_path / "out.mp3")})
    assert result.is_failure
