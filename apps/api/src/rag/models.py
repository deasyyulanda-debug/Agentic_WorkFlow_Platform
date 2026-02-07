"""
RAG Pipeline Models - Pydantic schemas for RAG operations
Defines request/response models for document ingestion, querying, and pipeline management.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ChunkingStrategy(str, Enum):
    """Text chunking strategies for document processing"""
    FIXED_SIZE = "fixed_size"          # Fixed character count chunks
    RECURSIVE = "recursive"            # Recursive text splitting
    SENTENCE = "sentence"              # Sentence-level splitting
    PARAGRAPH = "paragraph"            # Paragraph-level splitting


class EmbeddingProvider(str, Enum):
    """Embedding model providers"""
    OPENAI = "openai"                  # text-embedding-3-small / text-embedding-3-large
    CHROMA_DEFAULT = "chroma_default"  # Chroma's built-in (all-MiniLM-L6-v2)


class VectorStoreType(str, Enum):
    """Supported vector store backends"""
    CHROMA = "chroma"                  # ChromaDB (local, easy setup)


class RAGPipelineStatus(str, Enum):
    """Pipeline lifecycle status"""
    CREATED = "created"
    INGESTING = "ingesting"
    READY = "ready"
    ERROR = "error"


# ============================================================================
# Pipeline Configuration
# ============================================================================

class ChunkingConfig(BaseModel):
    """Configuration for document chunking"""
    strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.RECURSIVE,
        description="Chunking strategy to use"
    )
    chunk_size: int = Field(
        default=1000,
        ge=100, le=10000,
        description="Target chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0, le=2000,
        description="Overlap between chunks in characters"
    )

    model_config = ConfigDict(extra='forbid')


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation"""
    provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.CHROMA_DEFAULT,
        description="Embedding provider to use"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model name (e.g., text-embedding-3-small)"
    )

    model_config = ConfigDict(extra='forbid')


class VectorStoreConfig(BaseModel):
    """Configuration for vector store"""
    store_type: VectorStoreType = Field(
        default=VectorStoreType.CHROMA,
        description="Vector store backend"
    )
    collection_name: Optional[str] = Field(
        default=None,
        description="Collection name (auto-generated if not provided)"
    )

    model_config = ConfigDict(extra='forbid')


class RetrievalConfig(BaseModel):
    """Configuration for retrieval step"""
    top_k: int = Field(
        default=5,
        ge=1, le=50,
        description="Number of results to retrieve"
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Minimum similarity score threshold"
    )

    model_config = ConfigDict(extra='forbid')


# ============================================================================
# Request Models
# ============================================================================

class RAGPipelineConfig(BaseModel):
    """Request to create a RAG pipeline"""
    name: str = Field(
        ..., min_length=1, max_length=255,
        description="Pipeline name"
    )
    description: str = Field(
        default="",
        description="Pipeline description"
    )
    chunking: ChunkingConfig = Field(
        default_factory=ChunkingConfig,
        description="Chunking configuration"
    )
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig,
        description="Embedding configuration"
    )
    vector_store: VectorStoreConfig = Field(
        default_factory=VectorStoreConfig,
        description="Vector store configuration"
    )
    retrieval: RetrievalConfig = Field(
        default_factory=RetrievalConfig,
        description="Retrieval configuration"
    )

    model_config = ConfigDict(extra='forbid')


class RAGQueryRequest(BaseModel):
    """Request to query a RAG pipeline"""
    query: str = Field(
        ..., min_length=1,
        description="Query text for retrieval"
    )
    top_k: Optional[int] = Field(
        default=None, ge=1, le=50,
        description="Override default top_k"
    )
    generate_answer: bool = Field(
        default=True,
        description="Whether to generate an LLM-synthesized answer from retrieved chunks"
    )

    model_config = ConfigDict(extra='forbid')


# ============================================================================
# Response Models
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response after document upload and processing"""
    pipeline_id: str
    file_name: str
    file_size_bytes: int
    chunks_created: int
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class RetrievedChunk(BaseModel):
    """A single retrieved chunk from vector search"""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class RAGQueryResponse(BaseModel):
    """Response from querying a RAG pipeline"""
    query: str
    answer: Optional[str] = Field(
        default=None,
        description="LLM-generated answer synthesized from retrieved context"
    )
    results: List[RetrievedChunk]
    total_results: int
    pipeline_id: str

    model_config = ConfigDict(from_attributes=True)


class RAGPipelineResponse(BaseModel):
    """Response for RAG pipeline details"""
    id: str
    name: str
    description: str
    status: RAGPipelineStatus
    config: Dict[str, Any]
    document_count: int = 0
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RAGPipelineListResponse(BaseModel):
    """Response for listing pipelines"""
    pipelines: List[RAGPipelineResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
