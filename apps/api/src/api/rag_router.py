"""
RAG Pipeline API Router - Enterprise-Grade Endpoints
Handles RAG pipeline CRUD, document management, querying, and statistics.

Endpoints:
- POST   /pipelines              - Create pipeline
- GET    /pipelines              - List pipelines
- GET    /pipelines/{id}         - Get pipeline details
- DELETE /pipelines/{id}         - Delete pipeline
- POST   /pipelines/{id}/documents        - Upload document
- GET    /pipelines/{id}/documents        - List documents
- DELETE /pipelines/{id}/documents/{doc}  - Delete document
- POST   /pipelines/{id}/query            - Query pipeline
- GET    /pipelines/{id}/stats            - Pipeline statistics
- GET    /config/options                  - Configuration options
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import List

from rag.models import (
    RAGPipelineConfig,
    RAGPipelineResponse,
    DocumentUploadResponse,
    DocumentInfo,
    RAGQueryRequest,
    RAGQueryResponse,
    PipelineStatistics,
)
from rag.service import get_rag_service

router = APIRouter()


# ============================================================================
# Pipeline CRUD
# ============================================================================

@router.post(
    "/pipelines",
    response_model=RAGPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create RAG pipeline",
    description="Create a new RAG pipeline with chunking, embedding, and retrieval configuration",
)
async def create_pipeline(config: RAGPipelineConfig):
    """Create a new RAG pipeline."""
    service = get_rag_service()
    try:
        pipeline = await service.create_pipeline(config)
        return pipeline
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/pipelines",
    response_model=List[RAGPipelineResponse],
    summary="List RAG pipelines",
    description="List all RAG pipelines (persisted, survives restarts)",
)
async def list_pipelines():
    """List all RAG pipelines."""
    service = get_rag_service()
    return await service.list_pipelines()


@router.get(
    "/pipelines/{pipeline_id}",
    response_model=RAGPipelineResponse,
    summary="Get RAG pipeline",
    description="Get details of a specific RAG pipeline",
)
async def get_pipeline(pipeline_id: str):
    """Get pipeline details."""
    service = get_rag_service()
    try:
        return await service.get_pipeline(pipeline_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/pipelines/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete RAG pipeline",
    description="Delete a RAG pipeline and all its data (DB + ChromaDB)",
)
async def delete_pipeline(pipeline_id: str):
    """Delete a pipeline."""
    service = get_rag_service()
    try:
        await service.delete_pipeline(pipeline_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Document Management
# ============================================================================

@router.post(
    "/pipelines/{pipeline_id}/documents",
    response_model=DocumentUploadResponse,
    summary="Upload document to RAG pipeline",
    description="Upload and ingest a document (TXT, CSV, MD, PDF, JSON, DOCX, HTML) into a RAG pipeline",
)
async def upload_document(
    pipeline_id: str,
    file: UploadFile = File(..., description="Document file to upload"),
):
    """Upload and ingest a document into the pipeline."""
    # Validate file type
    allowed_extensions = {".txt", ".csv", ".md", ".pdf", ".json", ".docx", ".html", ".htm"}
    file_ext = ""
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(sorted(allowed_extensions))}",
        )

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )

    # Limit file size (20MB for enterprise use)
    max_size = 20 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large (max {max_size // (1024*1024)}MB)",
        )

    service = get_rag_service()
    try:
        result = await service.ingest_document(
            pipeline_id=pipeline_id,
            file_name=file.filename or "unnamed",
            file_content=content,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {str(e)}",
        )


@router.get(
    "/pipelines/{pipeline_id}/documents",
    response_model=List[DocumentInfo],
    summary="List pipeline documents",
    description="List all documents ingested into a RAG pipeline",
)
async def list_documents(pipeline_id: str):
    """List all documents in a pipeline."""
    service = get_rag_service()
    try:
        return await service.list_documents(pipeline_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/pipelines/{pipeline_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document from pipeline",
    description="Delete a specific document and its chunks from a RAG pipeline",
)
async def delete_document(pipeline_id: str, document_id: str):
    """Delete a specific document from a pipeline."""
    service = get_rag_service()
    try:
        await service.delete_document(pipeline_id, document_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Query
# ============================================================================

@router.post(
    "/pipelines/{pipeline_id}/query",
    response_model=RAGQueryResponse,
    summary="Query RAG pipeline",
    description="Query a RAG pipeline with optional metadata filtering and LLM reranking",
)
async def query_pipeline(
    pipeline_id: str,
    request: RAGQueryRequest,
):
    """Query the pipeline for relevant chunks with optional reranking."""
    service = get_rag_service()
    try:
        return await service.query(pipeline_id, request)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )


# ============================================================================
# Statistics
# ============================================================================

@router.get(
    "/pipelines/{pipeline_id}/stats",
    response_model=PipelineStatistics,
    summary="Get pipeline statistics",
    description="Get detailed statistics and observability data for a RAG pipeline",
)
async def get_pipeline_stats(pipeline_id: str):
    """Get detailed pipeline statistics."""
    service = get_rag_service()
    try:
        return await service.get_statistics(pipeline_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Configuration Options
# ============================================================================

@router.get(
    "/config/options",
    summary="Get RAG configuration options",
    description="Get available options for RAG pipeline configuration (chunking strategies, embedding providers, etc.)",
)
async def get_config_options():
    """Return available configuration options for the RAG pipeline builder UI."""
    return {
        "chunking_strategies": [
            {
                "value": "fixed_size",
                "label": "Fixed Size",
                "description": "Split text into fixed character count chunks",
            },
            {
                "value": "recursive",
                "label": "Recursive (Recommended)",
                "description": "Recursively split using hierarchy of separators - best for general use",
            },
            {
                "value": "sentence",
                "label": "Sentence",
                "description": "Split text by sentences, grouping into chunks",
            },
            {
                "value": "paragraph",
                "label": "Paragraph",
                "description": "Split text by paragraphs",
            },
            {
                "value": "semantic",
                "label": "Semantic (AI-powered)",
                "description": "Split by meaning boundaries using sentence embeddings - best quality chunks",
            },
        ],
        "embedding_providers": [
            {
                "value": "bge_small",
                "label": "BGE-Small-EN v1.5 (Speed: Fast | Quality: Strong | Use: Best CPU Default)",
                "description": "384 dimensions, ~3000 sent/sec, 130MB — MTEB top-ranked small model, free & local",
            },
            {
                "value": "chroma_default",
                "label": "all-MiniLM-L6-v2 (Speed: Fast | Quality: Good | Use: General & Prototyping)",
                "description": "384 dimensions, ~2000 sent/sec, 120MB — Quick testing, free & local",
            },
            {
                "value": "st_mpnet",
                "label": "all-mpnet-base-v2 (Speed: Medium | Quality: Better | Use: Production RAG)",
                "description": "768 dimensions, ~600 sent/sec, 420MB — Recommended for production, free & local",
            },
            {
                "value": "st_roberta",
                "label": "all-roberta-large-v1 (Speed: Slow | Quality: Best | Use: High Accuracy)",
                "description": "1024 dimensions, ~300 sent/sec, 1.3GB — Maximum quality, free & local",
            },
            {
                "value": "qwen3_embed",
                "label": "Qwen3-Embedding-0.6B (Speed: Slow | Quality: SOTA | Use: GPU Recommended)",
                "description": "1024 dimensions, 0.6B params, 1.2GB — State-of-the-art MTEB, slow on CPU",
            },
            {
                "value": "openai",
                "label": "OpenAI Embeddings",
                "description": "OpenAI text-embedding-3-small/large (requires API key)",
            },
            {
                "value": "google",
                "label": "Google Embeddings",
                "description": "Google text embeddings via Generative AI API (requires API key)",
            },
            {
                "value": "sentence_transformers",
                "label": "Sentence Transformers (Custom Model)",
                "description": "Choose from 5000+ models on HuggingFace, free & local",
            },
            {
                "value": "huggingface",
                "label": "HuggingFace API",
                "description": "HuggingFace Inference API embeddings (requires API key)",
            },
        ],
        "vector_stores": [
            {
                "value": "chroma",
                "label": "ChromaDB",
                "description": "Open-source vector database, runs locally, persisted to disk",
            },
        ],
        "reranker_models": [
            {
                "value": "qwen3",
                "label": "Qwen3-Reranker-0.6B (Local, Free, High Quality)",
                "description": "State-of-the-art reranker, runs locally on CPU, no API cost. ~1.2GB download.",
            },
            {
                "value": "llm",
                "label": "LLM-Based Reranking (Uses Pipeline LLM)",
                "description": "Uses your configured LLM provider for reranking. Costs API calls.",
            },
        ],
        "supported_file_types": [
            {"extension": ".txt", "label": "Text Files"},
            {"extension": ".pdf", "label": "PDF Documents"},
            {"extension": ".md", "label": "Markdown Files"},
            {"extension": ".csv", "label": "CSV Files"},
            {"extension": ".json", "label": "JSON Files"},
            {"extension": ".docx", "label": "Word Documents"},
            {"extension": ".html", "label": "HTML Files"},
        ],
        "llm_providers": [
            {
                "value": "gemini",
                "label": "Google Gemini",
                "description": "Google Gemini models (requires GOOGLE_API_KEY)",
                "models": [
                    {"value": "gemini-2.5-flash", "label": "Gemini 2.5 Flash (Default)", "default": True},
                    {"value": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
                    {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
                    {"value": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"},
                    {"value": "gemini-1.5-flash", "label": "Gemini 1.5 Flash"},
                ],
            },
            {
                "value": "groq",
                "label": "Groq",
                "description": "Ultra-fast inference engine (requires GROQ_API_KEY)",
                "models": [
                    {"value": "llama-3.3-70b-versatile", "label": "LLaMA 3.3 70B Versatile", "default": True},
                    {"value": "llama-3.1-8b-instant", "label": "LLaMA 3.1 8B Instant"},
                ],
            },
            {
                "value": "openrouter",
                "label": "OpenRouter",
                "description": "Access 100+ models via one API (requires OPENROUTER_API_KEY)",
                "models": [
                    {"value": "anthropic/claude-sonnet-4.5", "label": "Claude Sonnet 4.5", "default": True},
                    {"value": "anthropic/claude-opus-4.5", "label": "Claude Opus 4.5"},
                    {"value": "openai/gpt-oss-120b", "label": "GPT OSS 120B"},
                    {"value": "openai/gpt-5.2", "label": "GPT 5.2"},
                    {"value": "openai/gpt-oss-safeguard-20b", "label": "GPT OSS Safeguard 20B"},
                    {"value": "openai/gpt-5.2-codex", "label": "GPT 5.2 Codex"},
                    {"value": "deepseek/deepseek-v3.2", "label": "DeepSeek V3.2"},
                    {"value": "tngtech/deepseek-r1t2-chimera:free", "label": "DeepSeek R1T2 Chimera (Free)"},
                    {"value": "nex-agi/deepseek-v3.1-nex-n1", "label": "DeepSeek V3.1 Nex N1"},
                    {"value": "deepseek/deepseek-v3.2-speciale", "label": "DeepSeek V3.2 Speciale"},
                    {"value": "google/gemini-3-flash-preview", "label": "Gemini 3 Flash Preview"},
                    {"value": "google/gemini-3-pro-preview", "label": "Gemini 3 Pro Preview"},
                    {"value": "moonshotai/kimi-k2.5", "label": "Kimi K2.5"},
                ],
            },
            {
                "value": "openai",
                "label": "OpenAI",
                "description": "OpenAI models (requires OPENAI_API_KEY)",
                "models": [
                    {"value": "gpt-5.2-2025-12-11", "label": "GPT 5.2 (2025-12-11)", "default": True},
                    {"value": "o3-deep-research-2025-06-26", "label": "O3 Deep Research"},
                    {"value": "gpt-5.2-pro-2025-12-11", "label": "GPT 5.2 Pro"},
                    {"value": "o4-mini-deep-research-2025-06-26", "label": "O4 Mini Deep Research"},
                    {"value": "gpt-5.2-codex", "label": "GPT 5.2 Codex"},
                    {"value": "gpt-5-mini-2025-08-07", "label": "GPT 5 Mini"},
                ],
            },
            {
                "value": "anthropic",
                "label": "Anthropic",
                "description": "Anthropic Claude models (requires ANTHROPIC_API_KEY)",
                "models": [
                    {"value": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4", "default": True},
                    {"value": "claude-opus-4-20250514", "label": "Claude Opus 4"},
                    {"value": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku"},
                ],
            },
            {
                "value": "deepseek",
                "label": "DeepSeek",
                "description": "DeepSeek models (requires DEEPSEEK_API_KEY)",
                "models": [
                    {"value": "deepseek-chat", "label": "DeepSeek Chat", "default": True},
                    {"value": "deepseek-coder", "label": "DeepSeek Coder"},
                ],
            },
        ],
        "defaults": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "top_k": 10,
            "chunking_strategy": "recursive",
            "embedding_provider": "bge_small",
            "vector_store": "chroma",
            "reranking_enabled": True,
            "reranking_top_k": 5,
            "reranker_model": "qwen3",
            "max_file_size_mb": 20,
            "llm_provider": "gemini",
            "llm_model": "gemini-2.5-flash",
        },
    }
