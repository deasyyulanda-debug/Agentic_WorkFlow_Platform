"""
Base Repository - Abstract base for all repositories
Provides common CRUD operations with type safety
"""
from typing import TypeVar, Generic, Optional, List, Type, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar('T', bound=DeclarativeMeta)


class BaseRepository(Generic[T]):
    """
    Generic repository for common database operations.
    Follows repository pattern to abstract data access.
    
    Benefits:
    - Centralized query logic
    - Easier testing (mock repositories)
    - Type-safe operations
    - Consistent error handling
    """
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """Create a new entity"""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def get(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination"""
        result = await self.session.execute(
            select(self.model)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def update(self, id: str, **kwargs) -> Optional[T]:
        """Update entity by ID"""
        entity = await self.get(id)
        if not entity:
            return None
        
        for key, value in kwargs.items():
            setattr(entity, key, value)
        
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete entity by ID"""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """Count entities with optional filters"""
        query = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def exists(self, id: str) -> bool:
        """Check if entity exists"""
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return result.scalar_one() > 0
