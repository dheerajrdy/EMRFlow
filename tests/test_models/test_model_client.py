from types import SimpleNamespace

import pytest

from src.models.model_client import GoogleModelClient, ModelResponse


class DummyResponse:
    def __init__(self, text: str):
        self.text = text
        self.finish_reason = "stop"
        self.usage_metadata = SimpleNamespace(prompt_token_count=5, candidates_token_count=3)


class StubGenAI:
    """Minimal stub for google.generativeai."""

    def __init__(self, text: str):
        self.text = text
        self.configure_called = False

    def configure(self, api_key: str):
        self.configure_called = True

    def GenerativeModel(self, model_name: str):
        return StubModel(self.text)


class StubModel:
    def __init__(self, text: str):
        self.text = text

    def generate_content(self, *args, **kwargs):
        return DummyResponse(self.text)


@pytest.fixture
def stub_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_generate_uses_stub(monkeypatch, stub_env):
    from src.models import model_client as mc

    stub = StubGenAI("hello world")
    monkeypatch.setattr(mc, "genai", stub)

    client = GoogleModelClient()
    response = await client.generate("hi")

    assert isinstance(response, ModelResponse)
    assert response.content == "hello world"
    assert stub.configure_called


@pytest.mark.asyncio
async def test_generate_structured_parses_json(monkeypatch, stub_env):
    from src.models import model_client as mc

    stub = StubGenAI('{"intent": "FAQ", "entities": {"doctor": "Singh"}}')
    monkeypatch.setattr(mc, "genai", stub)

    client = GoogleModelClient()
    structured = await client.generate_structured("hi", schema={"type": "object"})

    assert structured["intent"] == "FAQ"
    assert structured["entities"]["doctor"] == "Singh"
