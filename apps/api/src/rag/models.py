"""
RAG Pipeline Models - Enterprise-Grade Pydantic Schemas
Defines request/response models for document ingestion, querying, and pipeline management.

Enhanced with:
- Multiple embedding providers (Google, Sentence Transformers, HuggingFace, OpenAI)
- Semantic chunking strategy
- Metadata filtering for queries
- Document management models
- Pipeline statistics
- Reranking configuration
- Leverages AI-Research-SKILLs patterns (Chroma, FAISS, Sentence Transformers)
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ChunkingStrategy(str, Enum):
    """Text chunking strategies for document processing.
    Based on AI-Research-SKILLs best practices:
    - recursive is recommended default (LangChain pattern)
    - semantic for meaning-aware splitting
    """
    FIXED_SIZE = "fixed_size"          # Fixed character count chunks
    RECURSIVE = "recursive"            # Recursive text splitting (recommended)
    SENTENCE = "sentence"              # Sentence-level splitting
    PARAGRAPH = "paragraph"            # Paragraph-level splitting
    SEMANTIC = "semantic"              # Meaning-based splitting using embeddings


class EmbeddingProvider(str, Enum):
    """Embedding model providers.
    Leverages AI-Research-SKILLs: Sentence Transformers (5000+ models),
    Chroma defaults, OpenAI, Google, HuggingFace.
    """
    CHROMA_DEFAULT = "chroma_default"        # all-MiniLM-L6-v2 (fast, 384d)
    ST_MPNET = "st_mpnet"                    # all-mpnet-base-v2 (production, 768d)
    ST_ROBERTA = "st_roberta"                # all-roberta-large-v1 (best, 1024d)
    BGE_SMALL = "bge_small"                  # bge-small-en-v1.5 (fast CPU, 384d)
    QWEN3_EMBED = "qwen3_embed"              # Qwen3-Embedding-0.6B (GPU, 1024d)
    OPENAI = "openai"                        # text-embedding-3-small/large
    GOOGLE = "google"                        # Google text embeddings
    SENTENCE_TRANSFORMERS = "sentence_transformers"  # 5000+ models (free, local)
    HUGGINGFACE = "huggingface"              # HuggingFace API embeddings


class VectorStoreType(str, Enum):
    """Supported vector store backends.
    ChromaDB for MVP. Architecture supports future FAISS, Qdrant, Pinecone.
    """
    CHROMA = "chroma"                  # ChromaDB (local, easy setup)
    # Future: FAISS = "faiss"          # Facebook AI Similarity Search
    # Future: QDRANT = "qdrant"        # High-performance Rust vector search
    # Future: PINECONE = "pinecone"    # Managed cloud vector DB


class LLMProvider(str, Enum):
    """LLM providers for answer generation and reranking.
    Users choose provider + model when creating a pipeline.
    """
    GEMINI = "gemini"              # Google Gemini (default, free tier)
    GROQ = "groq"                  # Groq (fast inference)
    OPENROUTER = "openrouter"      # OpenRouter (access to many models)
    OPENAI = "openai"              # OpenAI direct
    ANTHROPIC = "anthropic"        # Anthropic Claude
    DEEPSEEK = "deepseek"          # DeepSeek


class RAGPipelineStatus(str, Enum):
    """Pipeline lifecycle status"""
    CREATED = "created"
    INGESTING = "ingesting"
    READY = "ready"
    ERROR = "error"


class MetadataFilterOperator(str, Enum):
    """Operators for metadata filtering (ChromaDB where clause)"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "nin"


# ============================================================================
# Pipeline Configuration
# ============================================================================

class ChunkingConfig(BaseModel):
    """Configuration for document chunking.
    Follows AI-Research-SKILLs recommendations:
    - General Q&A: 512-1024 chars
    - Long context: 1024-2048 chars
    - Overlap: 10-20% of chunk_size
    """
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
    """Configuration for embedding generation.
    Supports multiple providers per AI-Research-SKILLs patterns.
    """
    provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.CHROMA_DEFAULT,
        description="Embedding provider to use"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model name (e.g., text-embedding-3-small, all-mpnet-base-v2)"
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


class LLMConfig(BaseModel):
    """Configuration for the LLM used in answer generation and reranking.
    Users select provider and model at pipeline creation time.
    """
    provider: LLMProvider = Field(
        default=LLMProvider.GEMINI,
        description="LLM provider for answer generation"
    )
    model: str = Field(
        default="gemini-2.5-flash",
        description="Specific model to use (e.g., gemini-2.5-flash, llama-3.3-70b-versatile)"
    )

    model_config = ConfigDict(extra='forbid')


class RetrievalConfig(BaseModel):
    """Configuration for retrieval step.
    Includes reranking for enterprise-grade quality.
    """
    top_k: int = Field(
        default=10,
        ge=1, le=50,
        description="Number of results to retrieve"
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Minimum similarity score threshold"
    )
    reranking_enabled: bool = Field(
        default=True,
        description="Enable model-based reranking of retrieved chunks for better relevance"
    )
    reranking_top_k: int = Field(
        default=5,
        ge=1, le=20,
        description="Number of chunks to keep after reranking"
    )
    reranker_model: str = Field(
        default="qwen3",
        description="Reranker model: 'qwen3' (Qwen3-Reranker-0.6B, local) or 'llm' (LLM-based)"
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
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM provider and model for answer generation"
    )

    model_config = ConfigDict(extra='forbid')


class MetadataFilter(BaseModel):
    """A single metadata filter condition"""
    field: str = Field(..., description="Metadata field name (e.g., 'file_name', 'chunk_index')")
    operator: MetadataFilterOperator = Field(
        default=MetadataFilterOperator.EQUALS,
        description="Filter operator"
    )
    value: Any = Field(..., description="Filter value")

    model_config = ConfigDict(extra='forbid')


class RAGQueryRequest(BaseModel):
    """Request to query a RAG pipeline.
    Enhanced with metadata filtering and reranking control.
    """
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
    metadata_filters: Optional[List[MetadataFilter]] = Field(
        default=None,
        description="Metadata filters to narrow search results"
    )
    reranking_enabled: Optional[bool] = Field(
        default=None,
        description="Override pipeline reranking setting for this query"
    )

    model_config = ConfigDict(extra='forbid')


# ============================================================================
# Response Models
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response after document upload and processing"""
    pipeline_id: str
    document_id: str
    file_name: str
    file_size_bytes: int
    chunks_created: int
    processing_time_ms: int
    character_count: int
    word_count: int
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class DocumentInfo(BaseModel):
    """Information about an ingested document"""
    id: str
    pipeline_id: str
    file_name: str
    file_size_bytes: int
    file_type: str
    chunk_count: int
    character_count: Optional[int] = None
    word_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RetrievedChunk(BaseModel):
    """A single retrieved chunk from vector search"""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None
    rerank_score: Optional[float] = Field(
        default=None,
        description="LLM-assigned relevance score after reranking"
    )

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
    reranking_applied: bool = Field(
        default=False,
        description="Whether reranking was applied to the results"
    )
    query_time_ms: Optional[int] = Field(
        default=None,
        description="Total query processing time in milliseconds"
    )

    model_config = ConfigDict(from_attributes=True)


class RAGPipelineResponse(BaseModel):
    """Response model for RAG pipeline details"""
    id: str
    name: str
    description: str
    status: RAGPipelineStatus
    config: Dict[str, Any]
    document_count: int
    chunk_count: int
    total_queries: int = 0
    last_query_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineStatistics(BaseModel):
    """Detailed pipeline statistics for observability"""
    pipeline_id: str
    pipeline_name: str
    status: RAGPipelineStatus
    document_count: int
    chunk_count: int
    total_queries: int
    last_query_at: Optional[datetime] = None
    documents: List[DocumentInfo]
    config: Dict[str, Any]
    # Storage info
    embedding_provider: str
    chunking_strategy: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    reranking_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
