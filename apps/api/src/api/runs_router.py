"""
Runs API Router
Handles workflow execution runs
"""
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks, Depends
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from db.database import get_db

from models.schemas import (
    RunCreate,
    RunResponse,
    RunExecutionResult,
    RunStatusEnum,
    RunModeEnum,
)
from services.run_service import RunService
from engine.workflow_engine import WorkflowEngine
from core.exceptions import (
    RunNotFoundError,
    WorkflowNotFoundError,
    ValidationError as AppValidationError,
    WorkflowExecutionError,
)

router = APIRouter()


@router.post(
    "",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create run",
    description="Create a new workflow run (queued for execution)"
)
async def create_run(
    run_data: RunCreate,
    session: AsyncSession = Depends(get_db)
):
    """Create new run"""
    service = RunService(session)
    try:
        run = await service.create_run(run_data)
        return run
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/execute",
    response_model=RunExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Create and execute run",
    description="Create and immediately execute a workflow run (synchronous)"
)
async def create_and_execute_run(
    run_data: RunCreate,
    session: AsyncSession = Depends(get_db)
):
    """Create and execute run synchronously"""
    service = RunService(session)
    engine = WorkflowEngine(session)
    
    try:
        # Create run
        run = await service.create_run(run_data)
        
        # Execute workflow
        result = await engine.execute(str(run.id))
        
        # Get updated run
        final_run = await service.get_run(str(run.id))
        
        return RunExecutionResult(
            run=final_run,
            output=result.get("output"),
            metrics=result.get("metrics")
        )
    except RunNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/execute-async",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create and execute run (async)",
    description="Create and execute a workflow run in the background (asynchronous)"
)
async def create_and_execute_run_async(
    run_data: RunCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    """Create and execute run asynchronously"""
    from core import get_logger
    logger = get_logger(__name__)
    logger.info(f"🚀 EXECUTE-ASYNC ENDPOINT HIT! workflow_id={run_data.workflow_id}, mode={run_data.mode}")
    
    service = RunService(session)
    
    try:
        # Create run
        logger.info(f"Creating run for workflow {run_data.workflow_id}...")
        run = await service.create_run(run_data)
        logger.info(f"✓ Run created with ID: {run.id}")
        
        # Execute in background thread
        import threading
        
        def execute_in_thread(run_id: str):
            """Execute workflow in background thread"""
            from db.database import AsyncSessionLocal
            from core import get_logger
            
            logger = get_logger(__name__)
            logger.info(f"🔥 THREAD STARTED for run: {run_id}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def run_workflow():
                    logger.info(f"📦 Creating session for run: {run_id}")
                    async with AsyncSessionLocal() as session:
                        engine = WorkflowEngine(session)
                        logger.info(f"▶️ Starting execution for run: {run_id}")
                        await engine.execute(run_id)
                        logger.info(f"✅ Execution completed for run: {run_id}")
                
                loop.run_until_complete(run_workflow())
            except Exception as e:
                logger.error(f"❌ Thread error for run {run_id}: {str(e)}", exc_info=True)
            finally:
                loop.close()
                logger.info(f"🏁 Thread finished for run: {run_id}")
        
        logger.info(f"⏰ Starting background thread for run: {run.id}")
        thread = threading.Thread(target=execute_in_thread, args=(str(run.id),), daemon=True)
        thread.start()
        logger.info(f"✓ Thread started successfully")
        
        return run
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[RunResponse],
    summary="List runs",
    description="Retrieve all runs with optional filtering"
)
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    workflow_id: Optional[UUID] = None,
    status_filter: Optional[RunStatusEnum] = None,
    run_mode: Optional[RunModeEnum] = None,
    session: AsyncSession = Depends(get_db)
):
    """List runs with filters"""
    service = RunService(session)
    # Get all runs with filters applied by service
    all_runs = await service.list_runs(
        workflow_id=str(workflow_id) if workflow_id else None,
        status=status_filter,
        limit=1000  # Get all, apply pagination here
    )
    # Apply pagination
    return all_runs[skip:skip+limit]


@router.get(
    "/{run_id}",
    response_model=RunResponse,
    summary="Get run by ID",
    description="Retrieve specific run by ID"
)
async def get_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get run by ID"""
    service = RunService(session)
    try:
        run = await service.get_run(str(run_id))
        return run
    except RunNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{run_id}/execute",
    response_model=RunExecutionResult,
    summary="Execute existing run",
    description="Execute an existing queued run"
)
async def execute_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Execute existing run"""
    service = RunService(session)
    engine = WorkflowEngine(session)
    
    try:
        # Check run exists and is in QUEUED status
        run = await service.get_run(str(run_id))
        if run.status != RunStatusEnum.QUEUED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run is not in QUEUED status (current: {run.status})"
            )
        
        # Execute workflow
        result = await engine.execute(str(run_id))
        
        # Get updated run
        final_run = await service.get_run(str(run_id))
        
        return RunExecutionResult(
            run=final_run,
            output=result.get("output"),
            metrics=result.get("metrics")
        )
    except RunNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WorkflowExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete run",
    description="Delete run by ID"
)
async def delete_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Delete run"""
    service = RunService(session)
    try:
        await service.delete_run(str(run_id))
    except RunNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{run_id}/status",
    summary="Get run status",
    description="Get current status of a run"
)
async def get_run_status(
    run_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get run status"""
    service = RunService(session)
    try:
        run = await service.get_run(str(run_id))
        return {
            "run_id": str(run.id),
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "error_message": run.error_message
        }
    except RunNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
