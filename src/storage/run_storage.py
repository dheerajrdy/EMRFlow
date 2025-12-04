"""
Storage for workflow run metadata and results.

Based on CodeFlow learning pattern - track all runs for improvement.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json
from pathlib import Path
from datetime import datetime
import logging

from src.orchestration.workflow_context import WorkflowContext


logger = logging.getLogger(__name__)


class RunStorage(ABC):
    """Abstract base class for run storage."""

    @abstractmethod
    async def save_run(self, context: WorkflowContext) -> None:
        """Save a workflow run."""
        pass

    @abstractmethod
    async def get_run(self, workflow_id: str) -> Optional[WorkflowContext]:
        """Retrieve a workflow run by ID."""
        pass

    @abstractmethod
    async def list_runs(
        self,
        limit: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List workflow runs with optional filtering."""
        pass


class JSONLRunStorage(RunStorage):
    """
    JSONL-based storage for workflow runs.

    Simple file-based storage where each run is a JSON line.
    Good for development and small-scale usage.
    """

    def __init__(self, storage_path: str = "runs"):
        """
        Initialize JSONL storage.

        Args:
            storage_path: Directory path for storing run files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.runs_file = self.storage_path / "runs.jsonl"

    async def save_run(self, context: WorkflowContext) -> None:
        """
        Save workflow run to JSONL file.

        Args:
            context: Workflow context to save
        """
        try:
            run_data = context.to_dict()
            run_data["saved_at"] = datetime.utcnow().isoformat()

            # Append to JSONL file
            with open(self.runs_file, "a") as f:
                f.write(json.dumps(run_data) + "\n")

            logger.info(f"Saved run {context.workflow_id} to {self.runs_file}")

        except Exception as e:
            logger.error(f"Failed to save run {context.workflow_id}: {str(e)}")
            raise

    async def get_run(self, workflow_id: str) -> Optional[WorkflowContext]:
        """
        Retrieve workflow run by ID.

        Args:
            workflow_id: ID of the workflow to retrieve

        Returns:
            WorkflowContext if found, None otherwise
        """
        if not self.runs_file.exists():
            return None

        try:
            with open(self.runs_file, "r") as f:
                for line in f:
                    run_data = json.loads(line)
                    if run_data.get("workflow_id") == workflow_id:
                        return WorkflowContext.from_dict(run_data)

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve run {workflow_id}: {str(e)}")
            return None

    async def list_runs(
        self,
        limit: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflow runs.

        Args:
            limit: Maximum number of runs to return
            status: Filter by status (optional)

        Returns:
            List of run data dictionaries
        """
        if not self.runs_file.exists():
            return []

        try:
            runs = []
            with open(self.runs_file, "r") as f:
                for line in f:
                    run_data = json.loads(line)

                    # Apply status filter if provided
                    if status and run_data.get("status") != status:
                        continue

                    runs.append(run_data)

            # Sort by created_at descending (most recent first)
            runs.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )

            # Apply limit if provided
            if limit:
                runs = runs[:limit]

            return runs

        except Exception as e:
            logger.error(f"Failed to list runs: {str(e)}")
            return []

    async def get_run_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics about runs.

        Returns:
            Dictionary with run statistics
        """
        runs = await self.list_runs()

        if not runs:
            return {
                "total_runs": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0
            }

        total = len(runs)
        success = sum(1 for r in runs if r.get("status") == "success")
        failure = sum(1 for r in runs if r.get("status") == "failure")

        return {
            "total_runs": total,
            "success_count": success,
            "failure_count": failure,
            "success_rate": success / total if total > 0 else 0.0,
            "most_recent": runs[0].get("created_at") if runs else None
        }


def create_storage(config: Dict[str, Any]) -> RunStorage:
    """
    Factory function to create appropriate storage from config.

    Args:
        config: Storage configuration

    Returns:
        RunStorage instance

    Example config:
        {
            "type": "jsonl",
            "path": "runs"
        }
    """
    storage_type = config.get("type", "jsonl").lower()

    if storage_type == "jsonl":
        return JSONLRunStorage(
            storage_path=config.get("path", "runs")
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
