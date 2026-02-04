"""
Settings Repository - Data access for provider settings and secrets
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Settings, Provider
from .base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    """Repository for Settings operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Settings)
    
    async def get_by_provider(self, provider: Provider) -> Optional[Settings]:
        """Get settings for a specific provider"""
        result = await self.session.execute(
            select(Settings).where(Settings.provider == provider)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self) -> List[Settings]:
        """Get all active provider settings"""
        result = await self.session.execute(
            select(Settings).where(Settings.is_active == True)
        )
        return list(result.scalars().all())
    
    async def upsert(self, provider: Provider, encrypted_value: str) -> Settings:
        """
        Insert or update provider settings.
        If exists, update. If not, create new.
        """
        existing = await self.get_by_provider(provider)
        
        if existing:
            # Update existing
            existing.encrypted_value = encrypted_value
            existing.is_active = True
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new
            return await self.create(
                provider=provider,
                encrypted_value=encrypted_value,
                is_active=True
            )
    
    async def mark_tested(
        self,
        provider: Provider,
        success: bool,
        tested_at
    ) -> Optional[Settings]:
        """Mark a provider as tested with result"""
        setting = await self.get_by_provider(provider)
        if not setting:
            return None
        
        setting.last_tested_at = tested_at
        setting.test_status = "success" if success else "failed"
        
        await self.session.commit()
        await self.session.refresh(setting)
        return setting
    
    async def deactivate(self, provider: Provider) -> bool:
        """Deactivate a provider (soft delete)"""
        setting = await self.get_by_provider(provider)
        if not setting:
            return False
        
        setting.is_active = False
        await self.session.commit()
        return True
