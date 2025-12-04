"""
Basic tests for EMRFlow core components.

Tests the foundational classes to ensure they work correctly.
"""

import pytest
from datetime import datetime
from src.agents.base_agent import BaseAgent, AgentResult, AgentStatus
from src.orchestration.workflow_context import WorkflowContext, WorkflowStatus
from src.models.model_client import ModelClient, ModelResponse


class MockModelClient(ModelClient):
    """Mock model client for testing."""

    async def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None, **kwargs):
        return ModelResponse(
            content="Mock response",
            model="mock-model",
            usage={"input_tokens": 10, "output_tokens": 5}
        )

    async def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        return {"mock": "structured_output"}


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    async def execute(self, input_data):
        self._validate_input(input_data)
        return self._create_success_result(
            output={"message": "Mock agent executed successfully"}
        )


@pytest.mark.asyncio
async def test_agent_result_creation():
    """Test AgentResult creation and properties."""
    result = AgentResult(
        status=AgentStatus.SUCCESS,
        output={"key": "value"}
    )

    assert result.is_success
    assert not result.is_failure
    assert "timestamp" in result.metadata


@pytest.mark.asyncio
async def test_base_agent_execution():
    """Test base agent execution."""
    mock_client = MockModelClient()
    agent = MockAgent(mock_client, name="TestAgent")

    result = await agent.execute({"test": "input"})

    assert result.is_success
    assert result.output["message"] == "Mock agent executed successfully"


@pytest.mark.asyncio
async def test_workflow_context():
    """Test WorkflowContext functionality."""
    context = WorkflowContext(
        workflow_id="test-123",
        input_data={"initial": "data"}
    )

    assert context.status == WorkflowStatus.PENDING
    assert not context.is_complete
    assert not context.has_errors

    # Update step result
    context.update_step_result("step1", {"result": "data"})
    assert context.get_step_result("step1") == {"result": "data"}

    # Add error
    context.add_error("Test error")
    assert context.has_errors
    assert len(context.errors) == 1

    # Change status
    context.set_status(WorkflowStatus.SUCCESS)
    assert context.is_complete
    assert context.is_success


def test_workflow_context_serialization():
    """Test WorkflowContext to/from dict conversion."""
    original = WorkflowContext(
        workflow_id="test-456",
        input_data={"key": "value"}
    )
    original.update_step_result("step1", {"result": "test"})
    original.add_error("test error")

    # Convert to dict and back
    data = original.to_dict()
    restored = WorkflowContext.from_dict(data)

    assert restored.workflow_id == original.workflow_id
    assert restored.input_data == original.input_data
    assert restored.step_results == original.step_results
    assert restored.errors == original.errors


@pytest.mark.asyncio
async def test_mock_model_client():
    """Test mock model client."""
    client = MockModelClient()

    # Test generate
    response = await client.generate("Test prompt")
    assert response.content == "Mock response"
    assert response.model == "mock-model"

    # Test generate_structured
    structured = await client.generate_structured("Test prompt", schema={})
    assert structured["mock"] == "structured_output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
