"""
Workflows API Router
Handles workflow CRUD operations
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db

from models.schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    PersonaEnum,
)
from services.workflow_service import WorkflowService
from core.exceptions import (
    WorkflowNotFoundError,
    ValidationError as AppValidationError,
)

router = APIRouter()


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
    description="Create a new workflow definition"
)
async def create_workflow(
    workflow_data: WorkflowCreate,
    session: AsyncSession = Depends(get_db)
):
    """Create new workflow"""
    service = WorkflowService(session)
    try:
        workflow = await service.create_workflow(workflow_data)
        return workflow
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[WorkflowResponse],
    summary="List workflows",
    description="Retrieve all workflows with optional filtering"
)
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = False,
    persona: Optional[PersonaEnum] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """List workflows with filters"""
    service = WorkflowService(session)
    all_workflows = await service.list_workflows(
        persona=persona,
        active_only=active_only,
        tag=search
    )
    # Apply pagination
    return all_workflows[skip:skip+limit]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow by ID",
    description="Retrieve specific workflow by ID"
)
async def get_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get workflow by ID"""
    service = WorkflowService(session)
    try:
        workflow = await service.get_workflow(str(workflow_id))
        return workflow
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update workflow",
    description="Update existing workflow"
)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    session: AsyncSession = Depends(get_db)
):
    """Update workflow"""
    service = WorkflowService(session)
    try:
        workflow = await service.update_workflow(str(workflow_id), workflow_data)
        return workflow
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


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete workflow",
    description="Delete workflow by ID"
)
async def delete_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Delete workflow"""
    service = WorkflowService(session)
    try:
        await service.delete_workflow(str(workflow_id))
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{workflow_id}/activate",
    response_model=WorkflowResponse,
    summary="Activate workflow",
    description="Set workflow as active"
)
async def activate_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Activate workflow"""
    service = WorkflowService(session)
    try:
        update_data = WorkflowUpdate(is_active=True)
        workflow = await service.update_workflow(str(workflow_id), update_data)
        return workflow
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{workflow_id}/deactivate",
    response_model=WorkflowResponse,
    summary="Deactivate workflow",
    description="Set workflow as inactive"
)
async def deactivate_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Deactivate workflow"""
    service = WorkflowService(session)
    try:
        update_data = WorkflowUpdate(is_active=False)
        workflow = await service.update_workflow(str(workflow_id), update_data)
        return workflow
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{workflow_id}/validate",
    summary="Validate workflow schema",
    description="Validate workflow schema without saving"
)
async def validate_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Validate workflow schema"""
    service = WorkflowService(session)
    try:
        workflow = await service.get_workflow(str(workflow_id))
        # Validation happens during get_workflow via schema parsing
        return {
            "valid": True,
            "workflow_id": str(workflow_id),
            "message": "Workflow schema is valid"
        }
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"valid": False, "errors": str(e)}
        )
