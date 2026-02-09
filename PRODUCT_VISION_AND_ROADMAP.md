# Agentic RAG Workflow Platform
## Product Vision & Implementation Roadmap

**Document Version:** 1.0  
**Date:** February 9, 2026  
**Status:** Strategic Planning & Vision Alignment

---

## Executive Summary

The Agentic RAG Workflow Platform is positioned as **"Webflow for RAG"** — a visual builder that enables users to create, deploy, and export production-ready RAG pipelines without deep technical expertise. Unlike traditional RAG tools that only provide hosted services or require manual coding, this platform offers three tiers of automation and includes complete code export capabilities.

**Core Value Proposition:**
- Build RAG pipelines in minutes (vs. hours with AI agents + skills, days with manual coding)
- Three modes: Manual (learning), Human-in-Loop (guided), Autonomous (agentic)
- Deploy centrally for teams OR export as standalone codebase
- Democratize RAG development for non-ML engineers

---

## Part 1: Current Implementation Status

### ✅ What Has Been Built (Production-Ready)

#### 1.1 Core RAG Engine
- **Document Processing**
  - PDF support (PyPDF2 + pdfplumber)
  - DOCX support (python-docx)
  - Text chunking with configurable size/overlap
  - Metadata extraction

- **Embedding Models**
  - Primary: BAAI/bge-small-en-v1.5 (33M params, 384 dims, CPU-optimized)
  - Secondary: Qwen/Qwen3-Embedding-0.6B (600M params, 1024 dims, GPU-ready)
  - Automatic routing based on hardware availability

- **Vector Database**
  - ChromaDB with cosine similarity (hnsw:space=cosine)
  - Fixed L2 distance issue → Cosine distance implementation
  - Local persistent storage
  - Score formula: `max(0.0, 1.0 - distance)`

- **Reranking Pipeline**
  - Qwen3-Reranker-0.6B (600M params, causal LM)
  - Yes/no token logit comparison for relevance scoring
  - LLM-based fallback reranking
  - Configurable top-K (default: 10 → 5)
  - Performance optimizations: 10-chunk cap, 500-char truncation
  - ~170s for 10 chunks on CPU

- **Multi-Provider LLM Integration**
  - Google Gemini (default: gemini-2.5-pro)
  - OpenAI (GPT models)
  - Anthropic (Claude models)
  - Fallback chain: Gemini → Groq → OpenRouter → OpenAI → Anthropic → DeepSeek
  - Enhanced Markdown formatting in system prompts

#### 1.2 Backend Architecture
- **Framework:** FastAPI (async)
- **Database:** SQLite + async SQLAlchemy + aiosqlite
- **API Structure:**
  - RESTful endpoints at `/api/v1/rag/*`
  - Pipeline CRUD operations
  - Document upload/management
  - Query execution with timing metrics
  - Retrieval configuration API

- **Key Features:**
  - Async operations throughout
  - 10-minute timeout for long-running queries
  - Structured logging (JSON format)
  - CORS configured for Next.js frontend

#### 1.3 Frontend Application
- **Framework:** Next.js 15.1.0 + React 19
- **UI Components:**
  - Pipeline creation wizard
  - Document upload with drag-and-drop
  - Real-time query interface
  - ReactMarkdown rendering for AI answers
  - Reranking controls (toggle, model selection, top-K)
  - Timing display (retrieval, reranking, LLM)
  - Source chunk display with details

- **API Communication:**
  - Direct fetch to backend (bypasses Next.js proxy for query endpoints)
  - 10-minute AbortController timeout
  - Proper error handling for timeouts and failures

#### 1.4 Testing & Quality
- **Test Coverage:** 48/48 tests passing
- **Test Types:** Unit tests, integration tests, API tests
- **Test Framework:** pytest + pytest-asyncio

#### 1.5 Local Development Setup
- Python 3.12.5 with virtual environment
- Node.js 18+ for frontend
- PostgreSQL-compatible SQLite setup
- Bash startup scripts for Codespaces/Linux deployment

#### 1.6 Git Repository Structure
- **Branches:** `copilot/build-product-ui-workflow` (main development)
- **Remote Repos:** 
  - `amittian/Agentic_WorkFlow_Platform` (main)
  - `deasyyulanda-debug/Agentic_WorkFlow_Platform` (main)
- **Last Commit:** 934adb1 (includes all db models, config, requirements)

#### 1.7 Performance Optimizations Implemented
- ChromaDB cosine distance (fixed from L2)
- Reranker input capped at 10 chunks (prevents 300s+ processing)
- Text truncation at 500 chars for reranking
- Frontend timeout increased to 10 minutes
- Model caching at class level (prevents re-downloads)
- Direct API calling (bypasses Next.js proxy bottleneck)

---

## Part 2: Alignment with Orchestra AI 83 Skills Approach

### 2.1 What Are the 83 Skills?

The Orchestra AI Skills repository contains **expert knowledge files** that make AI coding agents (Claude Code, Cursor, Codex) smarter when building systems. They are NOT ready-made applications but rather:

- Production code patterns and snippets
- Architecture decision frameworks
- Troubleshooting solutions from real GitHub issues
- Integration recipes for tools
- Best practices and optimizations
- Evaluation methodologies

**Key Insight:** Skills are meant for **AI agents to consume**, not humans to read. They enable agents to make autonomous decisions about tooling, architecture, and implementation.

### 2.2 Alignment Assessment

| Orchestra Skill Category | Our Implementation | Status |
|---|---|---|
| **Document Loading** | PyPDF2, pdfplumber, python-docx | ✅ Aligned |
| **Text Chunking** | Recursive splitting with configurable overlap | ✅ Aligned |
| **Embeddings** | bge-small-en-v1.5, Qwen3-Embedding | ✅ Aligned |
| **Vector Stores** | ChromaDB with cosine distance | ✅ Aligned |
| **Retrieval Strategies** | Top-K with fetch_k overfetch | ✅ Aligned |
| **Reranking** | Qwen3-Reranker + LLM fallback | ✅ Aligned (Advanced) |
| **Multi-Provider LLM** | Gemini, OpenAI, Anthropic + fallback chain | ✅ Aligned |
| **Full-Stack UI** | Next.js + FastAPI production app | ✅ **Beyond Skills** |
| **Hybrid Search (BM25 + Vector)** | Not implemented | 🔲 Gap |
| **Multi-Hop/Conversational RAG** | Not implemented | 🔲 Gap |
| **Evaluation Metrics** | No automated scoring | 🔲 Gap |
| **Observability/Tracing** | Basic timing logs only | 🔲 Gap |
| **Agentic Decision-Making** | Manual configuration only | 🔲 **Core Gap** |

### 2.3 What This Means

**You're ahead in:** Having a deployed, production-ready application with UI. The skills produce code snippets; you have a complete system.

**You're aligned in:** Core RAG components, model choices, architecture patterns.

**You need to add:** The **agentic layer** — where the system autonomously decides which tools, embeddings, chunking strategies, and retrieval patterns to use based on document analysis and user requirements.

### 2.4 The Critical Difference

```
Orchestra Skills Model:
  Developer → Prompt AI agent → Agent reads skills → Agent generates code → Developer runs code

Your Product Vision:
  User → Describes need → Agent analyzes → Agent decides configuration → System builds pipeline → User queries OR exports code
```

Your platform should **be the agent** that the skills teach developers to build.

---

## Part 3: Three-Tier RAG Architecture

### 3.1 Product Modes Overview

The platform will offer three distinct modes, serving different user personas and trust levels:

```
┌─────────────────────────────────────────────────────────────────┐
│                  Agentic RAG Workflow Platform                  │
│                                                                 │
│  ┌──────────────┐  ┌────────────────────┐  ┌─────────────────┐ │
│  │   Manual     │  │  Human-in-Loop     │  │  Autonomous     │ │
│  │     RAG      │  │   Agentic RAG      │  │  Agentic RAG    │ │
│  └──────────────┘  └────────────────────┘  └─────────────────┘ │
│        ↓                    ↓                       ↓           │
│   Human decides      Agent proposes          Agent decides      │
│   everything         Human approves          everything         │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Mode 1: Manual RAG Pipeline Builder

**Who:** Developers, researchers, students, curious users  
**Goal:** Learn how RAG works, experiment with configurations  
**User Control:** 100% manual  

**User Experience:**
```
1. Upload documents
2. Configure:
   • Embedding model (bge-small vs. Qwen3)
   • Vector database (ChromaDB vs. Qdrant vs. FAISS)
   • Chunk size and overlap
   • Top-K retrieval
   • Reranker (on/off, model selection)
   • LLM provider and model
3. Test queries
4. Iterate on configuration
5. Export when satisfied
```

**UI Characteristics:**
- Full configuration panel visible
- Tooltips explaining each option
- Real-time preview of chunking results
- Side-by-side comparison of different configs

**Target Persona:**
- **Learning Developer:** Wants to understand RAG internals
- **Researcher:** Testing different embedding models for academic work
- **Consultant:** Prototyping for client demos

### 3.3 Mode 2: Agentic RAG (Human-in-Loop)

**Who:** Informed users, product managers, technical leads  
**Goal:** Get AI recommendations but maintain oversight  
**User Control:** Agent proposes, human reviews and overrides  

**User Experience:**
```
1. Upload documents
2. Describe requirements in natural language:
   "I need to search legal contracts with high precision. 
    We have ~50 documents. Speed is not critical but accuracy is."
3. Agent analyzes and proposes:
   ✓ Recommended: Qdrant (hybrid search for legal precision)
   ✓ Embedding: bge-small-en-v1.5 (sufficient for 50 docs)
   ✓ Chunk size: 800 tokens, 100 overlap (preserves clause boundaries)
   ✓ Reranker: ON (Qwen3, high accuracy mode)
   ✓ LLM: Gemini 2.5 Pro (structured output for clauses)
   
   Reasoning:
   - Legal documents benefit from larger chunks to preserve context
   - Hybrid search catches exact legal terms (BM25) + semantic meaning
   - 50 docs = medium scale, no need for FAISS
   
4. User reviews each choice
5. User can override: "Actually, use Gemini 2.5 Flash for cost savings"
6. Agent adjusts: "Noted. Flash may reduce clause extraction quality by ~10%."
7. User approves final config
8. System builds pipeline
9. User tests queries
10. Export when validated
```

**UI Characteristics:**
- Natural language requirements input
- Agent presents recommendations with reasoning
- Each choice has "Why?" explanation
- Override controls for each parameter
- Before/after comparison when user changes settings

**Target Persona:**
- **Product Manager:** Understands the business need but not ML details
- **Technical Lead:** Wants speed but needs to validate choices
- **Consultant:** Needs to explain choices to clients

### 3.4 Mode 3: Agentic RAG (Autonomous)

**Who:** End users, business teams, production deployments  
**Goal:** Get answers from documents immediately  
**User Control:** Minimal — just describe the need  

**User Experience:**
```
1. Upload documents
2. Simple prompt:
   "These are our company's HR policies. I need to answer employee questions about benefits."
3. Agent:
   • Analyzes document types (PDFs, structured text)
   • Detects domain (HR, benefits language)
   • Determines scale (20 docs, ~500 pages)
   • Picks configuration automatically
   • Builds pipeline
   • Displays: "Pipeline ready. Ask your first question."
4. User immediately starts querying
5. Agent logs all decisions for transparency
6. Export available if user wants to customize later
```

**UI Characteristics:**
- Minimal interface: upload + one-line description
- No configuration options visible
- "Building your pipeline..." progress indicator
- Agent's decisions visible in "View Configuration" panel (optional)
- Query interface appears immediately when ready

**Target Persona:**
- **Business User:** Wants answers, doesn't care about ML
- **Support Team:** Needs instant search for documentation
- **Executive:** Wants insights from reports without IT involvement

### 3.5 Mode Transition Matrix

Users can switch modes at any time:

| From | To | What Happens |
|---|---|---|
| Manual → HITL | Agent reviews manual config, suggests improvements |
| Manual → Autonomous | Agent takes over, user's config becomes baseline |
| HITL → Manual | User unlocks all controls, sees agent's reasoning |
| HITL → Autonomous | User approves agent's last proposal, locks config |
| Autonomous → HITL | Agent explains current config, allows overrides |
| Autonomous → Manual | Full config panel unlocked for experimentation |

---

## Part 4: Team Deployment & Multi-Tenancy

### 4.1 Deployment Model: Centralized Server

The platform is deployed once on a shared server (on-prem or cloud) and accessed by multiple users/teams.

```
┌────────────────────────────────────────────────────┐
│  Platform: https://rag.company.com                 │
│                                                    │
│  ┌──────────────────────────────────────────┐     │
│  │  Authentication Layer                    │     │
│  │  • Username/password (Phase 1)           │     │
│  │  • SSO: Google/Microsoft (Phase 3)       │     │
│  └──────────────────────────────────────────┘     │
│                    ↓                               │
│  ┌──────────────────────────────────────────┐     │
│  │  Teams/Workspaces                        │     │
│  │  • Marketing Team (13 users)             │     │
│  │  • Legal Team (8 users)                  │     │
│  │  • Research Team (5 users)               │     │
│  └──────────────────────────────────────────┘     │
│                    ↓                               │
│  ┌──────────────────────────────────────────┐     │
│  │  Shared RAG Pipelines                    │     │
│  │  • Product Docs (Public, Query-Only)     │     │
│  │  • Legal Contracts (Team-Only, Restricted)│     │
│  │  • Research Papers (Private, Owner-Only) │     │
│  └──────────────────────────────────────────┘     │
└────────────────────────────────────────────────────┘
```

### 4.2 User Roles & Permissions

| Role | Can Create Pipelines | Can Query | Can Edit | Can Share | Can Export Code |
|---|---|---|---|---|---|
| **Admin** | ✅ All teams | ✅ All | ✅ All | ✅ All | ✅ Yes |
| **Creator** | ✅ Own team | ✅ Shared + Own | ✅ Own | ✅ Within team | ✅ Yes |
| **Member** | ❌ No | ✅ Shared + Own | ❌ No | ❌ No | ❌ No |
| **Query-Only** | ❌ No | ✅ Shared only | ❌ No | ❌ No | ❌ No |
| **Viewer** | ❌ No | ❌ No (read docs only) | ❌ No | ❌ No | ❌ No |

### 4.3 Pipeline Visibility Levels

When a user creates a pipeline, they set visibility:

```
┌─────────────────────────────────────────────┐
│  Pipeline: Product Documentation Search     │
│                                             │
│  Visibility:  [ Private ▼ ]                 │
│               • Private (only me)           │
│               • Team (Marketing Team)       │
│               • Organization (all users)    │
│               • Public Link (anyone w/ URL) │
│                                             │
│  Access Level: [ Query-Only ▼ ]            │
│                • Query-Only                 │
│                • Query + View Config        │
│                • Full Edit                  │
└─────────────────────────────────────────────┘
```

### 4.4 Query-Only Interface

For team members who just need to search (not configure):

**URL Pattern:** `https://rag.company.com/query/{pipeline_id}`

**UI Characteristics:**
- Clean search box (Google-style)
- No configuration options visible
- Auto-suggests recent queries
- Shows source documents with highlights
- "Ask a follow-up" for conversational mode

**Bookmark-Friendly:**
- Manager creates pipeline
- Sets visibility to "Team, Query-Only"
- Shares URL: `https://rag.company.com/query/legal-contracts-2026`
- Team bookmarks link, uses like internal search engine

### 4.5 Multi-Tenant Architecture Requirements

| Feature | Phase 1 (MVP) | Phase 2 (Teams) | Phase 3 (Enterprise) |
|---|---|---|---|
| User authentication | Basic auth | Auth + profiles | SSO (Google/MS) |
| Teams/workspaces | Single workspace | Multiple teams | Org hierarchy |
| Pipeline isolation | User-scoped DB rows | Team-scoped + RBAC | Full data isolation |
| API key management | Global .env keys | Team-level keys | User-level keys + quotas |
| Query history | Per-user logs | Team analytics | Cross-org reporting |
| Cost tracking | None | Team usage logs | Chargeback reports |
| Storage isolation | Shared ChromaDB | Team collections | Separate vector DBs |

### 4.6 Phased Rollout Plan

**Phase 1: Quick Multi-User Access (Week 1-2)**
- Deploy to shared server (company workstation or cloud VM)
- Add basic username/password auth
- Create `/query/{pipeline_id}` pages for query-only access
- Manager shares links to team members

**Phase 2: Full Team Platform (Month 1-2)**
- Teams/workspace management
- Role-based permissions
- Shared pipeline dashboard
- Query history per team
- Usage analytics

**Phase 3: Enterprise Features (Month 3+)**
- SSO integration
- Admin dashboard with user management
- Cost allocation per team
- Advanced security (audit logs, compliance)
- On-prem deployment packages

---

## Part 5: Code Export — The Differentiator

### 5.1 Vision Statement

**"Users shouldn't be locked into our platform. They should be able to export a production-ready, well-documented codebase at any time and run it independently or customize it further."**

This feature transforms the product from a **hosted service** to a **development accelerator**.

### 5.2 What Gets Exported

When a user clicks "Export Pipeline as Code," they receive a complete, deployable project:

```
my-rag-pipeline/
├── README.md                    # Setup guide, architecture overview
├── ARCHITECTURE.md              # Deep dive: why each tool was chosen
├── CUSTOMIZATION.md             # How to extend and modify
├── docker-compose.yml           # One-command deployment
├── Dockerfile                   # Production container
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Proper ignores
│
├── src/
│   ├── main.py                  # FastAPI app (standalone)
│   ├── config.py                # All user choices baked in
│   ├── embedding.py             # Chosen embedding model + inference
│   ├── vector_store.py          # ChromaDB/Qdrant setup + CRUD
│   ├── chunking.py              # Document processing + splitting
│   ├── reranker.py              # Reranking logic (if enabled)
│   ├── llm.py                   # LLM provider integration
│   ├── retrieval.py             # Query + retrieval logic
│   └── utils.py                 # Helpers, logging
│
├── data/
│   ├── documents/               # Optional: include uploaded docs
│   └── vector_db/               # ChromaDB persistence (optional)
│
├── tests/
│   ├── test_embedding.py        # Unit tests for each module
│   ├── test_retrieval.py
│   └── test_api.py              # E2E API tests
│
├── scripts/
│   ├── setup.sh                 # Environment setup
│   ├── ingest_docs.py           # Reingest documents
│   └── benchmark.py             # Performance testing
│
└── kubernetes/                  # Optional: K8s manifests
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```

### 5.3 Code Quality Standards

The exported code must be:

✅ **Production-Ready**
- Proper error handling
- Async operations where appropriate
- Connection pooling for databases
- Graceful shutdown handlers

✅ **Well-Documented**
- Inline comments explaining complex logic
- Docstrings for all functions
- README with clear setup steps
- Architecture diagrams (Mermaid/PlantUML)

✅ **Customizable**
- Modular design (each component is swappable)
- Configuration file for easy tuning
- Extension points documented

✅ **Tested**
- Unit tests for core functions
- Integration tests for API
- Load testing scripts included
- CI/CD config (GitHub Actions template)

✅ **Better Than Manual Coding**
- Uses best practices (logging, monitoring hooks, etc.)
- Includes optimizations discovered during platform use
- No placeholder code or TODOs

### 5.4 Export Options

Users can customize the export:

```
┌────────────────────────────────────────────┐
│  Export Pipeline: "Legal Contracts RAG"    │
│                                            │
│  Format:        [⚫ Standalone App]        │
│                 ○ API Only (no UI)         │
│                 ○ Library (pip installable)│
│                                            │
│  Deployment:    [☑] Docker Compose         │
│                 [☑] Kubernetes manifests   │
│                 [☐] AWS SAM template       │
│                 [☐] Terraform config       │
│                                            │
│  Include:       [☑] Uploaded documents     │
│                 [☑] Vector DB (pre-indexed)│
│                 [☑] Test suite             │
│                 [☑] Monitoring setup       │
│                                            │
│  License:       [⚫ MIT (permissive)]      │
│                 ○ Apache 2.0               │
│                 ○ Proprietary (your IP)    │
│                                            │
│  Attribution:   [☑] Include "Built with   │
│                     Agentic RAG Platform"  │
│                                            │
│  [Cancel]  [Export as .zip]  [Push to GitHub]│
└────────────────────────────────────────────┘
```

### 5.5 GitHub Integration (Bonus)

**"Push to GitHub" feature:**
1. User authenticates with GitHub OAuth
2. Creates new repo (or selects existing)
3. Platform commits code with:
   - Proper .gitignore
   - Initial commit message: "RAG pipeline exported from Agentic Platform"
   - Tagged release: `v1.0.0-export`
4. User can immediately:
   - Clone repo
   - Onboard developers
   - Set up CI/CD
   - Track customizations

### 5.6 Generated Documentation Example

**README.md excerpt:**

```markdown
# Legal Contracts RAG Pipeline

This RAG pipeline was built using the **Agentic RAG Workflow Platform** 
in Human-in-Loop mode on February 9, 2026.

## Architecture Decisions

| Component | Choice | Reasoning |
|---|---|---|
| **Vector DB** | Qdrant v1.7 | Hybrid search (BM25 + semantic) for legal precision |
| **Embedding** | bge-small-en-v1.5 | 384 dims, fast, sufficient for 50 docs |
| **Chunking** | 800 tokens, 100 overlap | Preserves legal clause boundaries |
| **Reranker** | Qwen3-Reranker-0.6B | High accuracy mode for contract queries |
| **LLM** | Gemini 2.5 Pro | Structured output for clause extraction |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Start with Docker
docker-compose up

# 4. API is ready at http://localhost:8000
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the termination clause?"}'
```

## Customization Guide

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for:
- Adding new embedding models
- Switching to FAISS for scale
- Implementing custom rerankers
- Integrating with LangSmith for observability
```

### 5.7 Comparison with Alternatives

| Approach | Time to Deploy | Code Quality | Customizable? | Cost |
|---|---|---|---|---|
| **Manual coding** | 3-5 days | Varies (junior to expert) | Fully | Dev time only |
| **AI agent + 83 skills** | 4-8 hours | Good (with prompt eng) | Fully | API calls + dev time |
| **LangChain templates** | 2-4 hours | Basic boilerplate | Somewhat | Free |
| **Pinecone/Weaviate (hosted)** | 1 hour | No code (hosted only) | No | $$ monthly |
| **Our Platform Export** | 10 minutes | Production-grade | Fully | Free (or Pro plan) |

**Key Differentiator:** You get both speed AND quality. Faster than AI agents, better code than templates, more flexible than hosted services.

---

## Part 6: Implementation Roadmap

### 6.1 Phase 1: Foundation Enhancement (Weeks 1-3)

**Goal:** Solidify Multi-Tenant Support + Code Export MVP

#### Week 1: Multi-Tenant Foundation
- [ ] Add user authentication (username/password)
- [ ] Create user management API
- [ ] Add `user_id` foreign key to RAG pipelines
- [ ] Implement pipeline visibility settings (private/team/public)
- [ ] Create `/query/{pipeline_id}` query-only interface
- [ ] Deploy to shared test server

#### Week 2: Code Export Engine
- [ ] Design export template structure
- [ ] Build code generator (Jinja2 templates)
- [ ] Create README/docs generators
- [ ] Implement Docker/docker-compose generation
- [ ] Add requirements.txt builder (only used packages)
- [ ] Test export with Manual RAG pipeline

#### Week 3: Export Refinement
- [ ] Add Kubernetes manifest generation
- [ ] Create ARCHITECTURE.md auto-generator
- [ ] Build test suite generator
- [ ] Implement "Push to GitHub" OAuth flow
- [ ] Add export UI to frontend
- [ ] User testing with 3-5 beta users

**Deliverable:** Users can create pipelines and export production-ready code.

---

### 6.2 Phase 2: Agentic Layer — Human-in-Loop (Weeks 4-7)

**Goal:** Implement agent that analyzes requirements and proposes configurations.

#### Week 4: Agent Planning System
- [ ] Design decision framework (rules + heuristics)
- [ ] Create document analyzer:
  - [ ] Detect document types (PDF structure, language)
  - [ ] Estimate scale (doc count, total pages)
  - [ ] Identify domain (legal, medical, general)
- [ ] Build requirement parser (NLP from user description)

#### Week 5: Configuration Recommender
- [ ] Implement embedding model selector logic
- [ ] Create vector DB recommender (ChromaDB vs. Qdrant vs. FAISS)
- [ ] Build chunking strategy selector
- [ ] Add reranker on/off decision logic
- [ ] Implement LLM model selector

#### Week 6: Reasoning & Explanation
- [ ] Create reasoning text generator:
  - "Why Qdrant? → Hybrid search needed for legal precision"
  - "Why chunk size 800? → Preserves clause boundaries"
- [ ] Build comparison module ("bge-small vs. Qwen3: speed vs. accuracy")
- [ ] Add "What if I change X?" simulator

#### Week 7: Frontend Integration
- [ ] Create Human-in-Loop UI flow
- [ ] Add natural language requirements input
- [ ] Build agent proposal display with reasoning
- [ ] Implement override controls
- [ ] Add before/after comparison view
- [ ] User testing with beta group

**Deliverable:** Users can describe needs, agent proposes config, users approve/override.

---

### 6.3 Phase 3: Full Autonomy Mode (Weeks 8-10)

**Goal:** Agent handles everything without human intervention.

#### Week 8: Zero-Config Pipeline Builder
- [ ] Implement one-click pipeline creation
- [ ] Auto-analyze uploaded documents
- [ ] Auto-configure all parameters
- [ ] Build pipeline without user input
- [ ] Add decision logging for transparency

#### Week 9: Continuous Optimization
- [ ] Create query analysis module (track slow queries)
- [ ] Implement auto-tuning:
  - Adjust top-K based on result quality
  - Switch reranker on/off based on latency budget
- [ ] Add A/B testing framework (test two configs, pick better one)

#### Week 10: Autonomous UI + Testing
- [ ] Build simplified autonomous mode UI
- [ ] Add "View Agent Decisions" panel
- [ ] Implement pipeline switching (manual ↔ HITL ↔ autonomous)
- [ ] User testing with non-technical users

**Deliverable:** Complete autonomous RAG pipeline creation.

---

### 6.4 Phase 4: Advanced Features (Weeks 11-14)

**Goal:** Add hybrid search, multi-hop, observability.

#### Week 11: Hybrid Search (BM25 + Vector)
- [ ] Integrate Qdrant (install + client)
- [ ] Implement BM25 keyword search
- [ ] Build ensemble retrieval (combine BM25 + semantic)
- [ ] Add UI controls for hybrid search weight tuning

#### Week 12: Conversational RAG
- [ ] Add conversation memory (store chat history)
- [ ] Implement context-aware query reformulation
- [ ] Build follow-up question detection
- [ ] Create conversational UI mode

#### Week 13: Observability & Tracing
- [ ] Integrate LangSmith or Phoenix
- [ ] Add structured trace logging:
  - Retrieval step traces
  - Reranking decision logs
  - LLM prompt/response pairs
- [ ] Build trace viewer UI

#### Week 14: Evaluation Dashboard
- [ ] Create ground truth dataset builder
- [ ] Implement retrieval metrics (precision, recall, MRR)
- [ ] Add answer quality scoring (ROUGE, BLEU, custom)
- [ ] Build comparison dashboard (config A vs. B)

**Deliverable:** Advanced RAG capabilities matching Orchestra skills best practices.

---

### 6.5 Phase 5: Enterprise Features (Weeks 15-18)

**Goal:** Make platform enterprise-ready.

#### Week 15: Teams & Workspaces
- [ ] Create team management API
- [ ] Implement workspace isolation
- [ ] Add team-level API key management
- [ ] Build team admin dashboard

#### Week 16: Advanced Auth & Security
- [ ] Implement SSO (Google, Microsoft)
- [ ] Add RBAC (role-based access control)
- [ ] Create audit logs
- [ ] Implement data encryption at rest

#### Week 17: Cost Tracking & Quotas
- [ ] Track LLM API usage per user/team
- [ ] Implement usage quotas
- [ ] Create cost allocation reports
- [ ] Add billing integration (optional)

#### Week 18: On-Prem Deployment
- [ ] Create on-prem installation package
- [ ] Build Helm chart for Kubernetes
- [ ] Add white-label export option
- [ ] Write enterprise deployment guide

**Deliverable:** Enterprise-grade multi-tenant platform.

---

### 6.6 Summary Timeline

| Phase | Duration | Key Deliverable |
|---|---|---|
| **Phase 1: Foundation** | Weeks 1-3 | Multi-tenant + Code Export MVP |
| **Phase 2: HITL Agent** | Weeks 4-7 | Agent proposes configs, user approves |
| **Phase 3: Autonomous** | Weeks 8-10 | Fully autonomous pipeline creation |
| **Phase 4: Advanced RAG** | Weeks 11-14 | Hybrid search, observability, evaluation |
| **Phase 5: Enterprise** | Weeks 15-18 | Teams, SSO, on-prem deployment |

**Total:** ~4.5 months to full product maturity.

---

## Part 7: Technical Architecture Details

### 7.1 Current Tech Stack (Production)

| Layer | Technology | Version | Notes |
|---|---|---|---|
| **Backend Framework** | FastAPI | 0.115.0 | Async Python web framework |
| **Database** | SQLite + SQLAlchemy | 2.0.36 | Async ORM with aiosqlite |
| **Vector Store** | ChromaDB | 0.4.15+ | Local vector database |
| **Embeddings** | Sentence Transformers | 2.2.0+ | bge-small-en-v1.5, Qwen3 |
| **Reranker** | Transformers (HF) | 5.1.0 | Qwen3-Reranker-0.6B |
| **LLM Integration** | google-generativeai | 0.8.3 | Gemini 2.5 Pro primary |
| | openai | 1.54.4 | GPT models |
| | anthropic | 0.39.0 | Claude models |
| **ML Framework** | torch | 2.10.0+cpu | CPU-only inference |
| **Document Processing** | PyPDF2, pdfplumber | 3.0.0+, 0.10.0+ | PDF parsing |
| | python-docx | 1.0.0+ | DOCX parsing |
| **Frontend** | Next.js | 15.1.0 | React 19 framework |
| **HTTP Client** | axios | 1.7.9 | API communication |
| **Markdown Rendering** | react-markdown | Latest | AI answer formatting |
| **Testing** | pytest, pytest-asyncio | 8.0.0+, 0.23.0+ | 48/48 tests passing |

### 7.2 Planned Tech Stack Additions

| Feature | Technology | Reason |
|---|---|---|
| **Hybrid Search** | Qdrant | BM25 + semantic search |
| **Observability** | LangSmith or Phoenix | Structured tracing |
| **Evaluation** | RAGAS or custom | Automated quality scoring |
| **Auth** | Auth0 or Authelia | SSO + RBAC |
| **Monitoring** | Prometheus + Grafana | Metrics dashboard |
| **Container Orchestration** | Kubernetes | Production deployment |

### 7.3 Data Models

#### 7.3.1 Core Database Schema

```python
# User Management
class User(Base):
    id: UUID
    username: str
    email: str
    hashed_password: str
    role: UserRole  # admin, creator, member, viewer
    created_at: datetime
    teams: List[Team]

# Team/Workspace
class Team(Base):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    created_at: datetime
    members: List[User]
    api_keys: Dict[str, str]  # Encrypted

# RAG Pipeline (Extended)
class RAGPipelineDB(Base):
    id: UUID
    name: str
    description: str
    owner_id: UUID  # NEW
    team_id: UUID | None  # NEW
    visibility: PipelineVisibility  # private, team, org, public
    mode: PipelineMode  # manual, hitl, autonomous
    status: str
    embedding_config: Dict
    vector_store_config: Dict
    retrieval_config: Dict
    llm_config: Dict
    agent_decisions: Dict | None  # NEW: logs agent's reasoning
    created_at: datetime
    updated_at: datetime

# Query History (NEW)
class QueryHistory(Base):
    id: UUID
    pipeline_id: UUID
    user_id: UUID
    query: str
    answer: str
    chunks_retrieved: List[Dict]
    retrieval_time_ms: int
    reranking_time_ms: int
    llm_time_ms: int
    total_time_ms: int
    feedback: int | None  # thumbs up/down
    created_at: datetime
```

#### 7.3.2 Agent Decision Log Schema

```python
{
  "pipeline_id": "abc-123",
  "mode": "human_in_loop",
  "analyzed_at": "2026-02-09T10:30:00Z",
  "document_analysis": {
    "count": 50,
    "total_pages": 1250,
    "avg_page_length": 450,
    "detected_type": "legal_contracts",
    "language": "en",
    "domain_keywords": ["termination", "liability", "indemnification"]
  },
  "requirements": {
    "user_input": "Search legal contracts with high precision",
    "parsed_intent": {
      "accuracy_priority": "high",
      "speed_priority": "low",
      "scale": "medium"
    }
  },
  "decisions": [
    {
      "component": "vector_db",
      "recommended": "qdrant",
      "alternatives": ["chromadb", "faiss"],
      "reasoning": "Hybrid search (BM25 + semantic) improves precision for legal terms by 25-40%",
      "confidence": 0.92
    },
    {
      "component": "embedding",
      "recommended": "bge-small-en-v1.5",
      "alternatives": ["qwen3-embedding"],
      "reasoning": "50 docs = medium scale, bge-small sufficient. Qwen3 adds latency (170ms vs 20ms) without accuracy gain at this scale",
      "confidence": 0.88
    },
    {
      "component": "chunking",
      "recommended": {"size": 800, "overlap": 100},
      "alternatives": [{"size": 500, "overlap": 50}],
      "reasoning": "Legal clauses average 600-900 tokens. Larger chunks preserve clause boundaries, reducing split clauses by 65%",
      "confidence": 0.95
    }
  ],
  "user_overrides": [
    {
      "component": "llm",
      "agent_recommended": "gemini-2.5-pro",
      "user_chose": "gemini-2.5-flash",
      "reason": "Cost optimization",
      "agent_warning": "Flash may reduce clause extraction quality by ~10%"
    }
  ]
}
```

### 7.4 Code Export Architecture

```python
# Export Engine Design

class PipelineExporter:
    """Generates production-ready code from pipeline config."""
    
    def __init__(self, pipeline: RAGPipelineDB):
        self.pipeline = pipeline
        self.templates = TemplateLoader()
    
    def export(self, options: ExportOptions) -> ExportedProject:
        """Main export orchestrator."""
        project = ExportedProject()
        
        # 1. Generate core application code
        project.add_file("src/main.py", self._generate_main())
        project.add_file("src/config.py", self._generate_config())
        project.add_file("src/embedding.py", self._generate_embedding())
        project.add_file("src/retrieval.py", self._generate_retrieval())
        
        # 2. Generate deployment configs
        if options.include_docker:
            project.add_file("Dockerfile", self._generate_dockerfile())
            project.add_file("docker-compose.yml", self._generate_compose())
        
        if options.include_kubernetes:
            project.add_dir("kubernetes", self._generate_k8s_manifests())
        
        # 3. Generate documentation
        project.add_file("README.md", self._generate_readme())
        project.add_file("ARCHITECTURE.md", self._generate_architecture_doc())
        
        # 4. Include optional data
        if options.include_documents:
            project.add_dir("data/documents", self._export_documents())
        
        if options.include_vector_db:
            project.add_dir("data/vector_db", self._export_chromadb())
        
        # 5. Generate tests
        if options.include_tests:
            project.add_dir("tests", self._generate_tests())
        
        return project
    
    def _generate_main(self) -> str:
        """Generate FastAPI app with user's exact config."""
        return self.templates.render("main.py.jinja2", {
            "embedding_model": self.pipeline.embedding_config["model_name"],
            "vector_db": self.pipeline.vector_store_config["type"],
            "reranker_enabled": self.pipeline.retrieval_config.get("reranking_enabled", False),
            "llm_provider": self.pipeline.llm_config["provider"],
            "llm_model": self.pipeline.llm_config["model"]
        })
    
    def _generate_readme(self) -> str:
        """Generate comprehensive README."""
        return self.templates.render("README.md.jinja2", {
            "pipeline_name": self.pipeline.name,
            "created_date": self.pipeline.created_at,
            "mode": self.pipeline.mode,
            "decisions": self.pipeline.agent_decisions,
            "architecture_table": self._build_architecture_table()
        })
```

### 7.5 Agent Decision Engine Design

```python
# Agent Architecture

class AgenticRAGBuilder:
    """Autonomous RAG pipeline configuration agent."""
    
    def __init__(self, llm_provider: BaseLLM):
        self.llm = llm_provider  # Uses Gemini 2.5 Pro for reasoning
        self.analyzer = DocumentAnalyzer()
        self.recommender = ConfigurationRecommender()
        self.explainer = DecisionExplainer()
    
    async def build_pipeline(
        self, 
        documents: List[Document], 
        requirements: str,
        mode: PipelineMode
    ) -> PipelineConfig:
        """Main agent orchestration."""
        
        # 1. Analyze uploaded documents
        doc_profile = await self.analyzer.analyze(documents)
        
        # 2. Parse user requirements
        parsed_reqs = await self._parse_requirements(requirements, doc_profile)
        
        # 3. Make configuration decisions
        config = await self.recommender.recommend(doc_profile, parsed_reqs)
        
        # 4. Generate explanations
        explanations = await self.explainer.explain(config, doc_profile, parsed_reqs)
        
        # 5. Handle mode-specific flows
        if mode == PipelineMode.HUMAN_IN_LOOP:
            # Return config + explanations for user review
            return {
                "config": config,
                "explanations": explanations,
                "requires_approval": True
            }
        
        elif mode == PipelineMode.AUTONOMOUS:
            # Apply config immediately, log decisions
            return {
                "config": config,
                "explanations": explanations,
                "requires_approval": False,
                "decision_log": self._build_decision_log(config, explanations)
            }
    
    async def _parse_requirements(self, requirements: str, doc_profile: Dict) -> Dict:
        """Use LLM to extract structured requirements from natural language."""
        
        prompt = f"""
        User uploaded {doc_profile['count']} documents ({doc_profile['type']}).
        User requirements: "{requirements}"
        
        Extract:
        1. Accuracy priority (high/medium/low)
        2. Speed priority (high/medium/low)
        3. Cost sensitivity (high/medium/low)
        4. Specific domain needs (e.g., "legal precision", "medical terminology")
        
        Return JSON.
        """
        
        response = await self.llm.generate(prompt)
        return json.loads(response)
    

class ConfigurationRecommender:
    """Recommends optimal RAG configuration."""
    
    def recommend(self, doc_profile: Dict, requirements: Dict) -> PipelineConfig:
        """Rule-based + heuristic decision system."""
        
        config = PipelineConfig()
        
        # Vector DB selection
        if doc_profile['count'] > 10_000:
            config.vector_db = "faiss"  # Billion-scale
        elif requirements['accuracy_priority'] == 'high' and doc_profile['type'] in ['legal', 'medical']:
            config.vector_db = "qdrant"  # Hybrid search
        else:
            config.vector_db = "chromadb"  # Default, simple
        
        # Embedding model selection
        if doc_profile['count'] < 100 and requirements['speed_priority'] == 'high':
            config.embedding = "bge-small-en-v1.5"  # Fast, sufficient
        elif requirements['accuracy_priority'] == 'high':
            config.embedding = "qwen3-embedding"  # Higher quality
        else:
            config.embedding = "bge-small-en-v1.5"  # Default
        
        # Chunking strategy
        if doc_profile['type'] == 'legal':
            config.chunk_size = 800  # Preserve clauses
            config.chunk_overlap = 100
        elif doc_profile['type'] == 'chat':
            config.chunk_size = 300  # Short messages
            config.chunk_overlap = 30
        else:
            config.chunk_size = 500  # Default
            config.chunk_overlap = 50
        
        # Reranker decision
        if requirements['accuracy_priority'] == 'high' and requirements['speed_priority'] != 'high':
            config.reranker_enabled = True
            config.reranker_model = "qwen3-reranker"
        else:
            config.reranker_enabled = False
        
        # LLM selection
        if requirements['cost_sensitivity'] == 'high':
            config.llm_model = "gemini-2.5-flash"
        else:
            config.llm_model = "gemini-2.5-pro"  # Default
        
        return config
```

---

## Part 8: Business Model & Monetization

### 8.1 Tiered Pricing Strategy

| Tier | Price | Target User | Key Features |
|---|---|---|---|
| **Free** | $0/month | Students, hobbyists, solo devs | Manual RAG only, 3 pipelines, export with attribution |
| **Pro** | $29/user/month | Teams, consultants | All 3 RAG modes, unlimited pipelines, no attribution, query-only users free |
| **Enterprise** | Custom | Large orgs | On-prem deployment, SSO, white-label exports, dedicated support |

### 8.2 Value Metrics

| Metric | Measure | Enterprise Value |
|---|---|---|
| **Time Saved** | Manual: 3-5 days → Platform: 10 min | $5,000+ in dev time |
| **Code Quality** | Junior dev vs. production-grade | Fewer bugs, faster deployment |
| **Flexibility** | Hosted + export options | No vendor lock-in |
| **Learning Curve** | Zero ML knowledge required | Democratizes RAG |

---

## Part 9: Success Criteria & KPIs

### 9.1 Technical KPIs

- [ ] **Pipeline Creation Time:** < 5 minutes for autonomous mode
- [ ] **Query Latency:** < 3 seconds for 10-doc retrieval + reranking
- [ ] **Export Time:** < 30 seconds for full project generation
- [ ] **Test Coverage:** > 90% for core modules
- [ ] **Uptime:** 99.5% for hosted platform

### 9.2 User Experience KPIs

- [ ] **Onboarding:** User creates first pipeline in < 10 minutes
- [ ] **Autonomous Accuracy:** Agent chooses optimal config 80%+ of the time
- [ ] **Export Usability:** Exported code runs without errors 95%+ of the time
- [ ] **User Satisfaction:** NPS score > 50

### 9.3 Business KPIs

- [ ] **User Acquisition:** 1,000 beta users in first 3 months
- [ ] **Conversion:** 5% free → Pro conversion rate
- [ ] **Retention:** 70% monthly active user retention
- [ ] **Enterprise Deals:** 5 enterprise contracts in first 6 months

---

## Part 10: Competitive Analysis

### 10.1 Direct Competitors

| Competitor | Strength | Weakness | Our Advantage |
|---|---|---|---|
| **LangChain** | Established ecosystem | Code-first, steep learning curve | No-code + code export |
| **Pinecone** | Managed vector DB | Vendor lock-in, cost scales with usage | Export freedom |
| **Weaviate** | Open-source option | Still requires coding | UI + export |
| **ChatGPT Plugins** | Consumer-friendly | No customization, closed | Full control + export |

### 10.2 Positioning Statement

**"We're the Webflow for RAG — build visually, export production code, deploy anywhere."**

---

## Part 11: Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| **Agent Makes Poor Choices** | High | Medium | Human-in-loop mode + decision logs |
| **Exported Code Has Bugs** | High | Low | Extensive testing, user feedback loop |
| **Competitors Copy Approach** | Medium | High | Fast execution, patent code export flow |
| **LLM API Costs Explode** | Medium | Low | Cost tracking, user quotas |
| **Users Don't Trust Agent** | High | Medium | Transparency, explainability, manual fallback |

---

## Part 12: Next Steps — Immediate Actions

### 12.1 This Week
- [x] Complete brainstorming session ✅
- [ ] Review and refine this document with stakeholders
- [ ] Set up project management (GitHub Projects or Jira)
- [ ] Create development environment for Phase 1
- [ ] Design database schema for multi-tenant support
- [ ] Prototype code export engine (single template)

### 12.2 This Month (Phase 1)
- [ ] Implement user authentication
- [ ] Build query-only interface
- [ ] Create basic code export (README + Dockerfile)
- [ ] Deploy to shared test server
- [ ] Recruit 10 beta testers
- [ ] Iterate based on feedback

### 12.3 Quarter 1 (Phases 1-2)
- [ ] Complete multi-tenant platform
- [ ] Launch Human-in-Loop agentic mode
- [ ] Full code export with GitHub integration
- [ ] Onboard 100 beta users
- [ ] Validate product-market fit

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation — AI that searches documents before answering |
| **Embedding** | Numerical representation of text for semantic search |
| **Vector Database** | Database optimized for similarity search (ChromaDB, Qdrant, FAISS) |
| **Reranking** | Re-scoring retrieved documents for better relevance |
| **Top-K** | Number of most relevant chunks to retrieve (e.g., top 10) |
| **Chunking** | Breaking documents into smaller pieces for indexing |
| **BM25** | Keyword-based search algorithm (used in hybrid search) |
| **Cosine Similarity** | Measure of similarity between two vectors (0-1 scale) |
| **HITL** | Human-in-the-Loop — agent proposes, human approves |
| **Orchestra Skills** | GitHub repo with 83 AI/ML expert knowledge files |

---

## Appendix B: Reference Links

- **Orchestra AI Skills Repo:** https://github.com/orchestra-ai-research/AI-Research-Skills
- **ChromaDB Docs:** https://docs.trychroma.com/
- **Sentence Transformers:** https://www.sbert.net/
- **Qwen Models (HuggingFace):** https://huggingface.co/Qwen
- **LangChain:** https://docs.langchain.com/
- **Qdrant:** https://qdrant.tech/documentation/

---

## Document History

| Version | Date | Changes | Author |
|---|---|---|---|
| 1.0 | Feb 9, 2026 | Initial comprehensive document | Product Team |

---

**END OF DOCUMENT**

*This document is a living roadmap and will be updated as the product evolves. All stakeholders should review and provide feedback within 48 hours.*
