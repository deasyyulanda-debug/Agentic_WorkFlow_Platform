"""
Artifacts API Router
Handles workflow execution artifacts
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import FileResponse
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import os

from db.database import get_db

from models.schemas import ArtifactResponse
from services.artifact_service import ArtifactService
from core.exceptions import NotFoundError

router = APIRouter()


@router.get(
    "",
    response_model=List[ArtifactResponse],
    summary="List artifacts",
    description="Retrieve all artifacts with optional filtering by run"
)
async def list_artifacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    run_id: Optional[UUID] = None,
    artifact_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """List artifacts with filters"""
    service = ArtifactService(session)
    artifacts = await service.list_artifacts(
        skip=skip,
        limit=limit,
        run_id=run_id,
        artifact_type=artifact_type
    )
    return artifacts


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Get artifact by ID",
    description="Retrieve specific artifact metadata by ID"
)
async def get_artifact(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get artifact by ID"""
    service = ArtifactService(session)
    try:
        artifact = await service.get_artifact(artifact_id)
        return artifact
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{artifact_id}/download",
    summary="Download artifact file",
    description="Download the actual artifact file"
)
async def download_artifact(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Download artifact file"""
    service = ArtifactService(session)
    try:
        artifact = await service.get_artifact(artifact_id)
        
        # Check if file exists
        if not os.path.exists(artifact.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact file not found: {artifact.file_path}"
            )
        
        return FileResponse(
            path=artifact.file_path,
            filename=artifact.file_name,
            media_type=artifact.mime_type or "application/octet-stream"
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{artifact_id}/content",
    summary="Get artifact content",
    description="Get artifact file content as JSON (for text files)"
)
async def get_artifact_content(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get artifact content"""
    service = ArtifactService(session)
    try:
        artifact = await service.get_artifact(artifact_id)
        
        # Check if file exists
        if not os.path.exists(artifact.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact file not found: {artifact.file_path}"
            )
        
        # Read file content
        try:
            with open(artifact.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "artifact_id": str(artifact.id),
                "file_name": artifact.file_name,
                "mime_type": artifact.mime_type,
                "content": content
            }
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a text file. Use /download endpoint instead."
            )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/run/{run_id}",
    response_model=List[ArtifactResponse],
    summary="Get artifacts by run ID",
    description="Retrieve all artifacts for a specific run"
)
async def get_artifacts_by_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get artifacts by run ID"""
    service = ArtifactService(session)
    artifacts = await service.get_artifacts_by_run(run_id)
    return artifacts


@router.delete(
    "/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete artifact",
    description="Delete artifact metadata and file"
)
async def delete_artifact(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Delete artifact"""
    service = ArtifactService(session)
    try:
        await service.delete_artifact(artifact_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
