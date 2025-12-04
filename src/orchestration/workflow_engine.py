"""
Workflow engine for orchestrating multi-agent workflows.

Based on CodeFlow learnings - explicit sequential orchestration with retry logic.
"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import asyncio
import logging
from datetime import datetime

from src.orchestration.workflow_context import WorkflowContext, WorkflowStatus


logger = logging.getLogger(__name__)


class WorkflowStep(ABC):
    """
    Abstract base class for workflow steps.

    Each step is responsible for:
    1. Reading from WorkflowContext
    2. Performing its specific operation
    3. Updating context with results
    4. Handling errors gracefully
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize workflow step.

        Args:
            name: Step name
            config: Step-specific configuration
        """
        self.name = name
        self.config = config or {}
        self.max_retries = self.config.get("max_retries", 2)

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        Execute the workflow step.

        Args:
            context: Current workflow context

        Returns:
            Updated workflow context
        """
        pass

    async def run(self, context: WorkflowContext) -> WorkflowContext:
        """
        Run the step with retry logic.

        Args:
            context: Current workflow context

        Returns:
            Updated workflow context
        """
        logger.info(f"Starting step: {self.name}")

        for attempt in range(self.max_retries + 1):
            try:
                context = await self.execute(context)
                logger.info(f"Step {self.name} completed successfully")
                return context

            except Exception as e:
                error_msg = f"Step {self.name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}"
                logger.error(error_msg)

                if attempt == self.max_retries:
                    context.add_error(error_msg)
                    context.set_status(WorkflowStatus.FAILURE)
                    return context
                else:
                    logger.info(f"Retrying step {self.name}...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return context

    def should_execute(self, context: WorkflowContext) -> bool:
        """
        Determine if this step should execute based on context.

        Override in subclasses for conditional execution.

        Args:
            context: Current workflow context

        Returns:
            True if step should execute, False to skip
        """
        return True


class WorkflowEngine:
    """
    Orchestrates execution of workflow steps.

    Features:
    - Sequential step execution
    - Conditional branching
    - Retry logic per step
    - Error handling and recovery
    - Progress tracking
    """

    def __init__(
        self,
        steps: List[WorkflowStep],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize workflow engine.

        Args:
            steps: List of workflow steps to execute
            config: Engine configuration
        """
        self.steps = steps
        self.config = config or {}
        self.timeout_seconds = self.config.get("timeout_seconds", 300)

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        Execute the complete workflow.

        Args:
            context: Initial workflow context

        Returns:
            Final workflow context with results
        """
        logger.info(f"Starting workflow: {context.workflow_id}")
        context.set_status(WorkflowStatus.RUNNING)
        context.add_metadata("started_at", datetime.utcnow().isoformat())

        try:
            # Execute steps sequentially
            for step in self.steps:
                # Check if workflow should continue
                if context.is_complete:
                    logger.info(f"Workflow {context.workflow_id} completed early at step {step.name}")
                    break

                # Check if step should execute
                if not step.should_execute(context):
                    logger.info(f"Skipping step: {step.name}")
                    continue

                # Execute step with timeout
                try:
                    context = await asyncio.wait_for(
                        step.run(context),
                        timeout=self.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    error_msg = f"Step {step.name} timed out after {self.timeout_seconds}s"
                    logger.error(error_msg)
                    context.add_error(error_msg)
                    context.set_status(WorkflowStatus.FAILURE)
                    break

                # Check for errors after step execution
                if context.has_errors and not context.is_complete:
                    logger.warning(f"Errors detected after step {step.name}, continuing...")

            # Set final status if not already set
            if not context.is_complete:
                context.set_status(WorkflowStatus.SUCCESS)

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg)
            context.add_error(error_msg)
            context.set_status(WorkflowStatus.FAILURE)

        finally:
            context.add_metadata("completed_at", datetime.utcnow().isoformat())
            logger.info(f"Workflow {context.workflow_id} finished with status: {context.status.value}")

        return context

    async def execute_with_timeout(
        self,
        context: WorkflowContext,
        timeout: Optional[int] = None
    ) -> WorkflowContext:
        """
        Execute workflow with overall timeout.

        Args:
            context: Initial workflow context
            timeout: Timeout in seconds (uses config default if not provided)

        Returns:
            Final workflow context
        """
        timeout = timeout or self.timeout_seconds

        try:
            return await asyncio.wait_for(
                self.execute(context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            error_msg = f"Workflow timed out after {timeout}s"
            logger.error(error_msg)
            context.add_error(error_msg)
            context.set_status(WorkflowStatus.ABORTED)
            return context


class ConditionalStep(WorkflowStep):
    """
    Workflow step that only executes if condition is met.

    Example:
        ```python
        def should_run(ctx):
            return ctx.get_step_result("previous_step")["status"] == "success"

        step = ConditionalStep(
            name="conditional",
            condition=should_run,
            base_step=actual_step
        )
        ```
    """

    def __init__(
        self,
        name: str,
        condition: callable,
        base_step: WorkflowStep,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize conditional step.

        Args:
            name: Step name
            condition: Function that takes context and returns bool
            base_step: The actual step to execute if condition is true
            config: Step configuration
        """
        super().__init__(name, config)
        self.condition = condition
        self.base_step = base_step

    def should_execute(self, context: WorkflowContext) -> bool:
        """Check if condition is met."""
        return self.condition(context)

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Execute the base step."""
        return await self.base_step.execute(context)
