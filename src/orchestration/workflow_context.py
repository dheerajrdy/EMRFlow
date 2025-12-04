"""
Workflow context for sharing state across workflow steps.

Based on CodeFlow pattern - provides clean way to pass data through pipeline.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"


@dataclass
class WorkflowContext:
    """
    Shared context passed through workflow steps.

    Each step reads from and writes to this context.
    Provides centralized state management for the workflow.

    Attributes:
        workflow_id: Unique identifier for this workflow run
        status: Current workflow status
        input_data: Initial input to the workflow
        step_results: Results from each completed step
        metadata: Workflow-level metadata
        errors: List of errors encountered
    """
    workflow_id: str
    input_data: Dict[str, Any]
    status: WorkflowStatus = WorkflowStatus.PENDING
    step_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize timestamps."""
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def update_step_result(self, step_name: str, result: Any) -> None:
        """
        Update results for a specific step.

        Args:
            step_name: Name of the step
            result: Result data from the step
        """
        self.step_results[step_name] = result
        self.updated_at = datetime.utcnow()

    def get_step_result(self, step_name: str) -> Optional[Any]:
        """
        Get results from a specific step.

        Args:
            step_name: Name of the step

        Returns:
            Step result if exists, None otherwise
        """
        return self.step_results.get(step_name)

    def add_error(self, error: str) -> None:
        """
        Add an error to the context.

        Args:
            error: Error message
        """
        self.errors.append(error)
        self.updated_at = datetime.utcnow()

    def set_status(self, status: WorkflowStatus) -> None:
        """
        Update workflow status.

        Args:
            status: New status
        """
        self.status = status
        self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the context.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "input_data": self.input_data,
            "step_results": self.step_results,
            "metadata": self.metadata,
            "errors": self.errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        """
        Create context from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            WorkflowContext instance
        """
        context = cls(
            workflow_id=data["workflow_id"],
            input_data=data["input_data"],
            status=WorkflowStatus(data.get("status", "pending")),
            step_results=data.get("step_results", {}),
            metadata=data.get("metadata", {}),
            errors=data.get("errors", [])
        )

        if data.get("created_at"):
            context.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            context.updated_at = datetime.fromisoformat(data["updated_at"])

        return context

    @property
    def is_complete(self) -> bool:
        """Check if workflow has completed (success or failure)."""
        return self.status in [WorkflowStatus.SUCCESS, WorkflowStatus.FAILURE, WorkflowStatus.ABORTED]

    @property
    def is_success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == WorkflowStatus.SUCCESS

    @property
    def has_errors(self) -> bool:
        """Check if workflow has any errors."""
        return len(self.errors) > 0
