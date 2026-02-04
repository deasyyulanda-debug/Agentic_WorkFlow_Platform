"""
Settings API Router
Handles provider settings CRUD operations
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db

from models.schemas import (
    SettingsCreate,
    SettingsUpdate,
    SettingsResponse,
    SettingsTestResponse,
)
from services.settings_service import SettingsService
from core.exceptions import (
    SettingsNotFoundError,
    DuplicateSettingsError,
    ValidationError as AppValidationError,
)

router = APIRouter()


@router.post(
    "",
    response_model=SettingsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create provider settings",
    description="Create new provider settings with encrypted API key"
)
async def create_settings(
    settings_data: SettingsCreate,
    session: AsyncSession = Depends(get_db)
):
    """Create new provider settings"""
    service = SettingsService(session)
    try:
        settings = await service.create_settings(settings_data)
        return settings
    except DuplicateSettingsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AppValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[SettingsResponse],
    summary="List all provider settings",
    description="Retrieve all provider settings (without decrypted API keys)"
)
async def list_settings(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    session: AsyncSession = Depends(get_db)
):
    """List all provider settings"""
    service = SettingsService(session)
    all_settings = await service.list_settings(active_only=active_only)
    # Apply pagination
    return all_settings[skip:skip+limit]


@router.get(
    "/{settings_id}",
    response_model=SettingsResponse,
    summary="Get settings by ID",
    description="Retrieve specific provider settings by ID"
)
async def get_settings(
    settings_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Get settings by ID"""
    service = SettingsService(session)
    try:
        settings = await service.get_settings(str(settings_id))
        return settings
    except SettingsNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/provider/{provider}",
    response_model=SettingsResponse,
    summary="Get settings by provider name",
    description="Retrieve provider settings by provider name (e.g., 'gemini', 'openai')"
)
async def get_settings_by_provider(
    provider: str,
    session: AsyncSession = Depends(get_db)
):
    """Get settings by provider name"""
    service = SettingsService(session)
    try:
        settings = await service.get_settings_by_provider(provider.upper())
        return settings
    except SettingsNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{settings_id}",
    response_model=SettingsResponse,
    summary="Update provider settings",
    description="Update existing provider settings"
)
async def update_settings(
    settings_id: UUID,
    settings_data: SettingsUpdate,
    session: AsyncSession = Depends(get_db)
):
    """Update provider settings"""
    service = SettingsService(session)
    try:
        settings = await service.update_settings(str(settings_id), settings_data)
        return settings
    except SettingsNotFoundError as e:
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
    "/{settings_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete provider settings",
    description="Delete provider settings by ID"
)
async def delete_settings(
    settings_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Delete provider settings"""
    service = SettingsService(session)
    try:
        await service.delete_settings(str(settings_id))
    except SettingsNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{settings_id}/test",
    response_model=SettingsTestResponse,
    summary="Test provider API key",
    description="Test if the provider API key is valid by making a test request"
)
async def test_settings(
    settings_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Test provider API key"""
    service = SettingsService(session)
    try:
        result = await service.test_settings(str(settings_id))
        return result
    except SettingsNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.post(
    "/{settings_id}/activate",
    response_model=SettingsResponse,
    summary="Activate provider settings",
    description="Set provider settings as active"
)
async def activate_settings(
    settings_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Activate provider settings"""
    service = SettingsService(session)
    try:
        update_data = SettingsUpdate(is_active=True)
        settings = await service.update_settings(str(settings_id), update_data)
        return settings
    except SettingsNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{settings_id}/deactivate",
    response_model=SettingsResponse,
    summary="Deactivate provider settings",
    description="Set provider settings as inactive"
)
async def deactivate_settings(
    settings_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """Deactivate provider settings"""
    service = SettingsService(session)
    try:
        update_data = SettingsUpdate(is_active=False)
        settings = await service.update_settings(str(settings_id), update_data)
        return settings
    except SettingsNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
