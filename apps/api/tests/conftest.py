"""
Pytest Configuration and Fixtures
Provides test client, database, and common fixtures
"""
import pytest
import asyncio
import sys
import os
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from db.database import Base, get_db
from core.config import settings
from core.security import init_security
from rag.service import set_session_factory, get_rag_service

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_db_engine, test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with test database"""
    
    # Override database dependency
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Override RAG service session factory to use test DB
    test_session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    set_session_factory(test_session_factory)
    
    # Reset RAG service singleton so it uses the test DB
    import rag.service as rag_module
    rag_module._rag_service = None
    
    # Initialize security
    init_security(settings.SECRET_KEY)
    
    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()
    set_session_factory(None)
    rag_module._rag_service = None


@pytest.fixture
def sample_settings_data():
    """Sample settings data for testing"""
    return {
        "provider": "gemini",  # Lowercase to match ProviderEnum
        "api_key": "test-api-key-1234567890",
        "is_active": True
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing"""
    return {
        "name": "Test Workflow",
        "description": "A test workflow for automated testing",
        "persona": "student",  # Lowercase to match PersonaEnum
        "definition": {  # Changed from schema to definition
            "steps": [
                {
                    "type": "prompt",
                    "template": "Write a short poem about {{topic}}",
                    "system_prompt": "You are a creative poet.",
                    "temperature": 0.8,
                    "max_tokens": 100,
                    "output_variable": "poem"
                },
                {
                    "type": "validate",
                    "source": "poem",
                    "rules": [
                        {"type": "not_empty"},
                        {"type": "min_length", "value": 10}
                    ]
}
            ]
        },
        "is_active": True,
        "tags": ["test", "poetry"]
    }


@pytest.fixture
def sample_run_data():
    """Sample run data for testing"""
    return {
        "input_data": {"topic": "artificial intelligence"},  # Changed from inputs
        "mode": "test_run",  # Changed from run_mode
        # provider removed - not part of RunCreate schema
    }
