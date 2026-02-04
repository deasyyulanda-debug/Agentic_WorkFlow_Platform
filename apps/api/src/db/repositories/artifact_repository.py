"""
Artifact Repository - Data access for run artifacts
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Artifact
from .base import BaseRepository


class ArtifactRepository(BaseRepository[Artifact]):
    """Repository for Artifact operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Artifact)
    
    async def get_by_run(self, run_id: str) -> List[Artifact]:
        """Get all artifacts for a specific run"""
        result = await self.session.execute(
            select(Artifact)
            .where(Artifact.run_id == run_id)
            .order_by(Artifact.created_at)
        )
        return list(result.scalars().all())
    
    async def get_by_type(self, run_id: str, artifact_type: str) -> Optional[Artifact]:
        """Get specific artifact type for a run"""
        result = await self.session.execute(
            select(Artifact)
            .where(Artifact.run_id == run_id)
            .where(Artifact.artifact_type == artifact_type)
        )
        return result.scalar_one_or_none()
    
    async def create_artifact(
        self,
        run_id: str,
        artifact_type: str,
        file_name: str,
        file_path: str,
        **kwargs
    ) -> Artifact:
        """Create a new artifact with required fields"""
        return await self.create(
            run_id=run_id,
            artifact_type=artifact_type,
            file_name=file_name,
            file_path=file_path,
            **kwargs
        )
