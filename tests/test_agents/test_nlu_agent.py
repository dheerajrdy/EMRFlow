import pytest

from src.agents.nlu_agent import NLUAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    def __init__(self, structured=None, fail=False):
        self.structured = structured or {"intent": "FAQ", "entities": {"doctor": "Singh"}}
        self.fail = fail

    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        if self.fail:
            raise RuntimeError("fail")
        return self.structured


@pytest.mark.asyncio
async def test_nlu_agent_returns_structured_result():
    agent = NLUAgent(model_client=MockModelClient())
    result = await agent.execute({"utterance": "What are your hours?"})
    assert result.output["intent"] == "FAQ"
    assert result.output["entities"]["doctor"] == "Singh"


@pytest.mark.asyncio
async def test_nlu_agent_fallback():
    agent = NLUAgent(model_client=MockModelClient(fail=True))
    result = await agent.execute({"utterance": "cancel my appointment"})
    assert result.output["intent"] == "CancelAppointment"
