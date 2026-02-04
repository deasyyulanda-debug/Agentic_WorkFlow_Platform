"""
Artifact Service - Artifact Storage Management
Handles storage and retrieval of run artifacts
"""
from typing import Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Artifact as ArtifactModel
from db.repositories import ArtifactRepository, RunRepository
from models.schemas import (
    ArtifactCreate,
    ArtifactResponse
)
from core import (
    RunNotFoundError,
    NotFoundError,
    get_logger,
    settings
)


class ArtifactService:
    """
    Service for managing run artifacts.
    
    Responsibilities:
    - Store artifacts (prompts, responses, logs)
    - Retrieve artifacts by run or type
    - Manage artifact file storage
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ArtifactRepository(session)
        self.run_repository = RunRepository(session)
        self.logger = get_logger(__name__)
        self.artifacts_path = Path(settings.ARTIFACTS_PATH)
        
        # Ensure artifacts directory exists
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
    
    async def create_artifact(self, data: ArtifactCreate) -> ArtifactResponse:
        """
        Create a new artifact.
        
        Args:
            data: Artifact creation data
            
        Returns:
            Created artifact
            
        Raises:
            RunNotFoundError: If run doesn't exist
        """
        # Verify run exists
        run = await self.run_repository.get(data.run_id)
        if not run:
            raise RunNotFoundError(data.run_id)
        
        self.logger.info(
            f"Creating {data.artifact_type} artifact for run {data.run_id}",
            run_id=data.run_id,
            artifact_type=data.artifact_type
        )
        
        # If content is large, store in file instead of database
        file_path = None
        content_to_store = data.content
        
        if len(data.content) > 10000:  # 10KB threshold
            # Store in file
            file_path = await self._store_content_to_file(
                data.run_id,
                data.artifact_type,
                data.content
            )
            # Store file path reference in database
            content_to_store = {"file_path": str(file_path)}
            self.logger.debug(f"Large content stored to file: {file_path}")
        
        # Create artifact
        # Generate file name and path (even if content stored in DB, these are required for consistency)
        if not file_path:
            # Content not stored in file yet - write it now
            import time
            timestamp = int(time.time() * 1000)
            file_name = f"{data.artifact_type}_{timestamp}.json"
            actual_file_path = await self._store_content_to_file(
                data.run_id, data.artifact_type, content_to_store
            )
            file_path = str(actual_file_path)  # Convert Path to string for database
        else:
            file_path = str(file_path)  # Ensure it's a string
            file_name = file_path.split("/")[-1]
        
        # Calculate file size
        file_size = len(content_to_store.encode('utf-8')) if content_to_store else 0
        
        artifact = await self.repository.create_artifact(
            run_id=data.run_id,
            artifact_type=data.artifact_type,
            file_name=file_name,
            file_path=file_path,
            file_size_bytes=file_size,
            mime_type="application/json",
            metadata=data.metadata
        )
        
        self.logger.info(f"Artifact created: {artifact.id}", run_id=data.run_id)
        
        return ArtifactResponse.model_validate(artifact)
    
    async def get_artifact(self, artifact_id: str) -> ArtifactResponse:
        """Get artifact by ID"""
        artifact = await self.repository.get(artifact_id)
        if not artifact:
            raise NotFoundError("Artifact", artifact_id)
        
        # If content is in file, read it
        if isinstance(artifact.content, dict) and "file_path" in artifact.content:
            file_path = Path(artifact.content["file_path"])
            if file_path.exists():
                artifact.content = await self._read_content_from_file(file_path)
        
        return ArtifactResponse.model_validate(artifact)
    
    async def get_artifacts_by_run(self, run_id: str) -> list[ArtifactResponse]:
        """
        Get all artifacts for a run.
        
        Args:
            run_id: Run ID
            
        Returns:
            List of artifacts
        """
        run = await self.run_repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        artifacts = await self.repository.get_by_run(run_id)
        
        return [ArtifactResponse.model_validate(a) for a in artifacts]
    
    async def get_artifacts_by_type(
        self,
        run_id: str,
        artifact_type: str
    ) -> list[ArtifactResponse]:
        """
        Get artifacts of a specific type for a run.
        
        Args:
            run_id: Run ID
            artifact_type: Type of artifact
            
        Returns:
            List of artifacts
        """
        run = await self.run_repository.get(run_id)
        if not run:
            raise RunNotFoundError(run_id)
        
        artifacts = await self.repository.get_by_type(run_id, artifact_type)
        
        return [ArtifactResponse.model_validate(a) for a in artifacts]
    
    async def delete_artifact(self, artifact_id: str) -> bool:
        """
        Delete an artifact.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            True if deleted
        """
        artifact = await self.repository.get(artifact_id)
        if not artifact:
            raise NotFoundError("Artifact", artifact_id)
        
        # Delete file if exists
        if isinstance(artifact.content, dict) and "file_path" in artifact.content:
            file_path = Path(artifact.content["file_path"])
            if file_path.exists():
                file_path.unlink()
                self.logger.debug(f"Deleted artifact file: {file_path}")
        
        # Delete from database
        await self.repository.delete(artifact_id)
        
        self.logger.info(f"Artifact deleted: {artifact_id}")
        
        return True
    
    async def delete_run_artifacts(self, run_id: str) -> int:
        """
        Delete all artifacts for a run.
        
        Args:
            run_id: Run ID
            
        Returns:
            Number of artifacts deleted
        """
        artifacts = await self.repository.get_by_run(run_id)
        
        count = 0
        for artifact in artifacts:
            await self.delete_artifact(artifact.id)
            count += 1
        
        self.logger.info(f"Deleted {count} artifacts for run {run_id}", run_id=run_id)
        
        return count
    
    async def _store_content_to_file(
        self,
        run_id: str,
        artifact_type: str,
        content: dict
    ) -> Path:
        """
        Store artifact content to file.
        
        Args:
            run_id: Run ID
            artifact_type: Artifact type
            content: Content to store
            
        Returns:
            Path to stored file
        """
        # Create run directory
        run_dir = self.artifacts_path / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        import time
        timestamp = int(time.time() * 1000)
        filename = f"{artifact_type}_{timestamp}.json"
        file_path = run_dir / filename
        
        # Write content
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        
        return file_path
    
    async def _read_content_from_file(self, file_path: Path) -> dict:
        """
        Read artifact content from file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Content dictionary
        """
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
