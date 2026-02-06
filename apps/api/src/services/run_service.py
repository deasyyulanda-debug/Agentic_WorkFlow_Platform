"""
Run Service - Workflow Execution Management
Handles run lifecycle and state transitions
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Run as RunModel, RunStatus, RunMode, Provider
from db.repositories import RunRepository, WorkflowRepository
from models.schemas import (
    RunCreate,
    RunResponse,
    ValidationResult
)
from core import (
    RunNotFoundError,
    WorkflowNotFoundError,
    InvalidStateTransitionError,
    get_logger
)


class RunService:
    """
    Service for managing workflow runs.
    
    Responsibilities:
    - Run lifecycle management
    - State machine enforcement
    - Metrics tracking
    - Validation result storage
    """
    
    # Valid state transitions (from -> to)
    VALID_TRANSITIONS = {
        RunStatus.QUEUED: [RunStatus.VALIDATING, RunStatus.RUNNING, RunStatus.CANCELLED, RunStatus.FAILED],
        RunStatus.VALIDATING: [RunStatus.RUNNING, RunStatus.FAILED, RunStatus.CANCELLED],
        RunStatus.RUNNING: [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED],
        RunStatus.COMPLETED: [],  # Terminal state
        RunStatus.FAILED: [],     # Terminal state
        RunStatus.CANCELLED: []   # Terminal state
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = RunRepository(session)
        self.workflow_repository = WorkflowRepository(session)
        self.logger = get_logger(__name__)
    
    async def create_run(self, data: RunCreate) -> RunResponse:
        """
        Create a new workflow run.
        
        Args:
            data: Run creation data
            
        Returns:
            Created run
            
        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
        """
        # Verify workflow exists
        workflow = await self.workflow_repository.get(data.workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(data.workflow_id)
        
        self.logger.info(
            f"Creating run for workflow {data.workflow_id} in {data.mode.value} mode with provider {data.provider.value}",
            workflow_id=data.workflow_id,
            mode=data.mode.value,
            provider=data.provider.value
        )
        
        # Convert ProviderEnum to Provider (schema enum to DB enum)
        provider_map = {
            "openai": Provider.OPENAI,
            "anthropic": Provider.ANTHROPIC,
            "gemini": Provider.GEMINI,
            "deepseek": Provider.DEEPSEEK,
            "openrouter": Provider.OPENROUTER,
            "groq": Provider.GROQ
        }
        db_provider = provider_map.get(data.provider.value, Provider.GEMINI)
        
        # Create run
        run = await self.repository.create(
            workflow_id=data.workflow_id,
            run_mode=data.mode,  # DB model uses 'run_mode'
            inputs=data.input_data,  # DB model uses 'inputs'
            provider=db_provider,  # Use provider from request
            status=RunStatus.QUEUED  # Initial state
        )
        
        self.logger.info(f"Run created: {run.id} with provider {db_provider.value}", run_id=run.id)
        
        return RunResponse.model_validate(run)
    
    async def get_run(self, run_id: str) -> RunResponse:
        """Get run by ID"""
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        return RunResponse.model_validate(run)
    
    async def delete_run(self, run_id: str) -> bool:
        """Delete run by ID"""
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        deleted = await self.repository.delete(run_id)
        if deleted:
            self.logger.info(f"Run deleted: {run_id}", run_id=run_id)
        return deleted
    
    async def list_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[RunStatus] = None,
        limit: int = 100
    ) -> list[RunResponse]:
        """
        List runs with optional filters.
        
        Args:
            workflow_id: Filter by workflow
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of runs
        """
        if workflow_id and status:
            runs = await self.repository.get_by_workflow_and_status(workflow_id, status)
        elif workflow_id:
            runs = await self.repository.get_by_workflow(workflow_id)
        elif status:
            # Get all runs and filter by status
            all_runs = await self.repository.get_all(limit=1000)
            runs = [r for r in all_runs if r.status == status]
        else:
            runs = await self.repository.get_all(limit=1000)
        
        # Apply limit
        runs = runs[:limit]
        
        return [RunResponse.model_validate(r) for r in runs]
    
    async def start_run(self, run_id: str) -> RunResponse:
        """
        Start a pending run.
        
        Args:
            run_id: Run ID
            
        Returns:
            Updated run
            
        Raises:
            InvalidStateTransitionError: If run is not in PENDING state
        """
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        # Validate state transition
        self._validate_transition(run.status, RunStatus.RUNNING)
        
        # Update to RUNNING (timestamps handled by repository)
        updated = await self.repository.update_status(
            run_id,
            RunStatus.RUNNING
        )
        
        self.logger.info(f"Run started: {run_id}", run_id=run_id)
        
        return RunResponse.model_validate(updated)
    
    async def complete_run(
        self,
        run_id: str,
        output_data: Optional[dict] = None,
        metrics: Optional[dict] = None
    ) -> RunResponse:
        """
        Complete a running run.
        
        Args:
            run_id: Run ID
            output_data: Final output data (will be stored in validation_result field)
            metrics: Execution metrics
            
        Returns:
            Updated run
        """
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        self._validate_transition(run.status, RunStatus.COMPLETED)
        
        # Update to COMPLETED (timestamps handled by repository)
        updated = await self.repository.update_status(
            run_id,
            RunStatus.COMPLETED
        )
        
        # Store output_data in validation_result field (DB doesn't have separate output_data or metrics columns)
        if output_data:
            # Merge metrics into output_data if provided
            if metrics:
                output_data['_metrics'] = metrics
            # Store in validation_result field
            updated = await self.repository.update(run_id, validation_result=output_data)
        
        self.logger.info(
            f"Run completed: {run_id}",
            run_id=run_id,
            metrics=metrics
        )
        
        return RunResponse.model_validate(updated)
    
    async def fail_run(
        self,
        run_id: str,
        error_message: str,
        error_details: Optional[dict] = None
    ) -> RunResponse:
        """
        Fail a running run.
        
        Args:
            run_id: Run ID
            error_message: Error message
            error_details: Additional error context
            
        Returns:
            Updated run
        """
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        self._validate_transition(run.status, RunStatus.FAILED)
        
        # Build error data
        error_data = {
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if error_details:
            error_data["details"] = error_details
        
        # Update to FAILED (timestamps handled by repository)
        updated = await self.repository.update_status(
            run_id,
            RunStatus.FAILED,
            error_message=error_message
        )
        
        # Store error details in output_data
        updated = await self.repository.update(
            run_id,
            output_data={"error": error_data}
        )
        
        self.logger.error(
            f"Run failed: {run_id} - {error_message}",
            run_id=run_id,
            error=error_message
        )
        
        return RunResponse.model_validate(updated)
    
    async def cancel_run(self, run_id: str) -> RunResponse:
        """
        Cancel a pending or running run.
        
        Args:
            run_id: Run ID
            
        Returns:
            Updated run
        """
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        self._validate_transition(run.status, RunStatus.CANCELLED)
        
        # Update to CANCELLED (timestamps handled by repository)
        updated = await self.repository.update_status(
            run_id,
            RunStatus.CANCELLED
        )
        
        self.logger.info(f"Run cancelled: {run_id}", run_id=run_id)
        
        return RunResponse.model_validate(updated)
    
    async def update_validation_result(
        self,
        run_id: str,
        result: ValidationResult
    ) -> RunResponse:
        """
        Update validation result for a validate-only run.
        
        Args:
            run_id: Run ID
            result: Validation result
            
        Returns:
            Updated run
        """
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        if run.mode != RunMode.VALIDATE_ONLY:
            raise InvalidStateTransitionError(
                run.mode.value,
                "Validation results only applicable to VALIDATE_ONLY mode"
            )
        
        # Store validation result
        validation_data = result.model_dump()
        updated = await self.repository.update_validation_result(run_id, validation_data)
        
        self.logger.info(
            f"Validation result updated for run {run_id}",
            run_id=run_id,
            is_valid=result.is_valid
        )
        
        return RunResponse.model_validate(updated)
    
    async def get_active_runs(self) -> list[RunResponse]:
        """Get all active (PENDING or RUNNING) runs"""
        runs = await self.repository.get_active_runs()
        return [RunResponse.model_validate(r) for r in runs]
    
    async def get_run_metrics(self, run_id: str) -> Optional[dict]:
        """Get execution metrics for a run"""
        run = await self.repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        return run.metrics
    
    def _validate_transition(self, current: RunStatus, target: RunStatus) -> None:
        """
        Validate state transition.
        
        Args:
            current: Current status
            target: Target status
            
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        valid_targets = self.VALID_TRANSITIONS.get(current, [])
        if target not in valid_targets:
            raise InvalidStateTransitionError(
                current.value,
                target.value
            )
