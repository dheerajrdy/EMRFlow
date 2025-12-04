"""
Base agent abstraction for EMRFlow.

Based on CodeFlow learnings - provides consistent interface for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.models.model_client import ModelClient


class AgentStatus(Enum):
    """Status of agent execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # Completed but with warnings
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """
    Standardized result from any agent execution.

    Attributes:
        status: Execution status
        output: Main output data from the agent
        metadata: Additional metadata (timing, model used, etc.)
        errors: List of errors if any occurred
        warnings: List of warnings
    """
    status: AgentStatus
    output: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def __post_init__(self):
        """Ensure metadata has timestamp."""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.utcnow().isoformat()

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == AgentStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if execution failed."""
        return self.status == AgentStatus.FAILURE


class BaseAgent(ABC):
    """
    Abstract base class for all agents in EMRFlow.

    All agents should:
    1. Have a clear, single responsibility
    2. Take typed inputs and return AgentResult
    3. Be model-agnostic (use ModelClient)
    4. Handle errors gracefully
    5. Protect PHI in logs and outputs
    """

    def __init__(
        self,
        model_client: ModelClient,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent.

        Args:
            model_client: Model client for LLM interactions
            name: Agent name (defaults to class name)
            config: Agent-specific configuration
        """
        self.model = model_client
        self.name = name or self.__class__.__name__
        self.config = config or {}

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main task.

        Args:
            input_data: Input data dictionary (schema defined by subclass)

        Returns:
            AgentResult with execution status and outputs
        """
        pass

    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data structure.

        Override in subclasses to add specific validation.

        Args:
            input_data: Input data to validate

        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(input_data, dict):
            raise ValueError(f"{self.name}: input_data must be a dictionary")

    def _protect_phi(self, data: str) -> str:
        """
        Sanitize data to remove/mask PHI for logging.

        Override in subclasses for domain-specific PHI protection.

        Args:
            data: String that may contain PHI

        Returns:
            Sanitized string safe for logging
        """
        # Placeholder - implement actual PHI detection/masking
        # Could use regex for common patterns, or ML-based detection
        return "[PHI PROTECTED]" if data else data

    async def _retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """
        Retry a function with exponential backoff.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        import asyncio

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

    def _create_success_result(
        self,
        output: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Helper to create success result.

        Args:
            output: Agent output data
            metadata: Additional metadata

        Returns:
            AgentResult with SUCCESS status
        """
        return AgentResult(
            status=AgentStatus.SUCCESS,
            output=output,
            metadata=metadata or {}
        )

    def _create_failure_result(
        self,
        error: str,
        output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Helper to create failure result.

        Args:
            error: Error message
            output: Partial output if any
            metadata: Additional metadata

        Returns:
            AgentResult with FAILURE status
        """
        return AgentResult(
            status=AgentStatus.FAILURE,
            output=output or {},
            metadata=metadata or {},
            errors=[error]
        )
