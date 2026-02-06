# Architecture Review & Product Roadmap

> **Review Date**: 2026-02-06
> **Role**: Principal Architect / Technical Critic
> **Status**: Critical Review — Honest Assessment

---

## Executive Summary

The Agentic Workflow Platform has a **solid foundation** — the FastAPI + Next.js stack is the right choice, the async architecture is well-designed, and the provider abstraction pattern is clean. However, there is a significant gap between the current MVP and the vision of replacing CLI/Codex/Claude with a UI for [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-research-SKILLs).

This document provides an honest, critical assessment and a phased roadmap to get from here to a shippable product.

---

## What's Working Well ✅

| Area | Assessment |
|------|-----------|
| **API Design** | Clean RESTful design, 31 endpoints, proper Pydantic validation |
| **Provider Abstraction** | Factory pattern with 6 providers — extensible and well-structured |
| **Async Architecture** | Proper use of async/await, aiosqlite, ASGI throughout |
| **Workflow Engine** | Sequential step execution with context passing works |
| **Docker Setup** | docker-compose.yml is production-ready for dev/staging |
| **Test Coverage** | 36 tests covering all API endpoints (now passing) |

---

## Critical Issues 🚨

### 1. Frontend Build Was Broken
**Fixed**: `next.config.js` rewrite used `process.env.NEXT_PUBLIC_API_URL` directly in template literal, which evaluates to `undefined` at build time when the env var isn't set.

**Root Cause**: Missing fallback in the `rewrites()` function (now fixed with local variable + default).

### 2. Test Suite Was Non-Functional
**Fixed**: `pytest-asyncio` was not in `requirements.txt`. All 36 tests were failing due to missing async test support.

**Root Cause**: Missing dev dependency — any new developer cloning this repo would see 36 failing tests, which severely impacts confidence and onboarding.

### 3. SQLite in Production
**Risk**: HIGH — SQLite does not support concurrent writes, connection pooling, or horizontal scaling. The claims of "production-ready" are premature with SQLite as the only database.

**Recommendation**: Add PostgreSQL support via `asyncpg`. SQLAlchemy already abstracts this — you just need to swap the connection string and add a migration tool (Alembic).

### 4. No Authentication
**Risk**: HIGH — `python-jose` and `passlib` are in requirements but no auth middleware exists. Any user can access any endpoint, modify any workflow, or delete any data.

**Recommendation**: Implement JWT auth before any deployment. The dependencies are already there — just needs the middleware and login endpoints.

### 5. No Database Migrations
**Risk**: MEDIUM — Using `Base.metadata.create_all()` in the app lifespan. This works for initial setup but will silently fail or break when you change models.

**Recommendation**: Add Alembic for schema migrations immediately.

### 6. No CI/CD Pipeline
**Risk**: MEDIUM — No GitHub Actions, no automated testing on PR. Tests existed but were broken, and nobody noticed.

**Recommendation**: Add a basic CI pipeline that runs tests on every push.

---

## Gap Analysis: Current State vs. AI-Research-SKILLs Vision

The [Orchestra-Research/AI-research-SKILLs](https://github.com/Orchestra-Research/AI-research-SKILLs) repo provides CLI-based AI research skills including:
- RAG pipeline construction
- Model fine-tuning orchestration
- ML research paper writing
- Multi-persona brainstorming
- Literature review automation

### What's Missing to Bridge the Gap

| Capability | Current State | Needed |
|-----------|--------------|--------|
| **RAG Pipeline Builder** | ❌ Not started | Drag-and-drop pipeline designer with steps: Ingest → Chunk → Embed → Index → Retrieve → Generate |
| **Model Fine-Tuning UI** | ❌ Not started | Dataset upload, hyperparameter config, training monitoring |
| **Research Paper Writer** | ❌ Not started | Multi-step workflow template with outline → sections → citations → review |
| **Multi-Persona Brainstorming** | 🟡 Partial (personas exist, no collaboration) | Multiple personas in a single workflow, cross-referencing outputs |
| **Document Upload/Ingestion** | ❌ Not started | File upload API, PDF/DOCX parsing, vector store integration |
| **Vector Store Integration** | ❌ Not started | FAISS, Pinecone, Weaviate, or ChromaDB support |
| **Workflow Templates Library** | ❌ Not started | Pre-built workflow templates users can select from dropdown |
| **Real-time Execution Streaming** | ❌ Not started | WebSocket support for live token streaming |

---

## Recommended Product Roadmap

### Phase 1: Foundation Hardening (Week 1-2)
> "You can't build a skyscraper on sand."

- [x] ~~Fix frontend build~~ ✅ Done
- [x] ~~Fix test suite~~ ✅ Done
- [x] Add GitHub Actions CI pipeline (pytest + next build on PR) ✅ Done
- [ ] Add Alembic database migrations
- [ ] Add PostgreSQL support (keep SQLite for dev)
- [ ] Implement JWT authentication (login/register/token refresh)
- [ ] Add rate limiting and input sanitization

### Phase 2: Workflow Templates & Enhanced UI (Week 3-4)
> "Make the common case easy."

- [ ] Create pre-built workflow templates:
  - RAG Pipeline (basic)
  - Research Paper Outline
  - Literature Review
  - Code Review
  - Brainstorming Session
- [ ] Build template selector dropdown in workflow creation UI
- [ ] Add visual workflow step designer (drag-and-drop or sequential wizard)
- [ ] Implement `branch` step type (conditional logic in workflows)
- [ ] Add workflow import/export (JSON)

### Phase 3: RAG Pipeline Integration (Week 5-7) — **IN PROGRESS** 🚧
> "This is the killer feature."

- [x] File upload API (PDF, TXT, CSV, MD, JSON — up to 10MB) ✅ Done
- [x] Document parsing service (text extraction from multiple file formats) ✅ Done
- [x] Text chunking strategies (fixed-size, recursive, sentence, paragraph) ✅ Done
- [x] Embedding generation (ChromaDB default + OpenAI embeddings) ✅ Done
- [x] Vector store integration (ChromaDB with persistent storage) ✅ Done
- [x] RAG retrieval step types in workflow engine (`rag_ingest`, `rag_retrieve`) ✅ Done
- [x] RAG pipeline configuration UI (pipeline builder page at /rag) ✅ Done
- [x] RAG API with 7 endpoints (create, list, get, delete, upload, query, config) ✅ Done
- [x] 12 RAG API tests (47 total passing) ✅ Done
- [ ] Add PyPDF2/pdfplumber for production PDF parsing
- [ ] Add FAISS vector store option (for high-performance use cases)
- [ ] Add Pinecone vector store option (for cloud-scale deployments)
- [ ] Connect RAG query results to LLM generation (RAG → Generate workflow)

### Phase 4: Advanced Features (Week 8-10)
> "Differentiate from the competition."

- [ ] WebSocket support for real-time execution streaming
- [ ] Multi-persona collaboration workflows
- [ ] Model fine-tuning workflow templates (dataset prep → training → eval)
- [ ] Research paper generation with citation management
- [ ] Workflow versioning and rollback
- [ ] Execution cost estimation and tracking

### Phase 5: Production & Deployment (Week 11-12)
> "Ship it."

- [ ] Production Dockerfile optimization (multi-stage builds)
- [ ] Kubernetes manifests (Helm charts)
- [ ] Cloud deployment guides (GCP, AWS, Azure)
- [ ] Monitoring and observability (Prometheus + Grafana)
- [ ] User documentation and API docs
- [ ] Security audit and penetration testing

---

## Technical Debt Register

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| SQLite → PostgreSQL | HIGH | Medium | Enables production deployment |
| Add auth middleware | HIGH | Medium | Security requirement |
| Add Alembic migrations | HIGH | Low | Prevents data loss on schema changes |
| Add CI/CD pipeline | MEDIUM | Low | Catches regressions early |
| WebSocket support | MEDIUM | Medium | Enables real-time UX |
| Next.js upgrade (security patch) | MEDIUM | Low | Fixes CVE-2025-66478 |
| Error boundary components | LOW | Low | Better error handling in UI |
| API response pagination consistency | LOW | Low | Better API design |

---

## Architecture Recommendations

### 1. Introduce a Pipeline Abstraction Layer
The current workflow engine supports linear step execution. For RAG pipelines, you need a **DAG (Directed Acyclic Graph)** execution model where steps can have multiple inputs and fan-out/fan-in patterns.

```
Current:  Step A → Step B → Step C  (linear)
Needed:   Step A → Step B ↘
                   Step C → Step E  (DAG)
          Step A → Step D ↗
```

### 2. Add a Plugin System for Step Types
Instead of hardcoding step types (prompt, transform, validate, branch), create a plugin registry where new step types can be registered:

- `rag_ingest` — Document ingestion
- `rag_embed` — Embedding generation
- `rag_retrieve` — Vector similarity search
- `fine_tune` — Model fine-tuning job
- `evaluate` — Model evaluation

### 3. Separate Configuration from Secrets
API keys should be stored in a dedicated secrets manager (or at minimum, a separate encrypted store), not in the same settings table as configuration.

---

## Final Assessment

**Grade: B-** — Good foundation, but not yet production-ready.

**Strengths**: Clean architecture, good API design, solid provider abstraction.
**Weaknesses**: Missing auth, SQLite-only, no CI, broken builds/tests (now fixed), no RAG capabilities.

The vision of replacing CLI-based AI research tools with a UI-driven platform is **excellent and commercially viable**. The current codebase is a good starting point, but it needs the Phase 1 hardening before any user-facing deployment.

**Next Steps**: Focus on Phase 1 foundation work, then Phase 2 templates. The RAG pipeline (Phase 3) is the killer feature that will differentiate this product — but don't rush to it before the foundation is solid.

---

*This review will be updated as the product evolves. Push your code daily and request reviews.*
