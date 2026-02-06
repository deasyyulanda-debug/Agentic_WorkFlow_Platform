"""
RAG Pipeline API Router
Handles RAG pipeline creation, document upload, and querying.
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import List

from rag.models import (
    RAGPipelineConfig,
    RAGPipelineResponse,
    DocumentUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from rag.service import get_rag_service

router = APIRouter()


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
    description="List all RAG pipelines",
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
    description="Delete a RAG pipeline and all its data",
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


@router.post(
    "/pipelines/{pipeline_id}/documents",
    response_model=DocumentUploadResponse,
    summary="Upload document to RAG pipeline",
    description="Upload and ingest a document (TXT, CSV, MD, PDF, JSON) into a RAG pipeline",
)
async def upload_document(
    pipeline_id: str,
    file: UploadFile = File(..., description="Document file to upload"),
):
    """Upload and ingest a document into the pipeline."""
    # Validate file type
    allowed_extensions = {".txt", ".csv", ".md", ".pdf", ".json"}
    file_ext = ""
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(allowed_extensions)}",
        )

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )

    # Limit file size (10MB)
    max_size = 10 * 1024 * 1024
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


@router.post(
    "/pipelines/{pipeline_id}/query",
    response_model=RAGQueryResponse,
    summary="Query RAG pipeline",
    description="Query a RAG pipeline to retrieve relevant document chunks",
)
async def query_pipeline(
    pipeline_id: str,
    request: RAGQueryRequest,
):
    """Query the pipeline for relevant chunks."""
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
                "label": "Recursive",
                "description": "Recursively split using hierarchy of separators (recommended)",
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
        ],
        "embedding_providers": [
            {
                "value": "chroma_default",
                "label": "ChromaDB Default (all-MiniLM-L6-v2)",
                "description": "Built-in sentence transformer model, no API key needed",
            },
            {
                "value": "openai",
                "label": "OpenAI Embeddings",
                "description": "OpenAI text-embedding-3-small/large (requires API key)",
            },
        ],
        "vector_stores": [
            {
                "value": "chroma",
                "label": "ChromaDB",
                "description": "Open-source vector database, runs locally",
            },
        ],
        "defaults": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "top_k": 5,
            "chunking_strategy": "recursive",
            "embedding_provider": "chroma_default",
            "vector_store": "chroma",
        },
    }
