"""
Workflow Repository - Data access for workflow definitions
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Workflow, Persona
from .base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for Workflow operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Workflow)
    
    async def get_by_persona(self, persona: Persona) -> List[Workflow]:
        """Get all workflows for a specific persona"""
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.persona == persona)
            .where(Workflow.is_active == True)
            .order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_active(self, limit: int = 100, offset: int = 0) -> List[Workflow]:
        """Get all active workflows"""
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.is_active == True)
            .order_by(Workflow.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def search_by_tag(self, tag: str) -> List[Workflow]:
        """
        Search workflows by tag.
        Note: SQLite JSON functions limited, better with PostgreSQL.
        """
        # Simple LIKE search in JSON (works but not optimal)
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.is_active == True)
            .where(Workflow.tags.contains(tag))  # SQLAlchemy 2.0 JSON contains
        )
        return list(result.scalars().all())
    
    async def get_by_difficulty(self, difficulty: str) -> List[Workflow]:
        """Get workflows by difficulty level"""
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.is_active == True)
            .where(Workflow.difficulty_level == difficulty)
            .order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def list(self) -> List[Workflow]:
        """Get all workflows - ordered by newest first"""
        result = await self.session.execute(
            select(Workflow).order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())
