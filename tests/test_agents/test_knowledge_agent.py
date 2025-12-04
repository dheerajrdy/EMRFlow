import pytest

from src.agents.knowledge_agent import KnowledgeAgent
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    async def generate(self, *args, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, *args, **kwargs):
        return {"mock": True}


@pytest.fixture
def knowledge_agent():
    return KnowledgeAgent(model_client=MockModelClient())


def test_answer_question_matches_faq(knowledge_agent):
    answer = knowledge_agent.answer_question("clinic hours")
    assert answer is not None
    assert "8:00 AM" in answer["answer"]


@pytest.mark.asyncio
async def test_execute_handles_no_match(knowledge_agent):
    result = await knowledge_agent.execute({"query": "Can you repair my car?"})
    assert result.status.value == "partial"
    assert result.output["answer"] is None
    assert "No FAQ match" in result.output["message"]
