"""
Run Repository - Data access for workflow runs
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..models import Run, RunStatus, Workflow
from .base import BaseRepository


class RunRepository(BaseRepository[Run]):
    """Repository for Run operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Run)
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Run]:
        """Get all runs - ordered by newest first"""
        result = await self.session.execute(
            select(Run)
            .order_by(desc(Run.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_with_workflow(self, run_id: str) -> Optional[Run]:
        """Get run with workflow relationship eagerly loaded"""
        result = await self.session.execute(
            select(Run)
            .where(Run.id == run_id)
            .options(selectinload(Run.workflow))  # Eager load workflow
        )
        return result.scalar_one_or_none()
    
    async def get_by_workflow(
        self,
        workflow_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Run]:
        """Get all runs for a specific workflow"""
        result = await self.session.execute(
            select(Run)
            .where(Run.workflow_id == workflow_id)
            .order_by(desc(Run.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_status(
        self,
        status: RunStatus,
        limit: int = 50
    ) -> List[Run]:
        """Get runs by status (for monitoring/cleanup)"""
        result = await self.session.execute(
            select(Run)
            .where(Run.status == status)
            .order_by(desc(Run.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_recent(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[Run]:
        """Get most recent runs across all workflows"""
        result = await self.session.execute(
            select(Run)
            .order_by(desc(Run.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def update_status(
        self,
        run_id: str,
        status: RunStatus,
        error_message: Optional[str] = None
    ) -> Optional[Run]:
        """Update run status (state machine transition)"""
        run = await self.get(run_id)
        if not run:
            return None
        
        run.status = status
        
        # Update timestamps based on status
        if status == RunStatus.VALIDATING and not run.started_at:
            run.started_at = datetime.utcnow()
        elif status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            if not run.completed_at:
                run.completed_at = datetime.utcnow()
            
            # Calculate execution duration
            if run.started_at:
                duration = (run.completed_at - run.started_at).total_seconds()
                run.execution_duration_seconds = int(duration)
        
        if error_message:
            run.error_message = error_message
        
        await self.session.commit()
        await self.session.refresh(run)
        return run
    
    async def update_validation_result(
        self,
        run_id: str,
        validation_result: dict,
        duration_seconds: int
    ) -> Optional[Run]:
        """Update validation result"""
        run = await self.get(run_id)
        if not run:
            return None
        
        run.validation_result = validation_result
        run.validation_duration_seconds = duration_seconds
        
        await self.session.commit()
        await self.session.refresh(run)
        return run
    
    async def update_artifacts(
        self,
        run_id: str,
        artifacts_path: str,
        total_tokens: Optional[int] = None,
        total_cost: Optional[str] = None
    ) -> Optional[Run]:
        """Update run artifacts and usage metrics"""
        run = await self.get(run_id)
        if not run:
            return None
        
        run.artifacts_path = artifacts_path
        if total_tokens:
            run.total_tokens_used = total_tokens
        if total_cost:
            run.total_cost_usd = total_cost
        
        await self.session.commit()
        await self.session.refresh(run)
        return run
    
    async def get_active_runs(self) -> List[Run]:
        """Get all currently active runs (not completed/failed) - ordered by newest first"""
        result = await self.session.execute(
            select(Run).where(
                Run.status.in_([
                    RunStatus.QUEUED,
                    RunStatus.VALIDATING,
                    RunStatus.RUNNING
                ])
            )
            .order_by(desc(Run.created_at))
        )
        return list(result.scalars().all())
    
    async def count_by_status(self, workflow_id: Optional[str] = None) -> dict:
        """Count runs by status (for analytics)"""
        from sqlalchemy import func
        
        query = select(
            Run.status,
            func.count(Run.id).label('count')
        ).group_by(Run.status)
        
        if workflow_id:
            query = query.where(Run.workflow_id == workflow_id)
        
        result = await self.session.execute(query)
        return {row.status: row.count for row in result}
