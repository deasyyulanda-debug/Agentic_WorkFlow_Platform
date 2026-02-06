"""
RAG (Retrieval-Augmented Generation) Pipeline Module
Provides document ingestion, chunking, embedding, and retrieval capabilities.

Inspired by Orchestra-Research/AI-research-SKILLs RAG patterns:
- ChromaDB for local vector storage
- FAISS for high-performance similarity search
- Sentence Transformers for embedding generation
"""

from .service import RAGService
from .models import (
    RAGPipelineConfig,
    RAGPipelineResponse,
    DocumentUploadResponse,
    ChunkingStrategy,
    EmbeddingProvider,
    VectorStoreType,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGPipelineStatus,
)

__all__ = [
    "RAGService",
    "RAGPipelineConfig",
    "RAGPipelineResponse",
    "DocumentUploadResponse",
    "ChunkingStrategy",
    "EmbeddingProvider",
    "VectorStoreType",
    "RAGQueryRequest",
    "RAGQueryResponse",
    "RAGPipelineStatus",
]
