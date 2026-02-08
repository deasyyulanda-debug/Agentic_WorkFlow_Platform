"""
RAG Pipeline Service - Enterprise-Grade Business Logic

Handles the complete RAG pipeline lifecycle:
1. Pipeline CRUD with SQLite persistence (survives restarts)
2. Document Upload → Parse text from files (PDF, TXT, MD, CSV, JSON, DOCX)
3. Chunking → Split text (fixed, recursive, sentence, paragraph, semantic)
4. Embedding → Generate vectors (ChromaDB default, OpenAI, Google, Sentence Transformers)
5. Storage → Store in ChromaDB vector database
6. Retrieval → Similarity search with metadata filtering
7. Reranking → LLM-based relevance reranking for quality
8. Answer Generation → Multi-provider LLM synthesis (Gemini, OpenAI, Anthropic)

Leverages AI-Research-SKILLs patterns:
- ChromaDB for local vector storage (SKILL: chroma)
- Sentence Transformers for free local embeddings (SKILL: sentence-transformers)
- Configurable chunking strategies (SKILL: langchain RAG guide)
- LLM-based reranking (SKILL: dspy reranking pattern)
- Metadata filtering (SKILL: chroma advanced usage)
"""
import os
import re
import json
import uuid
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from core import get_logger, settings
from db.database import AsyncSessionLocal
from db.models import RAGPipelineDB, RAGDocumentDB, RAGPipelineStatus as DBPipelineStatus

from .models import (
    RAGPipelineConfig,
    RAGPipelineResponse,
    RAGPipelineStatus,
    DocumentUploadResponse,
    DocumentInfo,
    RAGQueryRequest,
    RAGQueryResponse,
    RetrievedChunk,
    ChunkingStrategy,
    EmbeddingProvider,
    LLMProvider,
    MetadataFilter,
    MetadataFilterOperator,
    PipelineStatistics,
)


# Module-level session factory (overridable for testing)
_session_factory = None


def get_session_factory():
    """Get the current session factory. Uses AsyncSessionLocal by default."""
    global _session_factory
    return _session_factory or AsyncSessionLocal


def set_session_factory(factory):
    """Override session factory (for testing)."""
    global _session_factory
    _session_factory = factory


class RAGService:
    """
    Enterprise-grade RAG Pipeline Service.

    Responsibilities:
    - Pipeline CRUD with DB persistence
    - Multi-format document ingestion and intelligent chunking
    - Multi-provider embedding generation
    - Vector store management (ChromaDB)
    - Similarity search with metadata filtering
    - LLM-based reranking for quality retrieval
    - Answer synthesis with multi-provider fallback
    - Document management (list, delete per pipeline)
    - Pipeline statistics and observability
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._chroma_clients: Dict[str, Any] = {}

        # ChromaDB storage path
        self._chroma_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "chroma"
        )
        os.makedirs(self._chroma_path, exist_ok=True)

    # ========================================================================
    # Database helpers
    # ========================================================================

    async def _get_session(self) -> AsyncSession:
        """Get a new async database session."""
        return get_session_factory()()

    def _pipeline_to_response(self, db_pipeline: RAGPipelineDB) -> RAGPipelineResponse:
        """Convert DB model to response model."""
        llm_config = getattr(db_pipeline, 'llm_config', None) or {"provider": "gemini", "model": "gemini-2.5-flash"}
        return RAGPipelineResponse(
            id=db_pipeline.id,
            name=db_pipeline.name,
            description=db_pipeline.description,
            status=RAGPipelineStatus(db_pipeline.status.value),
            config={
                "chunking": db_pipeline.chunking_config,
                "embedding": db_pipeline.embedding_config,
                "vector_store": db_pipeline.vector_store_config,
                "retrieval": db_pipeline.retrieval_config,
                "llm": llm_config,
            },
            document_count=db_pipeline.document_count,
            chunk_count=db_pipeline.chunk_count,
            total_queries=db_pipeline.total_queries,
            last_query_at=db_pipeline.last_query_at,
            created_at=db_pipeline.created_at,
            updated_at=db_pipeline.updated_at,
        )

    # ========================================================================
    # ChromaDB management
    # ========================================================================

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

    # ========================================================================
    # Pipeline CRUD (DB-persisted)
    # ========================================================================

    async def create_pipeline(self, config: RAGPipelineConfig) -> RAGPipelineResponse:
        """Create a new RAG pipeline with the given configuration. Persisted to SQLite."""
        pipeline_id = str(uuid.uuid4())
        collection_name = config.vector_store.collection_name or f"pipeline_{pipeline_id[:8]}"

        # Initialize ChromaDB collection with cosine distance (all RAG skills use cosine)
        client = self._get_chroma_client(pipeline_id)
        client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Persist to database
        async with await self._get_session() as session:
            db_pipeline = RAGPipelineDB(
                id=pipeline_id,
                name=config.name,
                description=config.description,
                status=DBPipelineStatus.CREATED,
                chunking_config=config.chunking.model_dump(),
                embedding_config=config.embedding.model_dump(),
                vector_store_config={
                    **config.vector_store.model_dump(),
                    "collection_name": collection_name,
                },
                retrieval_config=config.retrieval.model_dump(),
                llm_config=config.llm.model_dump(),
                document_count=0,
                chunk_count=0,
                total_queries=0,
            )
            session.add(db_pipeline)
            await session.commit()
            await session.refresh(db_pipeline)

            self.logger.info(f"RAG pipeline created: {pipeline_id} ({config.name})")
            return self._pipeline_to_response(db_pipeline)

    async def get_pipeline(self, pipeline_id: str) -> RAGPipelineResponse:
        """Get pipeline by ID from database."""
        async with await self._get_session() as session:
            result = await session.execute(
                select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
            )
            db_pipeline = result.scalar_one_or_none()
            if not db_pipeline:
                raise ValueError(f"Pipeline not found: {pipeline_id}")
            return self._pipeline_to_response(db_pipeline)

    async def list_pipelines(self) -> List[RAGPipelineResponse]:
        """List all pipelines from database."""
        async with await self._get_session() as session:
            result = await session.execute(
                select(RAGPipelineDB).order_by(RAGPipelineDB.created_at.desc())
            )
            pipelines = result.scalars().all()
            return [self._pipeline_to_response(p) for p in pipelines]

    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline and its data from DB and ChromaDB."""
        async with await self._get_session() as session:
            result = await session.execute(
                select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
            )
            db_pipeline = result.scalar_one_or_none()
            if not db_pipeline:
                raise ValueError(f"Pipeline not found: {pipeline_id}")

            await session.delete(db_pipeline)
            await session.commit()

        # Clean up ChromaDB client
        if pipeline_id in self._chroma_clients:
            del self._chroma_clients[pipeline_id]

        # Clean up ChromaDB files
        import shutil
        persist_dir = os.path.join(self._chroma_path, pipeline_id)
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir, ignore_errors=True)

        self.logger.info(f"RAG pipeline deleted: {pipeline_id}")
        return True

    # ========================================================================
    # Document Management
    # ========================================================================

    async def list_documents(self, pipeline_id: str) -> List[DocumentInfo]:
        """List all documents in a pipeline."""
        async with await self._get_session() as session:
            # Verify pipeline exists
            pipeline_result = await session.execute(
                select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
            )
            if not pipeline_result.scalar_one_or_none():
                raise ValueError(f"Pipeline not found: {pipeline_id}")

            result = await session.execute(
                select(RAGDocumentDB)
                .where(RAGDocumentDB.pipeline_id == pipeline_id)
                .order_by(RAGDocumentDB.created_at.desc())
            )
            docs = result.scalars().all()
            return [
                DocumentInfo(
                    id=doc.id,
                    pipeline_id=doc.pipeline_id,
                    file_name=doc.file_name,
                    file_size_bytes=doc.file_size_bytes,
                    file_type=doc.file_type,
                    chunk_count=doc.chunk_count,
                    character_count=doc.character_count,
                    word_count=doc.word_count,
                    status=doc.status,
                    error_message=doc.error_message,
                    processing_time_ms=doc.processing_time_ms,
                    created_at=doc.created_at,
                )
                for doc in docs
            ]

    async def delete_document(self, pipeline_id: str, document_id: str) -> bool:
        """Delete a specific document from a pipeline and its chunks from ChromaDB."""
        async with await self._get_session() as session:
            result = await session.execute(
                select(RAGDocumentDB).where(
                    RAGDocumentDB.id == document_id,
                    RAGDocumentDB.pipeline_id == pipeline_id,
                )
            )
            doc = result.scalar_one_or_none()
            if not doc:
                raise ValueError(f"Document not found: {document_id}")

            # Remove chunks from ChromaDB
            try:
                pipeline_result = await session.execute(
                    select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
                )
                db_pipeline = pipeline_result.scalar_one_or_none()
                if db_pipeline:
                    collection_name = db_pipeline.vector_store_config.get("collection_name")
                    if collection_name:
                        client = self._get_chroma_client(pipeline_id)
                        collection = client.get_or_create_collection(
                            name=collection_name,
                            metadata={"hnsw:space": "cosine"},
                        )
                        # Delete by metadata filter
                        collection.delete(
                            where={"file_name": doc.file_name}
                        )

                    # Update pipeline counts
                    db_pipeline.document_count = max(0, db_pipeline.document_count - 1)
                    db_pipeline.chunk_count = max(0, db_pipeline.chunk_count - doc.chunk_count)
                    if db_pipeline.document_count == 0:
                        db_pipeline.status = DBPipelineStatus.CREATED
                    db_pipeline.updated_at = datetime.utcnow()
            except Exception as e:
                self.logger.warning(f"Error cleaning ChromaDB chunks: {e}")

            await session.delete(doc)
            await session.commit()

            self.logger.info(f"Document deleted: {document_id} from pipeline {pipeline_id}")
            return True

    # ========================================================================
    # Pipeline Statistics
    # ========================================================================

    async def get_statistics(self, pipeline_id: str) -> PipelineStatistics:
        """Get detailed pipeline statistics."""
        async with await self._get_session() as session:
            result = await session.execute(
                select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
            )
            db_pipeline = result.scalar_one_or_none()
            if not db_pipeline:
                raise ValueError(f"Pipeline not found: {pipeline_id}")

            docs = await self.list_documents(pipeline_id)

            return PipelineStatistics(
                pipeline_id=db_pipeline.id,
                pipeline_name=db_pipeline.name,
                status=RAGPipelineStatus(db_pipeline.status.value),
                document_count=db_pipeline.document_count,
                chunk_count=db_pipeline.chunk_count,
                total_queries=db_pipeline.total_queries,
                last_query_at=db_pipeline.last_query_at,
                documents=docs,
                config={
                    "chunking": db_pipeline.chunking_config,
                    "embedding": db_pipeline.embedding_config,
                    "vector_store": db_pipeline.vector_store_config,
                    "retrieval": db_pipeline.retrieval_config,
                    "llm": getattr(db_pipeline, 'llm_config', None) or {"provider": "gemini", "model": "gemini-2.5-flash"},
                },
                embedding_provider=db_pipeline.embedding_config.get("provider", "chroma_default"),
                chunking_strategy=db_pipeline.chunking_config.get("strategy", "recursive"),
                chunk_size=db_pipeline.chunking_config.get("chunk_size", 1000),
                chunk_overlap=db_pipeline.chunking_config.get("chunk_overlap", 200),
                top_k=db_pipeline.retrieval_config.get("top_k", 5),
                reranking_enabled=db_pipeline.retrieval_config.get("reranking_enabled", False),
                created_at=db_pipeline.created_at,
                updated_at=db_pipeline.updated_at,
            )

    # ========================================================================
    # Document Ingestion
    # ========================================================================

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
        3. Generate embeddings and store in ChromaDB
        4. Track document in database
        """
        start_time = time.time()

        async with await self._get_session() as session:
            # Verify pipeline exists
            result = await session.execute(
                select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
            )
            db_pipeline = result.scalar_one_or_none()
            if not db_pipeline:
                raise ValueError(f"Pipeline not found: {pipeline_id}")

            db_pipeline.status = DBPipelineStatus.INGESTING
            db_pipeline.updated_at = datetime.utcnow()
            await session.commit()

            document_id = str(uuid.uuid4())
            file_ext = os.path.splitext(file_name)[1].lower()

            try:
                # 1. Parse text from file
                text = self._parse_document(file_name, file_content)

                if not text.strip():
                    raise ValueError("Document contains no extractable text")

                char_count = len(text)
                word_count = len(text.split())

                # 2. Chunk the text
                chunking_config = db_pipeline.chunking_config
                chunks = self._chunk_text(
                    text,
                    strategy=ChunkingStrategy(chunking_config["strategy"]),
                    chunk_size=chunking_config["chunk_size"],
                    chunk_overlap=chunking_config["chunk_overlap"],
                )

                if not chunks:
                    raise ValueError("No chunks produced from document")

                # 3. Store in ChromaDB
                collection_name = db_pipeline.vector_store_config["collection_name"]
                client = self._get_chroma_client(pipeline_id)

                embedding_config = db_pipeline.embedding_config
                embedding_fn = self._get_embedding_function(embedding_config)

                if embedding_fn:
                    collection = client.get_or_create_collection(
                        name=collection_name,
                        embedding_function=embedding_fn,
                        metadata={"hnsw:space": "cosine"},
                    )
                else:
                    collection = client.get_or_create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"},
                    )

                # Add chunks with rich metadata
                chunk_ids = [f"{pipeline_id}_{document_id}_{i}" for i in range(len(chunks))]
                metadatas = [
                    {
                        "file_name": file_name,
                        "document_id": document_id,
                        "chunk_index": i,
                        "chunk_total": len(chunks),
                        "pipeline_id": pipeline_id,
                        "file_type": file_ext,
                        "ingested_at": datetime.utcnow().isoformat(),
                    }
                    for i in range(len(chunks))
                ]

                collection.add(
                    documents=chunks,
                    metadatas=metadatas,
                    ids=chunk_ids,
                )

                processing_time_ms = int((time.time() - start_time) * 1000)

                # 4. Track document in database
                db_doc = RAGDocumentDB(
                    id=document_id,
                    pipeline_id=pipeline_id,
                    file_name=file_name,
                    file_size_bytes=len(file_content),
                    file_type=file_ext,
                    chunk_count=len(chunks),
                    status="processed",
                    processing_time_ms=processing_time_ms,
                    character_count=char_count,
                    word_count=word_count,
                )
                session.add(db_doc)

                # Update pipeline stats
                db_pipeline.document_count = db_pipeline.document_count + 1
                db_pipeline.chunk_count = db_pipeline.chunk_count + len(chunks)
                db_pipeline.status = DBPipelineStatus.READY
                db_pipeline.updated_at = datetime.utcnow()
                await session.commit()

                self.logger.info(
                    f"Document ingested: {file_name} → {len(chunks)} chunks into pipeline {pipeline_id} "
                    f"({processing_time_ms}ms)"
                )

                return DocumentUploadResponse(
                    pipeline_id=pipeline_id,
                    document_id=document_id,
                    file_name=file_name,
                    file_size_bytes=len(file_content),
                    chunks_created=len(chunks),
                    processing_time_ms=processing_time_ms,
                    character_count=char_count,
                    word_count=word_count,
                    status="success",
                    message=f"Document '{file_name}' processed: {len(chunks)} chunks created in {processing_time_ms}ms",
                )

            except Exception as e:
                # Track failed document
                db_doc = RAGDocumentDB(
                    id=document_id,
                    pipeline_id=pipeline_id,
                    file_name=file_name,
                    file_size_bytes=len(file_content),
                    file_type=file_ext,
                    chunk_count=0,
                    status="error",
                    error_message=str(e),
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )
                session.add(db_doc)
                db_pipeline.status = DBPipelineStatus.ERROR
                db_pipeline.updated_at = datetime.utcnow()
                await session.commit()

                self.logger.error(f"Document ingestion failed: {e}")
                raise

    # ========================================================================
    # Query & Retrieval
    # ========================================================================

    async def query(
        self,
        pipeline_id: str,
        request: RAGQueryRequest,
    ) -> RAGQueryResponse:
        """Query a RAG pipeline with metadata filtering and optional reranking."""
        query_start = time.time()

        async with await self._get_session() as session:
            result = await session.execute(
                select(RAGPipelineDB).where(RAGPipelineDB.id == pipeline_id)
            )
            db_pipeline = result.scalar_one_or_none()
            if not db_pipeline:
                raise ValueError(f"Pipeline not found: {pipeline_id}")

            if db_pipeline.status.value != RAGPipelineStatus.READY:
                raise ValueError(
                    f"Pipeline is not ready for queries (status: {db_pipeline.status.value})"
                )

            retrieval_config = db_pipeline.retrieval_config
            llm_config = getattr(db_pipeline, 'llm_config', None) or {"provider": "gemini", "model": "gemini-2.5-flash"}
            top_k = request.top_k or retrieval_config["top_k"]

            collection_name = db_pipeline.vector_store_config["collection_name"]
            client = self._get_chroma_client(pipeline_id)

            embedding_config = db_pipeline.embedding_config
            embedding_fn = self._get_embedding_function(embedding_config)

            if embedding_fn:
                collection = client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=embedding_fn,
                    metadata={"hnsw:space": "cosine"},
                )
            else:
                collection = client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )

            # Build ChromaDB where clause from metadata filters
            where_clause = self._build_where_clause(request.metadata_filters)

            # Determine how many results to fetch (more if reranking)
            reranking_enabled = request.reranking_enabled if request.reranking_enabled is not None \
                else retrieval_config.get("reranking_enabled", False)
            # Fetch slightly more for reranking, but cap at 10 to keep CPU inference fast
            fetch_k = min(top_k + 5, 15) if reranking_enabled else top_k

            # Query ChromaDB
            query_kwargs = {
                "query_texts": [request.query],
                "n_results": min(fetch_k, collection.count() or 1),
            }
            if where_clause:
                query_kwargs["where"] = where_clause

            results = collection.query(**query_kwargs)

            # Parse results
            retrieved_chunks = []
            if results and results.get("documents") and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
                distances = results["distances"][0] if results.get("distances") else [None] * len(documents)

                for doc, meta, dist in zip(documents, metadatas, distances):
                    # Cosine distance: 0 = identical, 2 = opposite. Similarity = 1 - distance.
                    score = max(0.0, 1.0 - dist) if dist is not None else None

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

            # Apply reranking if enabled (Qwen3-Reranker or LLM-based)
            reranking_applied = False
            if reranking_enabled and len(retrieved_chunks) > 0:
                reranking_top_k = retrieval_config.get("reranking_top_k", 5)
                reranker_model = retrieval_config.get("reranker_model", "qwen3")
                # Cap input to reranker at 10 chunks to keep CPU inference under 3 min
                chunks_for_reranking = retrieved_chunks[:10]
                reranked = await self._rerank_chunks(
                    request.query, chunks_for_reranking, reranking_top_k,
                    reranker_model=reranker_model, llm_config=llm_config,
                )
                if reranked is not None:
                    retrieved_chunks = reranked
                    reranking_applied = True

            # Trim to final top_k
            retrieved_chunks = retrieved_chunks[:top_k]

            # Update query stats
            db_pipeline.total_queries = db_pipeline.total_queries + 1
            db_pipeline.last_query_at = datetime.utcnow()
            db_pipeline.updated_at = datetime.utcnow()
            await session.commit()

            query_time_ms = int((time.time() - query_start) * 1000)

            return RAGQueryResponse(
                query=request.query,
                answer=await self._generate_answer(request.query, retrieved_chunks, llm_config)
                if request.generate_answer and retrieved_chunks
                else None,
                results=retrieved_chunks,
                total_results=len(retrieved_chunks),
                pipeline_id=pipeline_id,
                reranking_applied=reranking_applied,
                query_time_ms=query_time_ms,
            )

    # ========================================================================
    # Metadata Filtering
    # ========================================================================

    def _build_where_clause(self, filters: Optional[List[MetadataFilter]]) -> Optional[Dict]:
        """Build ChromaDB where clause from metadata filters."""
        if not filters:
            return None

        operator_map = {
            MetadataFilterOperator.EQUALS: "$eq",
            MetadataFilterOperator.NOT_EQUALS: "$ne",
            MetadataFilterOperator.GREATER_THAN: "$gt",
            MetadataFilterOperator.GREATER_THAN_EQUAL: "$gte",
            MetadataFilterOperator.LESS_THAN: "$lt",
            MetadataFilterOperator.LESS_THAN_EQUAL: "$lte",
            MetadataFilterOperator.IN: "$in",
            MetadataFilterOperator.NOT_IN: "$nin",
        }

        if len(filters) == 1:
            f = filters[0]
            op = operator_map.get(f.operator, "$eq")
            if op == "$eq":
                return {f.field: f.value}
            return {f.field: {op: f.value}}

        # Multiple filters → $and
        conditions = []
        for f in filters:
            op = operator_map.get(f.operator, "$eq")
            if op == "$eq":
                conditions.append({f.field: f.value})
            else:
                conditions.append({f.field: {op: f.value}})

        return {"$and": conditions}

    # ========================================================================
    # Reranking (Qwen3-Reranker-0.6B + LLM fallback)
    # ========================================================================

    _qwen3_reranker = None  # Class-level cache for Qwen3-Reranker model
    _qwen3_tokenizer = None

    def _load_qwen3_reranker(self):
        """Load Qwen3-Reranker-0.6B model (cached at class level)."""
        if RAGService._qwen3_reranker is not None:
            return RAGService._qwen3_reranker, RAGService._qwen3_tokenizer

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM

            self.logger.info("Loading Qwen3-Reranker-0.6B model (first time, ~1.2GB download)...")
            tokenizer = AutoTokenizer.from_pretrained(
                "Qwen/Qwen3-Reranker-0.6B", padding_side='left'
            )
            model = AutoModelForCausalLM.from_pretrained(
                "Qwen/Qwen3-Reranker-0.6B"
            ).eval()

            RAGService._qwen3_reranker = model
            RAGService._qwen3_tokenizer = tokenizer
            self.logger.info("Qwen3-Reranker-0.6B loaded successfully")
            return model, tokenizer
        except Exception as e:
            self.logger.warning(f"Failed to load Qwen3-Reranker-0.6B: {e}")
            return None, None

    def _qwen3_rerank_score(self, query: str, documents: List[str]) -> Optional[List[float]]:
        """Score query-document pairs using Qwen3-Reranker-0.6B.
        Based on official HuggingFace usage pattern.
        """
        import time
        t0 = time.time()
        model, tokenizer = self._load_qwen3_reranker()
        if model is None or tokenizer is None:
            return None

        try:
            import torch

            token_false_id = tokenizer.convert_tokens_to_ids("no")
            token_true_id = tokenizer.convert_tokens_to_ids("yes")
            max_length = 8192

            prefix = (
                "<|im_start|>system\n"
                'Judge whether the Document meets the requirements based on the Query and the '
                'Instruct provided. Note that the answer can only be "yes" or "no".'
                "<|im_end|>\n<|im_start|>user\n"
            )
            suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
            suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)

            instruction = (
                "Given a query, retrieve relevant passages that answer the query"
            )

            # Format inputs
            pairs = []
            for doc in documents:
                text = (
                    f"<Instruct>: {instruction}\n"
                    f"<Query>: {query}\n"
                    f"<Document>: {doc}"
                )
                pairs.append(text)

            self.logger.info(f"Qwen3-Reranker: scoring {len(documents)} documents (avg {sum(len(d) for d in documents)//max(len(documents),1)} chars each)")

            # Tokenize
            inputs = tokenizer(
                pairs, padding=False, truncation='longest_first',
                return_attention_mask=False,
                max_length=max_length - len(prefix_tokens) - len(suffix_tokens),
            )
            for i, ele in enumerate(inputs['input_ids']):
                inputs['input_ids'][i] = prefix_tokens + ele + suffix_tokens
            inputs = tokenizer.pad(
                inputs, padding=True, return_tensors="pt",
            )
            for key in inputs:
                inputs[key] = inputs[key].to(model.device)

            # Compute scores
            with torch.no_grad():
                batch_scores = model(**inputs).logits[:, -1, :]
                true_vector = batch_scores[:, token_true_id]
                false_vector = batch_scores[:, token_false_id]
                batch_scores = torch.stack([false_vector, true_vector], dim=1)
                batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
                scores = batch_scores[:, 1].exp().tolist()

            elapsed = time.time() - t0
            self.logger.info(f"Qwen3-Reranker: completed in {elapsed:.1f}s, scores: {[f'{s:.3f}' for s in scores]}")

            return scores

        except Exception as e:
            self.logger.warning(f"Qwen3-Reranker scoring failed: {e}")
            return None

    async def _rerank_chunks(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int,
        reranker_model: str = "qwen3",
        llm_config: Dict[str, str] = None,
    ) -> Optional[List[RetrievedChunk]]:
        """
        Rerank retrieved chunks for better relevance.
        Supports:
        - 'qwen3': Qwen3-Reranker-0.6B (local model, free, fast, high quality)
        - 'llm': LLM-based reranking via configured provider (uses API calls)
        """
        if not chunks:
            return chunks

        if reranker_model == "qwen3":
            # Use Qwen3-Reranker-0.6B (local, no API cost)
            documents = [chunk.content[:500] for chunk in chunks]  # Truncate for CPU efficiency
            scores = self._qwen3_rerank_score(query, documents)

            if scores is not None and len(scores) == len(chunks):
                for chunk, score in zip(chunks, scores):
                    chunk.rerank_score = float(score)
                re_ranked = sorted(chunks, key=lambda c: c.rerank_score or 0, reverse=True)
                return re_ranked[:top_k]
            else:
                self.logger.warning("Qwen3-Reranker failed, falling back to LLM reranking")
                # Fall through to LLM reranking

        # LLM-based reranking fallback
        return await self._rerank_chunks_llm(query, chunks, top_k, llm_config)

    async def _rerank_chunks_llm(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int,
        llm_config: Dict[str, str] = None,
    ) -> Optional[List[RetrievedChunk]]:
        """
        LLM-based reranking fallback.
        Pattern from AI-Research-SKILLs (DSPy reranking pattern).
        Uses the pipeline's configured LLM provider/model.
        """
        if not chunks:
            return chunks

        # Build reranking prompt
        chunk_descriptions = []
        for i, chunk in enumerate(chunks):
            preview = chunk.content[:300].replace("\n", " ")
            chunk_descriptions.append(f"[Chunk {i}]: {preview}")

        chunks_text = "\n".join(chunk_descriptions)

        rerank_prompt = (
            f"You are a relevance scoring assistant. Given a query and document chunks, "
            f"score each chunk's relevance to the query on a scale of 0.0 to 1.0.\n\n"
            f"Query: {query}\n\n"
            f"Chunks:\n{chunks_text}\n\n"
            f"Return ONLY a JSON array of scores in order, e.g. [0.9, 0.3, 0.7, ...]\n"
            f"No explanation, just the JSON array."
        )

        # Use pipeline's configured LLM
        scores_text = await self._call_llm(
            "You are a scoring assistant. Return only valid JSON.",
            rerank_prompt,
            llm_config,
        )
        if not scores_text:
            return None  # Skip reranking if no LLM available

        # Parse scores
        try:
            # Extract JSON array from response
            scores_text = scores_text.strip()
            if scores_text.startswith("```"):
                scores_text = scores_text.split("```")[1]
                if scores_text.startswith("json"):
                    scores_text = scores_text[4:]
            scores = json.loads(scores_text.strip())

            if not isinstance(scores, list) or len(scores) != len(chunks):
                self.logger.warning(f"Reranking returned {len(scores)} scores for {len(chunks)} chunks")
                return None

            # Assign rerank scores and sort
            for chunk, score in zip(chunks, scores):
                chunk.rerank_score = float(score)

            re_ranked = sorted(chunks, key=lambda c: c.rerank_score or 0, reverse=True)
            return re_ranked[:top_k]

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse reranking scores: {e}")
            return None

    # ========================================================================
    # Answer Generation (Multi-Provider)
    # ========================================================================

    async def _generate_answer(
        self, query: str, chunks: List[RetrievedChunk], llm_config: Dict[str, str] = None
    ) -> Optional[str]:
        """
        Generate a synthesized answer using the pipeline's configured LLM
        based on the retrieved context chunks.
        """
        context_parts = []
        for i, chunk in enumerate(chunks):
            source = chunk.metadata.get("file_name", "Unknown")
            score_info = ""
            if chunk.rerank_score is not None:
                score_info = f", Relevance: {chunk.rerank_score:.2f}"
            elif chunk.score is not None:
                score_info = f", Score: {chunk.score:.3f}"
            context_parts.append(
                f"[Source: {source}, Chunk {i + 1}{score_info}]\n{chunk.content}"
            )
        context = "\n\n---\n\n".join(context_parts)

        system_prompt = (
            "You are a precise research assistant that answers questions based ONLY on the "
            "provided context. Follow these rules:\n"
            "1. Answer the user's question using ONLY information from the context below.\n"
            "2. If the context doesn't contain enough information, say so clearly.\n"
            "3. Be concise and well-structured. Always format your response using proper Markdown:\n"
            "   - Use **bold** for key terms and headings.\n"
            "   - Use bullet points with `- ` or `* ` prefix for lists.\n"
            "   - Use numbered lists (`1. `) for sequential steps.\n"
            "   - Use headings (`##`, `###`) to organize longer answers.\n"
            "4. Cite which source/chunk your information comes from when relevant.\n"
            "5. Do NOT make up information that is not in the context.\n"
        )

        user_prompt = (
            f"Context from documents:\n\n{context}\n\n"
            f"---\n\n"
            f"Question: {query}\n\n"
            f"Please provide a clear, well-structured answer based on the context above."
        )

        # Use pipeline's configured LLM provider/model
        answer = await self._call_llm(system_prompt, user_prompt, llm_config)
        if answer:
            return answer

        self.logger.warning("LLM call failed for answer generation")
        return None

    # ========================================================================
    # LLM Dispatcher (Multi-Provider)
    # ========================================================================

    async def _call_llm(
        self, system_prompt: str, user_prompt: str, llm_config: Dict[str, str] = None
    ) -> Optional[str]:
        """
        Unified LLM dispatcher. Routes to the correct provider based on llm_config.
        Falls back through providers if the configured one fails.
        """
        if not llm_config:
            llm_config = {"provider": "gemini", "model": "gemini-2.5-flash"}

        provider = llm_config.get("provider", "gemini")
        model_name = llm_config.get("model", "gemini-2.5-flash")

        # Map provider to call method
        provider_calls = {
            "gemini": lambda: self._call_gemini(system_prompt, user_prompt, model_name),
            "groq": lambda: self._call_groq(system_prompt, user_prompt, model_name),
            "openrouter": lambda: self._call_openrouter(system_prompt, user_prompt, model_name),
            "openai": lambda: self._call_openai(system_prompt, user_prompt, model_name),
            "anthropic": lambda: self._call_anthropic(system_prompt, user_prompt, model_name),
            "deepseek": lambda: self._call_deepseek(system_prompt, user_prompt, model_name),
        }

        # Try configured provider first
        call_fn = provider_calls.get(provider)
        if call_fn:
            result = await call_fn()
            if result:
                return result
            self.logger.warning(f"Primary LLM provider '{provider}' failed, trying fallbacks")

        # Fallback chain: try other providers that have API keys
        fallback_order = ["gemini", "groq", "openrouter", "openai", "anthropic", "deepseek"]
        for fb_provider in fallback_order:
            if fb_provider == provider:
                continue
            fb_fn = provider_calls.get(fb_provider)
            if fb_fn:
                result = await fb_fn()
                if result:
                    self.logger.info(f"Fallback to '{fb_provider}' succeeded")
                    return result

        return None

    async def _call_gemini(self, system_prompt: str, user_prompt: str, model_name: str = "gemini-2.5-flash") -> Optional[str]:
        """Call Google Gemini API."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_prompt,
            )
            response = model.generate_content(user_prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            self.logger.warning(f"Gemini ({model_name}) failed: {e}")
        return None

    async def _call_groq(self, system_prompt: str, user_prompt: str, model_name: str = "llama-3.3-70b-versatile") -> Optional[str]:
        """Call Groq API (OpenAI-compatible)."""
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            if response.choices:
                return response.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"Groq ({model_name}) failed: {e}")
        return None

    async def _call_openrouter(self, system_prompt: str, user_prompt: str, model_name: str = "anthropic/claude-sonnet-4.5") -> Optional[str]:
        """Call OpenRouter API (OpenAI-compatible, access to many models)."""
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            if response.choices:
                return response.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"OpenRouter ({model_name}) failed: {e}")
        return None

    async def _call_openai(self, system_prompt: str, user_prompt: str, model_name: str = "gpt-5.2-2025-12-11") -> Optional[str]:
        """Call OpenAI API directly."""
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            if response.choices:
                return response.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"OpenAI ({model_name}) failed: {e}")
        return None

    async def _call_anthropic(self, system_prompt: str, user_prompt: str, model_name: str = "claude-sonnet-4-20250514") -> Optional[str]:
        """Call Anthropic API."""
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return None
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if response.content:
                return response.content[0].text
        except Exception as e:
            self.logger.warning(f"Anthropic ({model_name}) failed: {e}")
        return None

    async def _call_deepseek(self, system_prompt: str, user_prompt: str, model_name: str = "deepseek-chat") -> Optional[str]:
        """Call DeepSeek API (OpenAI-compatible)."""
        api_key = settings.DEEPSEEK_API_KEY
        if not api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            if response.choices:
                return response.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"DeepSeek ({model_name}) failed: {e}")
        return None

    # ========================================================================
    # Document Parsing
    # ========================================================================

    def _parse_document(self, file_name: str, content: bytes) -> str:
        """Parse text from uploaded document. Supports: TXT, CSV, MD, PDF, JSON, DOCX."""
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext == ".txt":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".csv":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".md":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".pdf":
            text = self._extract_pdf_text(content)
            if text.strip():
                return text
            raise ValueError(
                "Could not extract readable text from the PDF. "
                "The file may be image-based (scanned). "
                "Please use a text-based PDF or OCR the document first."
            )

        elif file_ext == ".json":
            return content.decode("utf-8", errors="replace")

        elif file_ext == ".docx":
            return self._extract_docx_text(content)

        elif file_ext in (".html", ".htm"):
            return self._extract_html_text(content)

        else:
            # Fallback: try to decode as text
            return content.decode("utf-8", errors="replace")

    def _extract_pdf_text(self, content: bytes) -> str:
        """
        Extract clean text from a PDF.
        Uses PyPDF2 (primary) with pdfplumber as fallback.
        """
        import io
        text = ""

        # Strategy 1: PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
        except Exception as e:
            self.logger.warning(f"PyPDF2 extraction failed: {e}")

        # Strategy 2: Fallback to pdfplumber
        if not text.strip():
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    pages_text = []
                    for page in pdf.pages:
                        page_text = page.extract_text(
                            x_tolerance=3,
                            y_tolerance=3,
                        )
                        if page_text:
                            page_text = self._fix_word_spacing(page_text)
                            pages_text.append(page_text)
                    text = "\n\n".join(pages_text)
            except Exception as e:
                self.logger.warning(f"pdfplumber extraction failed: {e}")

        text = self._clean_extracted_text(text)
        return text

    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX files using python-docx."""
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            raise ValueError(
                "python-docx is required for DOCX files. Install: pip install python-docx"
            )
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")

    def _extract_html_text(self, content: bytes) -> str:
        """Extract text from HTML files by stripping tags."""
        text = content.decode("utf-8", errors="replace")
        # Strip HTML tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _fix_word_spacing(self, text: str) -> str:
        """Fix concatenated words from poor PDF extraction."""
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
        return text

    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text by removing binary noise and artifacts."""
        if not text:
            return ""

        text = re.sub(r'[^\x20-\x7E\n\t\r]', ' ', text)

        pdf_noise_patterns = [
            r'endstream', r'endobj', r'\d+\s+\d+\s+obj',
            r'<<[^>]*>>', r'/\w+\s*\[?[^\]]*\]?', r'stream\s*$',
            r'xref', r'trailer', r'startxref', r'%%EOF',
            r'\\[()]', r'tex2pdf:\w+', r'Doc-Start',
            r'cite\.\d+@\w+', r'section\.\d+', r'subsection\.\d+\.\d+',
            r'subsubsection\.\d+\.\d+\.\d+', r'page\.\d+',
            r'Item\.\d+', r'figure\.\d+',
        ]
        for pattern in pdf_noise_patterns:
            text = re.sub(pattern, ' ', text, flags=re.MULTILINE)

        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        clean_lines = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                clean_lines.append('')
                continue
            alpha_count = sum(1 for c in line if c.isalpha())
            if len(line) > 0 and alpha_count / len(line) > 0.3:
                clean_lines.append(line)
            elif len(line) < 80 and alpha_count > 3:
                clean_lines.append(line)

        text = '\n'.join(clean_lines)
        return text.strip()

    # ========================================================================
    # Chunking Strategies
    # ========================================================================

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
        elif strategy == ChunkingStrategy.SEMANTIC:
            return self._chunk_semantic(text, chunk_size, chunk_overlap)
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
        Pattern from AI-Research-SKILLs LangChain RecursiveCharacterTextSplitter.
        """
        separators = ["\n\n", "\n", ". ", " "]
        return self._recursive_split(text, separators, size, overlap)

    def _recursive_split(
        self, text: str, separators: List[str], size: int, overlap: int
    ) -> List[str]:
        """Recursive splitting implementation."""
        if len(text) <= size:
            return [text.strip()] if text.strip() else []

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

        return self._chunk_fixed_size(text, size, overlap)

    def _chunk_by_sentence(self, text: str, size: int, overlap: int) -> List[str]:
        """Split text by sentences, grouping into chunks."""
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
                if len(para) > size:
                    sub_chunks = self._chunk_by_sentence(para, size, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_semantic(self, text: str, size: int, overlap: int) -> List[str]:
        """
        Semantic chunking: split by meaning boundaries.
        Groups sentences by semantic similarity using embeddings.
        Falls back to recursive if sentence-transformers not available.
        """
        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return self._chunk_recursive(text, size, overlap)

        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np

            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(sentences)

            # Calculate cosine similarity between consecutive sentences
            similarities = []
            for i in range(len(embeddings) - 1):
                a = embeddings[i]
                b = embeddings[i + 1]
                cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                similarities.append(cos_sim)

            # Find breakpoints where similarity drops significantly
            if similarities:
                mean_sim = np.mean(similarities)
                std_sim = np.std(similarities)
                threshold = mean_sim - std_sim  # Break at below-average similarity

                chunks = []
                current_chunk = sentences[0]

                for i in range(len(similarities)):
                    next_sentence = sentences[i + 1]
                    candidate = current_chunk + " " + next_sentence

                    # Break if similarity is low OR chunk is too large
                    if (similarities[i] < threshold and len(current_chunk) >= size * 0.3) or \
                       len(candidate) > size:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = next_sentence
                    else:
                        current_chunk = candidate

                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                return [c for c in chunks if c]

        except ImportError:
            self.logger.info("sentence-transformers not available, falling back to recursive chunking")

        return self._chunk_recursive(text, size, overlap)

    # ========================================================================
    # Embedding Functions
    # ========================================================================

    def _get_embedding_function(self, embedding_config: Dict[str, Any]):
        """Get embedding function based on provider config.
        Supports: ChromaDB default, OpenAI, Google, Sentence Transformers, HuggingFace.
        """
        provider = embedding_config.get("provider", "chroma_default")
        model_name = embedding_config.get("model")

        if provider == EmbeddingProvider.CHROMA_DEFAULT or provider == "chroma_default":
            return None  # ChromaDB uses default (all-MiniLM-L6-v2)

        elif provider == "st_mpnet":
            return self._get_sentence_transformer_embeddings("all-mpnet-base-v2")

        elif provider == "st_roberta":
            return self._get_sentence_transformer_embeddings("all-roberta-large-v1")

        elif provider == "bge_small":
            return self._get_sentence_transformer_embeddings("BAAI/bge-small-en-v1.5")

        elif provider == "qwen3_embed":
            return self._get_sentence_transformer_embeddings("Qwen/Qwen3-Embedding-0.6B")

        elif provider == EmbeddingProvider.OPENAI or provider == "openai":
            return self._get_openai_embeddings(model_name)

        elif provider == EmbeddingProvider.GOOGLE or provider == "google":
            return self._get_google_embeddings(model_name)

        elif provider == EmbeddingProvider.SENTENCE_TRANSFORMERS or provider == "sentence_transformers":
            return self._get_sentence_transformer_embeddings(model_name)

        elif provider == EmbeddingProvider.HUGGINGFACE or provider == "huggingface":
            return self._get_huggingface_embeddings(model_name)

        return None

    def _get_openai_embeddings(self, model_name: Optional[str] = None):
        """Get OpenAI embedding function for ChromaDB."""
        try:
            from chromadb.utils import embedding_functions
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                self.logger.warning("OpenAI API key not configured, falling back to default")
                return None
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=model_name or "text-embedding-3-small",
            )
        except ImportError:
            self.logger.warning("chromadb embedding_functions not available")
            return None

    def _get_google_embeddings(self, model_name: Optional[str] = None):
        """Get Google embedding function for ChromaDB."""
        try:
            from chromadb.utils import embedding_functions
            api_key = settings.GOOGLE_API_KEY
            if not api_key:
                self.logger.warning("Google API key not configured, falling back to default")
                return None
            return embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                api_key=api_key,
                model_name=model_name or "models/embedding-001",
            )
        except (ImportError, AttributeError):
            # Fallback: custom Google embedding function
            return self._get_google_embeddings_custom(model_name)

    def _get_google_embeddings_custom(self, model_name: Optional[str] = None):
        """Custom Google embedding function if ChromaDB built-in not available."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return None
        try:
            import google.generativeai as genai
            from chromadb import Documents, EmbeddingFunction, Embeddings

            genai.configure(api_key=api_key)

            class GoogleEmbeddingFunction(EmbeddingFunction):
                def __call__(self, input: Documents) -> Embeddings:
                    result = genai.embed_content(
                        model=model_name or "models/embedding-001",
                        content=input,
                        task_type="retrieval_document",
                    )
                    return result["embedding"]

            return GoogleEmbeddingFunction()
        except Exception as e:
            self.logger.warning(f"Google custom embeddings failed: {e}")
            return None

    def _get_sentence_transformer_embeddings(self, model_name: Optional[str] = None):
        """
        Get Sentence Transformers embedding function.
        AI-Research-SKILLs: 5000+ models, multilingual, free/local.
        """
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_name or "all-mpnet-base-v2"
            )
        except ImportError:
            self.logger.warning("sentence-transformers not available")
            return None

    def _get_huggingface_embeddings(self, model_name: Optional[str] = None):
        """Get HuggingFace API embedding function."""
        try:
            from chromadb.utils import embedding_functions
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                self.logger.warning("HuggingFace API key not configured, falling back to default")
                return None
            return embedding_functions.HuggingFaceEmbeddingFunction(
                api_key=api_key,
                model_name=model_name or "sentence-transformers/all-MiniLM-L6-v2",
            )
        except ImportError:
            self.logger.warning("HuggingFace embedding function not available")
            return None


# ========================================================================
# Singleton
# ========================================================================

_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
