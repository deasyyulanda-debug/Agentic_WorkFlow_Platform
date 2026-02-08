"""
Database Models - Agentic Workflow Platform
SQLAlchemy ORM models for persistence layer

Design principles:
- UUID primary keys (distributed-friendly)
- Timestamps on all tables (audit trail)
- JSON columns for flexible data (Pydantic validation at app layer)
- Indexes on frequently queried columns
- Soft deletes where appropriate (future feature)
"""
from sqlalchemy import Column, String, Text, DateTime, Enum, Integer, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from .database import Base


# ============================================================================
# Enums
# ============================================================================

class RunStatus(str, enum.Enum):
    """Run execution status - state machine"""
    QUEUED = "queued"           # Initial state after creation
    VALIDATING = "validating"   # Preflight validation in progress
    RUNNING = "running"         # Workflow executing
    COMPLETED = "completed"     # Success
    FAILED = "failed"           # Error occurred
    CANCELLED = "cancelled"     # User cancelled (future)


class RunMode(str, enum.Enum):
    """Run execution mode with different caps"""
    VALIDATE_ONLY = "validate_only"  # Dry run, no execution
    TEST_RUN = "test_run"            # Smoke test with strict caps
    FULL_RUN = "full_run"            # Complete execution


class Provider(str, enum.Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    GROQ = "groq"


class Persona(str, enum.Enum):
    """User personas (workflow categorization)"""
    STUDENT = "student"
    RESEARCHER = "researcher"         # Future
    ML_ENGINEER = "ml_engineer"       # Future
    DATA_SCIENTIST = "data_scientist" # Future
    AI_ARCHITECT = "ai_architect"     # Future


# ============================================================================
# Models
# ============================================================================

class Settings(Base):
    """
    User settings and encrypted secrets.
    MVP: Single user, no user_id enforcement.
    Future: Add user_id foreign key for multi-tenancy.
    """
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Provider configuration
    provider = Column(Enum(Provider), nullable=False, unique=True)
    encrypted_value = Column(Text, nullable=False)  # Fernet encrypted API key
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    last_tested_at = Column(DateTime, nullable=True)  # Last health check
    test_status = Column(String(20), nullable=True)   # "success" or "failed"
    
    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Future: Multi-user support
    # user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_settings_provider', 'provider'),
        Index('idx_settings_is_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Settings(provider={self.provider}, is_active={self.is_active})>"


class Workflow(Base):
    """
    Workflow definitions - templates for agentic workflows.
    Contains schema, default config, and metadata.
    """
    __tablename__ = "workflows"

    id = Column(String(50), primary_key=True)  # e.g., "learn_agentic_ai"
    
    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    persona = Column(Enum(Persona), nullable=False)
    
    # Workflow configuration (JSON)
    schema = Column(JSON, nullable=False)  # Dynamic form schema (fields, types, options)
    default_config = Column(JSON, nullable=True)  # Default values
    
    # Metadata
    version = Column(String(20), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    estimated_duration_seconds = Column(Integer, nullable=True)
    difficulty_level = Column(String(20), nullable=True)  # "beginner", "intermediate", "advanced"
    tags = Column(JSON, nullable=True)  # ["ai", "learning", "llm"]
    
    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    runs = relationship("Run", back_populates="workflow", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_workflows_persona', 'persona'),
        Index('idx_workflows_is_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, persona={self.persona})>"


class Run(Base):
    """
    Workflow execution runs.
    Tracks status, inputs, outputs, and execution metadata.
    """
    __tablename__ = "runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    workflow_id = Column(String(50), ForeignKey("workflows.id"), nullable=False)
    workflow = relationship("Workflow", back_populates="runs")
    
    # Execution config
    inputs = Column(JSON, nullable=False)  # User-provided workflow inputs
    run_mode = Column(Enum(RunMode), nullable=False)
    provider = Column(Enum(Provider), nullable=False)  # Which LLM provider to use
    
    # Status tracking
    status = Column(Enum(RunStatus), default=RunStatus.QUEUED, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Execution metrics
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    validation_duration_seconds = Column(Integer, nullable=True)
    execution_duration_seconds = Column(Integer, nullable=True)
    
    # Outputs
    artifacts_path = Column(String(500), nullable=True)  # Path to artifacts directory
    total_tokens_used = Column(Integer, nullable=True)
    total_cost_usd = Column(String(20), nullable=True)  # Decimal as string (future: proper Decimal type)
    
    # Validation results (JSON)
    validation_result = Column(JSON, nullable=True)  # Preflight validation details
    
    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Future: Multi-user support
    # user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_runs_workflow_id', 'workflow_id'),
        Index('idx_runs_status', 'status'),
        Index('idx_runs_created_at', 'created_at'),
        Index('idx_runs_provider', 'provider'),
        # Composite index for common query (filter by workflow + status)
        Index('idx_runs_workflow_status', 'workflow_id', 'status'),
    )

    def __repr__(self):
        return f"<Run(id={self.id}, workflow={self.workflow_id}, status={self.status})>"


class Artifact(Base):
    """
    Run artifacts - output files generated by workflows.
    Examples: notes.md, trace.json, logs.txt
    """
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    run = relationship("Run", back_populates="artifacts")
    
    # Artifact metadata
    artifact_type = Column(String(50), nullable=False)  # "notes", "trace", "logs", "output"
    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path from artifacts root
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)  # "text/markdown", "application/json"
    
    # Content metadata (optional)
    summary = Column(Text, nullable=True)  # Brief description of artifact content
    
    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_artifacts_run_id', 'run_id'),
        Index('idx_artifacts_type', 'artifact_type'),
    )

    def __repr__(self):
        return f"<Artifact(id={self.id}, run={self.run_id}, type={self.artifact_type})>"


# ============================================================================
# RAG Pipeline Models
# ============================================================================

class RAGPipelineStatus(str, enum.Enum):
    """RAG Pipeline lifecycle status"""
    CREATED = "created"
    INGESTING = "ingesting"
    READY = "ready"
    ERROR = "error"


class RAGPipelineDB(Base):
    """
    RAG Pipeline definitions - persisted to database.
    Stores pipeline config, status, and metadata.
    """
    __tablename__ = "rag_pipelines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    status = Column(Enum(RAGPipelineStatus), default=RAGPipelineStatus.CREATED, nullable=False)

    # Configuration (JSON)
    chunking_config = Column(JSON, nullable=False)    # strategy, chunk_size, chunk_overlap
    embedding_config = Column(JSON, nullable=False)    # provider, model
    vector_store_config = Column(JSON, nullable=False)  # store_type, collection_name
    retrieval_config = Column(JSON, nullable=False)    # top_k, score_threshold, reranking
    llm_config = Column(JSON, nullable=False, default={"provider": "gemini", "model": "gemini-2.5-flash"})  # provider, model

    # Stats
    document_count = Column(Integer, default=0, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    total_queries = Column(Integer, default=0, nullable=False)
    last_query_at = Column(DateTime, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    documents = relationship("RAGDocumentDB", back_populates="pipeline", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_rag_pipelines_status', 'status'),
        Index('idx_rag_pipelines_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<RAGPipeline(id={self.id}, name={self.name}, status={self.status})>"


class RAGDocumentDB(Base):
    """
    Documents ingested into RAG pipelines.
    Tracks individual document metadata and chunk information.
    """
    __tablename__ = "rag_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Relationships
    pipeline_id = Column(String(36), ForeignKey("rag_pipelines.id"), nullable=False)
    pipeline = relationship("RAGPipelineDB", back_populates="documents")

    # Document metadata
    file_name = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(20), nullable=False)  # .pdf, .txt, .md, etc.
    chunk_count = Column(Integer, default=0, nullable=False)

    # Processing metadata
    status = Column(String(20), default="processed", nullable=False)  # processed, error
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Content stats
    character_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_rag_documents_pipeline_id', 'pipeline_id'),
        Index('idx_rag_documents_file_name', 'file_name'),
    )

    def __repr__(self):
        return f"<RAGDocument(id={self.id}, file={self.file_name}, pipeline={self.pipeline_id})>"


# ============================================================================
# Future Models (Placeholder for multi-user feature)
# ============================================================================

# class User(Base):
#     """
#     User accounts for multi-tenancy.
#     Future feature - not in MVP.
#     """
#     __tablename__ = "users"
#
#     id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     email = Column(String(255), unique=True, nullable=False)
#     hashed_password = Column(String(255), nullable=False)
#     full_name = Column(String(200), nullable=True)
#     is_active = Column(Boolean, default=True, nullable=False)
#     is_admin = Column(Boolean, default=False, nullable=False)
#     
#     created_at = Column(DateTime, server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
#     
#     # Relationships
#     settings = relationship("Settings", back_populates="user")
#     runs = relationship("Run", back_populates="user")
