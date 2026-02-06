"""
RAG Pipeline Service - Core business logic for RAG operations.

Handles document processing pipeline:
1. Document Upload → Parse text from files
2. Chunking → Split text into manageable chunks
3. Embedding → Generate vector embeddings (via ChromaDB default or OpenAI)
4. Storage → Store in ChromaDB vector database
5. Retrieval → Similarity search for queries

Follows AI-Research-SKILLs patterns:
- ChromaDB for local vector storage
- Configurable chunking strategies
- Multiple embedding provider support
"""
import os
import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from core import get_logger, settings

from .models import (
    RAGPipelineConfig,
    RAGPipelineResponse,
    RAGPipelineStatus,
    DocumentUploadResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RetrievedChunk,
    ChunkingStrategy,
    EmbeddingProvider,
)


class RAGService:
    """
    Service for managing RAG pipelines.

    Responsibilities:
    - Pipeline CRUD
    - Document ingestion and chunking
    - Embedding generation
    - Vector store management
    - Similarity search / retrieval
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        self._chroma_clients: Dict[str, Any] = {}

        # ChromaDB storage path
        self._chroma_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "chroma"
        )
        os.makedirs(self._chroma_path, exist_ok=True)

    def _get_chroma_client(self, pipeline_id: str):
        """Get or create a ChromaDB client for a pipeline."""
        if pipeline_id in self._chroma_clients:
            return self._chroma_clients[pipeline_id]

        try:
            import chromadb
        except ImportError:
            raise RuntimeError(
                "chromadb is not installed. Install it with: pip install chromadb"
            )

        persist_dir = os.path.join(self._chroma_path, pipeline_id)
        os.makedirs(persist_dir, exist_ok=True)

        client = chromadb.PersistentClient(path=persist_dir)
        self._chroma_clients[pipeline_id] = client
        return client

    async def create_pipeline(self, config: RAGPipelineConfig) -> RAGPipelineResponse:
        """Create a new RAG pipeline with the given configuration."""
        pipeline_id = str(uuid.uuid4())
        now = datetime.utcnow()

        collection_name = config.vector_store.collection_name or f"pipeline_{pipeline_id[:8]}"

        # Initialize ChromaDB collection
        client = self._get_chroma_client(pipeline_id)
        client.get_or_create_collection(name=collection_name)

        pipeline_data = {
            "id": pipeline_id,
            "name": config.name,
            "description": config.description,
            "status": RAGPipelineStatus.CREATED,
            "config": {
                "chunking": config.chunking.model_dump(),
                "embedding": config.embedding.model_dump(),
                "vector_store": {
                    **config.vector_store.model_dump(),
                    "collection_name": collection_name,
                },
                "retrieval": config.retrieval.model_dump(),
            },
            "document_count": 0,
            "chunk_count": 0,
            "created_at": now,
            "updated_at": now,
        }

        self._pipelines[pipeline_id] = pipeline_data

        self.logger.info(f"RAG pipeline created: {pipeline_id} ({config.name})")

        return RAGPipelineResponse(**pipeline_data)

    async def get_pipeline(self, pipeline_id: str) -> RAGPipelineResponse:
        """Get pipeline by ID."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        return RAGPipelineResponse(**self._pipelines[pipeline_id])

    async def list_pipelines(self) -> List[RAGPipelineResponse]:
        """List all pipelines."""
        return [RAGPipelineResponse(**p) for p in self._pipelines.values()]

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline and its data."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Clean up ChromaDB client
        if pipeline_id in self._chroma_clients:
            del self._chroma_clients[pipeline_id]

        del self._pipelines[pipeline_id]
        self.logger.info(f"RAG pipeline deleted: {pipeline_id}")
        return True

    async def ingest_document(
        self,
        pipeline_id: str,
        file_name: str,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        """
        Ingest a document into a RAG pipeline.

        Steps:
        1. Parse text from the uploaded file
        2. Chunk the text according to pipeline config
        3. Store chunks in ChromaDB (embeddings auto-generated)
        """
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        pipeline = self._pipelines[pipeline_id]
        pipeline["status"] = RAGPipelineStatus.INGESTING
        pipeline["updated_at"] = datetime.utcnow()

        try:
            # 1. Parse text from file
            text = self._parse_document(file_name, file_content)

            if not text.strip():
                raise ValueError("Document contains no extractable text")

            # 2. Chunk the text
            chunking_config = pipeline["config"]["chunking"]
            chunks = self._chunk_text(
                text,
                strategy=ChunkingStrategy(chunking_config["strategy"]),
                chunk_size=chunking_config["chunk_size"],
                chunk_overlap=chunking_config["chunk_overlap"],
            )

            if not chunks:
                raise ValueError("No chunks produced from document")

            # 3. Store in ChromaDB
            collection_name = pipeline["config"]["vector_store"]["collection_name"]
            client = self._get_chroma_client(pipeline_id)

            # Get or create embedding function based on config
            embedding_config = pipeline["config"]["embedding"]
            embedding_fn = self._get_embedding_function(embedding_config)

            if embedding_fn:
                collection = client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=embedding_fn,
                )
            else:
                collection = client.get_or_create_collection(name=collection_name)

            # Add chunks to collection
            chunk_ids = [f"{pipeline_id}_{file_name}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "file_name": file_name,
                    "chunk_index": i,
                    "chunk_total": len(chunks),
                    "pipeline_id": pipeline_id,
                }
                for i in range(len(chunks))
            ]

            collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=chunk_ids,
            )

            # Update pipeline state
            pipeline["document_count"] = pipeline.get("document_count", 0) + 1
            pipeline["chunk_count"] = pipeline.get("chunk_count", 0) + len(chunks)
            pipeline["status"] = RAGPipelineStatus.READY
            pipeline["updated_at"] = datetime.utcnow()

            self.logger.info(
                f"Document ingested: {file_name} → {len(chunks)} chunks into pipeline {pipeline_id}"
            )

            return DocumentUploadResponse(
                pipeline_id=pipeline_id,
                file_name=file_name,
                file_size_bytes=len(file_content),
                chunks_created=len(chunks),
                status="success",
                message=f"Document '{file_name}' processed: {len(chunks)} chunks created",
            )

        except Exception as e:
            pipeline["status"] = RAGPipelineStatus.ERROR
            pipeline["updated_at"] = datetime.utcnow()
            self.logger.error(f"Document ingestion failed: {e}")
            raise

    async def query(
        self,
        pipeline_id: str,
        request: RAGQueryRequest,
    ) -> RAGQueryResponse:
        """Query a RAG pipeline for relevant document chunks."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        pipeline = self._pipelines[pipeline_id]

        if pipeline["status"] != RAGPipelineStatus.READY:
            raise ValueError(
                f"Pipeline is not ready for queries (status: {pipeline['status']})"
            )

        collection_name = pipeline["config"]["vector_store"]["collection_name"]
        retrieval_config = pipeline["config"]["retrieval"]

        top_k = request.top_k or retrieval_config["top_k"]

        client = self._get_chroma_client(pipeline_id)

        # Get embedding function
        embedding_config = pipeline["config"]["embedding"]
        embedding_fn = self._get_embedding_function(embedding_config)

        if embedding_fn:
            collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_fn,
            )
        else:
            collection = client.get_or_create_collection(name=collection_name)

        # Query ChromaDB
        results = collection.query(
            query_texts=[request.query],
            n_results=min(top_k, collection.count() or 1),
        )

        # Parse results
        retrieved_chunks = []
        if results and results.get("documents") and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
            distances = results["distances"][0] if results.get("distances") else [None] * len(documents)

            for doc, meta, dist in zip(documents, metadatas, distances):
                # ChromaDB uses L2 (Euclidean) distance by default.
                # Convert to a 0-1 similarity score: closer to 1 = more similar.
                score = 1.0 / (1.0 + dist) if dist is not None else None

                # Apply score threshold if configured
                threshold = retrieval_config.get("score_threshold")
                if threshold and score is not None and score < threshold:
                    continue

                retrieved_chunks.append(
                    RetrievedChunk(
                        content=doc,
                        metadata=meta or {},
                        score=score,
                    )
                )

        return RAGQueryResponse(
            query=request.query,
            results=retrieved_chunks,
            total_results=len(retrieved_chunks),
            pipeline_id=pipeline_id,
        )

    # ========================================================================
    # Private helpers
    # ========================================================================

    def _parse_document(self, file_name: str, content: bytes) -> str:
        """Parse text from uploaded document."""
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext == ".txt":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".csv":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".md":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".pdf":
            # Try to extract text from PDF
            try:
                import io
                # Use built-in basic PDF text extraction
                text = self._extract_pdf_text(content)
                if text.strip():
                    return text
            except Exception:
                pass
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".json":
            return content.decode("utf-8", errors="replace")

        else:
            # Fallback: try to decode as text
            return content.decode("utf-8", errors="replace")

    def _extract_pdf_text(self, content: bytes) -> str:
        """Basic PDF text extraction without external dependencies."""
        # Simple extraction: find text between BT and ET markers
        # This is a minimal approach — for production, use PyPDF2 or pdfplumber
        text_parts = []
        try:
            raw = content.decode("latin-1")
            # Find text objects in PDF
            import re
            # Extract text from PDF content streams
            for match in re.finditer(r'\(([^)]*)\)', raw):
                text = match.group(1)
                if len(text) > 2:
                    text_parts.append(text)
        except Exception:
            pass
        return " ".join(text_parts)

    def _chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
    ) -> List[str]:
        """Split text into chunks using the specified strategy."""
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, chunk_size, chunk_overlap)
        elif strategy == ChunkingStrategy.RECURSIVE:
            return self._chunk_recursive(text, chunk_size, chunk_overlap)
        elif strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(text, chunk_size, chunk_overlap)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, chunk_size, chunk_overlap)
        else:
            return self._chunk_recursive(text, chunk_size, chunk_overlap)

    def _chunk_fixed_size(self, text: str, size: int, overlap: int) -> List[str]:
        """Split text into fixed-size chunks with overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if overlap > 0 else end
            if start >= len(text):
                break
        return chunks

    def _chunk_recursive(self, text: str, size: int, overlap: int) -> List[str]:
        """
        Recursively split text using hierarchy of separators.
        Similar to LangChain's RecursiveCharacterTextSplitter.
        """
        separators = ["\n\n", "\n", ". ", " "]
        return self._recursive_split(text, separators, size, overlap)

    def _recursive_split(
        self, text: str, separators: List[str], size: int, overlap: int
    ) -> List[str]:
        """Recursive splitting implementation."""
        if len(text) <= size:
            return [text.strip()] if text.strip() else []

        # Try each separator
        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                chunks = []
                current_chunk = ""

                for part in parts:
                    candidate = (current_chunk + sep + part).strip() if current_chunk else part.strip()

                    if len(candidate) <= size:
                        current_chunk = candidate
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        # If part itself is too large, recurse with next separator
                        remaining_seps = separators[separators.index(sep) + 1:]
                        if remaining_seps and len(part) > size:
                            sub_chunks = self._recursive_split(
                                part, remaining_seps, size, overlap
                            )
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part.strip()

                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                return [c for c in chunks if c]

        # No separator found, fall back to fixed size
        return self._chunk_fixed_size(text, size, overlap)

    def _chunk_by_sentence(self, text: str, size: int, overlap: int) -> List[str]:
        """Split text by sentences, grouping into chunks."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= size:
                current_chunk = (current_chunk + " " + sentence).strip()
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_by_paragraph(self, text: str, size: int, overlap: int) -> List[str]:
        """Split text by paragraphs."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= size:
                current_chunk = (current_chunk + "\n\n" + para).strip()
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # If paragraph itself is too large, split by sentences
                if len(para) > size:
                    sub_chunks = self._chunk_by_sentence(para, size, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _get_embedding_function(self, embedding_config: Dict[str, Any]):
        """Get ChromaDB embedding function based on config."""
        provider = embedding_config.get("provider", "chroma_default")

        if provider == EmbeddingProvider.CHROMA_DEFAULT or provider == "chroma_default":
            # Use ChromaDB's built-in default embedding (all-MiniLM-L6-v2)
            return None  # ChromaDB uses default when None

        elif provider == EmbeddingProvider.OPENAI or provider == "openai":
            try:
                from chromadb.utils import embedding_functions

                # Get OpenAI API key from settings
                api_key = settings.OPENAI_API_KEY
                if not api_key:
                    self.logger.warning(
                        "OpenAI API key not configured, falling back to ChromaDB default embeddings"
                    )
                    return None

                model_name = embedding_config.get("model") if embedding_config.get("model") else "text-embedding-3-small"
                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=model_name,
                )
            except ImportError:
                self.logger.warning(
                    "chromadb embedding_functions not available, using default"
                )
                return None

        return None


# Global service instance (singleton)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
