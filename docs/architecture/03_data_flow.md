# Data Flow Architecture - Agentic Workflow Platform

**Document Version:** 1.0  
**Date:** February 4, 2026  
**Purpose:** Request/response lifecycles, state transitions, data transformations

---

## 1. Settings Configuration Flow

### User Story: Configure OpenAI Provider

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Next as Next.js (SSR)
    participant API as FastAPI
    participant Settings as SettingsService
    participant Security as SecretManager
    participant DB as SQLite

    Note over User,DB: Page Load
    User->>Browser: Navigate to /settings
    Browser->>Next: GET /settings
    Next->>API: GET /settings/providers
    API-->>Next: [{name: "openai", connected: false}, ...]
    Next-->>Browser: Render Settings Page (SSR)
    Browser-->>User: Display Provider List

    Note over User,DB: API Key Configuration
    User->>Browser: Select OpenAI + Enter API Key
    Browser->>API: POST /settings/secrets<br/>{provider: "openai", api_key: "sk-..."}
    
    API->>API: Validate Request (Pydantic)
    API->>Settings: store_secret("openai", "sk-...")
    
    Settings->>Security: encrypt("sk-...")
    Security->>Security: Fernet.encrypt()
    Security-->>Settings: "gAAAAB...encrypted..."
    
    Settings->>DB: INSERT/UPDATE settings<br/>encrypted_value="gAAAAB..."
    DB-->>Settings: Success
    
    Settings->>Settings: Test Connection (health_check)
    Settings->>OpenAI: GET /models (minimal call)
    OpenAI-->>Settings: 200 OK
    
    Settings-->>API: {connected: true, updated_at: "2026-02-04T..."}
    API-->>Browser: 200 OK {connected: true}
    Browser-->>User: "✅ Connected to OpenAI"
```

**Data Transformations:**

| Stage | Format | Example |
|-------|--------|---------|
| **User Input** | Plain text | `sk-1234567890abcdef` |
| **API Request** | JSON | `{"provider": "openai", "api_key": "sk-..."}` |
| **Validated** | Pydantic Model | `SecretRequest(provider=Provider.OPENAI, api_key=SecretStr(...))` |
| **Encrypted** | Base64 Fernet | `gAAAABfK7...` (160 chars) |
| **Stored** | SQLite TEXT | `encrypted_value` column |
| **Retrieved** | Decrypted str | `sk-1234567890abcdef` (in memory only) |
| **API Response** | JSON (status only) | `{"connected": true}` (never exposes key) |

**Security Boundaries:**
- 🔒 **Browser → API**: HTTPS only, key transmitted once
- 🔒 **API → DB**: Encrypted at rest (Fernet symmetric)
- 🔒 **DB → Memory**: Decrypted on-demand, never logged
- 🔒 **API → Browser**: Connection status only, no secrets

---

## 2. Workflow Discovery Flow

### User Story: Browse Available Workflows

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Next as Next.js
    participant API as FastAPI
    participant Workflow as WorkflowService
    participant DB as SQLite

    User->>Browser: Navigate to /workflows
    Browser->>Next: GET /workflows (SSR)
    
    Next->>API: GET /workflows?persona=student
    API->>Workflow: get_workflows(persona="student")
    
    Workflow->>DB: SELECT * FROM workflows<br/>WHERE persona='student' AND active=true
    DB-->>Workflow: [{id, name, description, schema_summary}, ...]
    
    Workflow->>Workflow: Enrich with metadata<br/>(tags, estimated_time, difficulty)
    Workflow-->>API: List[WorkflowSummary]
    
    API-->>Next: 200 OK [{id: "learn_agentic_ai", name: "Learn Agentic AI", ...}]
    Next-->>Browser: Render Workflow Cards (SSR)
    Browser-->>User: Display Workflow Catalog

    User->>Browser: Click "Learn Agentic AI"
    Browser->>Browser: Navigate to /workflows/learn_agentic_ai
```

**Data Transformations:**

```
Database Record (SQLite)
  ↓
WorkflowModel (SQLAlchemy ORM)
  ↓
WorkflowSummary (Pydantic)
  ↓
JSON Response
  ↓
TypeScript WorkflowCard Props
  ↓
React Component Render
```

---

## 3. Workflow Execution Flow (Core)

### User Story: Execute "Learn Agentic AI" in Test-Run Mode

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Next as Next.js
    participant API as FastAPI
    participant Runs as RunService
    participant Workflow as WorkflowService
    participant Engine as WorkflowEngine
    participant Validator as ValidationService
    participant Provider as ProviderFactory
    participant OpenAI as OpenAI API
    participant DB as SQLite
    participant FS as File System

    Note over User,FS: Phase 1: Schema Retrieval
    User->>Browser: Navigate to /workflows/learn_agentic_ai
    Browser->>API: GET /workflows/learn_agentic_ai/schema
    API->>Workflow: get_workflow_schema("learn_agentic_ai")
    Workflow->>DB: SELECT schema FROM workflows WHERE id=...
    DB-->>Workflow: JSON Schema (fields, types, options)
    Workflow-->>API: WorkflowSchema
    API-->>Browser: 200 OK {fields: [{name: "learning_goal", ...}], ...}
    Browser->>Browser: Render Dynamic Form (React Hook Form)
    Browser-->>User: Display Form

    Note over User,FS: Phase 2: Form Submission
    User->>Browser: Fill form + Select Test-Run Mode
    Browser->>Browser: Validate inputs (Zod)
    Browser->>API: POST /runs<br/>{workflow_id, inputs: {...}, run_mode: "test_run"}

    API->>API: Validate Request (Pydantic)
    API->>Runs: create_and_execute(request)

    Runs->>Workflow: get_workflow("learn_agentic_ai")
    Workflow->>DB: SELECT * FROM workflows WHERE id=...
    DB-->>Workflow: Workflow Record
    Workflow-->>Runs: Workflow Object

    Runs->>DB: INSERT INTO runs (id, workflow_id, inputs, run_mode, status='queued')
    DB-->>Runs: run_id="abc-123-def"

    Runs-->>API: Run Object {id: "abc-123-def", status: "queued"}
    API-->>Browser: 201 Created {run_id: "abc-123-def"}
    Browser-->>User: "Run started... (run_id: abc-123-def)"

    Note over User,FS: Phase 3: Async Execution (Non-Blocking)
    Runs->>Runs: asyncio.create_task(_execute_run("abc-123-def"))

    Note over Runs,FS: Background Task Execution
    Runs->>DB: UPDATE runs SET status='validating' WHERE id=...

    Runs->>Engine: validate(run_id="abc-123-def")
    Engine->>Validator: execute_validate_only(workflow, inputs)
    
    Validator->>DB: Get encrypted secrets
    DB-->>Validator: encrypted_value="gAAAAB..."
    Validator->>Validator: Decrypt secret
    
    Validator->>Provider: get_provider("openai")
    Provider->>Provider: Instantiate OpenAIAdapter(api_key=decrypted)
    Provider-->>Validator: OpenAIAdapter
    
    Validator->>OpenAI: GET /models (health check)
    OpenAI-->>Validator: 200 OK
    
    Validator->>Validator: Validate input schema
    Validator-->>Engine: ValidationResult(success=true)
    
    Engine-->>Runs: Validation Passed

    Runs->>DB: UPDATE runs SET status='running' WHERE id=...

    Runs->>Engine: execute(run_id="abc-123-def")
    Engine->>Engine: Get TestRun strategy (max_tokens=1000)
    
    Engine->>Provider: get_provider("openai")
    Provider-->>Engine: OpenAIAdapter
    
    Engine->>Engine: Build prompt from workflow + inputs
    Engine->>OpenAI: POST /chat/completions<br/>{messages: [...], max_tokens: 1000, tools: [...]}
    OpenAI-->>Engine: Completion Response
    
    Engine->>Engine: Process response + tool calls
    Engine->>Engine: Format output (notes, trace)
    
    Engine->>FS: Write /data/artifacts/abc-123-def/notes.md
    FS-->>Engine: Success
    Engine->>FS: Write /data/artifacts/abc-123-def/trace.json
    FS-->>Engine: Success
    
    Engine->>DB: INSERT INTO artifacts (run_id, artifact_type, file_path)
    DB-->>Engine: Success
    
    Engine-->>Runs: ExecutionResult(success=true, artifacts=[...])
    
    Runs->>DB: UPDATE runs SET status='completed', artifacts_path='/data/artifacts/abc-123-def'
    DB-->>Runs: Success

    Note over User,FS: Phase 4: Polling for Results
    Browser->>API: GET /runs/abc-123-def (polling every 2s)
    API->>Runs: get_run("abc-123-def")
    Runs->>DB: SELECT * FROM runs WHERE id=...
    DB-->>Runs: Run Record {status: 'completed', ...}
    Runs-->>API: Run Object
    API-->>Browser: 200 OK {status: "completed", artifacts: [...]}
    Browser-->>User: "✅ Run completed! View results →"

    User->>Browser: Click "View Results"
    Browser->>Browser: Navigate to /runs/abc-123-def

    Browser->>API: GET /runs/abc-123-def/artifacts
    API->>FS: Read /data/artifacts/abc-123-def/notes.md
    FS-->>API: Markdown Content
    API->>FS: Read /data/artifacts/abc-123-def/trace.json
    FS-->>API: JSON Trace
    API-->>Browser: 200 OK {notes: "# Learning Notes...", trace: {...}}
    Browser->>Browser: Render Markdown + Trace Viewer
    Browser-->>User: Display Results
```

---

## 4. Run State Machine

### Run Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Queued: POST /runs
    
    Queued --> Validating: Async task starts
    
    Validating --> Failed: Validation fails
    Validating --> Running: Validation passes
    
    Running --> Failed: Execution error
    Running --> Completed: Success
    
    Failed --> [*]
    Completed --> [*]
    
    note right of Validating
        - Check secrets exist
        - Test provider connection
        - Validate input schema
        - Estimate cost (future)
    end note
    
    note right of Running
        - Apply run mode caps
        - Execute workflow stages
        - Call LLM provider(s)
        - Generate artifacts
    end note
```

**Status Descriptions:**

| Status | Description | User Action | Duration |
|--------|-------------|-------------|----------|
| **Queued** | Run created, awaiting execution | Wait | <1s |
| **Validating** | Preflight checks running | Wait | 2-5s |
| **Running** | Workflow executing | Wait | 30s-10min |
| **Completed** | Success, artifacts available | View results | Final |
| **Failed** | Error occurred, check logs | Retry / debug | Final |

---

## 5. Data Persistence Strategy

### Write Patterns

**Database (SQLite/PostgreSQL):**
```
┌──────────────────────────────────────┐
│ Metadata (fast queries)              │
├──────────────────────────────────────┤
│ • Run status, timestamps             │
│ • User settings (encrypted secrets)  │
│ • Workflow definitions               │
│ • Artifact metadata (paths, sizes)   │
└──────────────────────────────────────┘
```

**File System (Artifacts):**
```
/data/artifacts/
├── {run_id}/
│   ├── notes.md         ← Workflow output
│   ├── trace.json       ← Execution trace
│   ├── logs.txt         ← Debug logs
│   └── metadata.json    ← Run config
```

**Why Split Storage?**
- **DB**: Fast queries, indexing, relational data
- **FS**: Large text files, easier export, cheaper storage
- **Migration**: FS → S3 later without DB schema changes

---

## 6. Error Handling Flow

### Scenario: Provider API Failure During Execution

```mermaid
sequenceDiagram
    participant Engine as WorkflowEngine
    participant Provider as OpenAIAdapter
    participant OpenAI as OpenAI API
    participant DB as SQLite
    participant Logger

    Engine->>Provider: complete(messages, max_tokens=1000)
    Provider->>OpenAI: POST /chat/completions
    OpenAI-->>Provider: 429 Rate Limit Exceeded
    
    Provider->>Provider: Catch openai.RateLimitError
    Provider->>Logger: log.warning("Rate limit hit", extra={...})
    
    Provider->>Provider: Retry with exponential backoff<br/>(attempt 1/3, wait 2s)
    Provider->>OpenAI: POST /chat/completions (retry)
    OpenAI-->>Provider: 429 Rate Limit Exceeded
    
    Provider->>Provider: Retry (attempt 2/3, wait 4s)
    Provider->>OpenAI: POST /chat/completions (retry)
    OpenAI-->>Provider: 500 Internal Server Error
    
    Provider->>Provider: Retry (attempt 3/3, wait 8s)
    Provider->>OpenAI: POST /chat/completions (retry)
    OpenAI-->>Provider: Timeout (30s)
    
    Provider->>Logger: log.error("Provider failure after retries", exc_info=True)
    Provider-->>Engine: Raise ProviderError("OpenAI unavailable")
    
    Engine->>Engine: Catch ProviderError
    Engine->>DB: UPDATE runs SET status='failed',<br/>error_message='OpenAI unavailable after 3 retries'
    Engine->>Logger: log.error("Run failed", extra={run_id, error})
    
    Engine-->>User: Error propagates to API response
```

**Error Categories:**

| Error Type | HTTP Status | Retry? | User Message |
|------------|-------------|--------|--------------|
| **ValidationError** | 400 | No | "Invalid input: {details}" |
| **ProviderError** | 502 | Yes (3x) | "Provider unavailable, try again later" |
| **RateLimitError** | 429 | Yes (backoff) | "Rate limit exceeded, retrying..." |
| **TimeoutError** | 504 | Yes (1x) | "Request timed out, try Test-Run mode" |
| **InternalError** | 500 | No | "Internal error, contact support" |

---

## 7. Frontend State Management

### Zustand Store Architecture

```typescript
// src/lib/stores/runs.ts
interface RunsState {
  // State
  runs: Record<string, Run>;
  currentRunId: string | null;
  pollingIntervals: Record<string, NodeJS.Timeout>;

  // Actions
  createRun: (request: CreateRunRequest) => Promise<string>;
  fetchRun: (runId: string) => Promise<void>;
  startPolling: (runId: string) => void;
  stopPolling: (runId: string) => void;
}

const useRunsStore = create<RunsState>((set, get) => ({
  runs: {},
  currentRunId: null,
  pollingIntervals: {},

  createRun: async (request) => {
    const response = await api.post('/runs', request);
    const run = response.data;
    
    set((state) => ({
      runs: { ...state.runs, [run.id]: run },
      currentRunId: run.id
    }));
    
    // Start polling for status
    get().startPolling(run.id);
    
    return run.id;
  },

  fetchRun: async (runId) => {
    const response = await api.get(`/runs/${runId}`);
    const run = response.data;
    
    set((state) => ({
      runs: { ...state.runs, [runId]: run }
    }));
    
    // Stop polling if terminal status
    if (['completed', 'failed'].includes(run.status)) {
      get().stopPolling(runId);
    }
  },

  startPolling: (runId) => {
    const interval = setInterval(() => {
      get().fetchRun(runId);
    }, 2000); // Poll every 2s
    
    set((state) => ({
      pollingIntervals: { ...state.pollingIntervals, [runId]: interval }
    }));
  },

  stopPolling: (runId) => {
    const interval = get().pollingIntervals[runId];
    if (interval) {
      clearInterval(interval);
      set((state) => {
        const { [runId]: _, ...rest } = state.pollingIntervals;
        return { pollingIntervals: rest };
      });
    }
  }
}));
```

**Data Flow:**
```
User Action (Submit Form)
  ↓
Zustand Action (createRun)
  ↓
API Call (POST /runs)
  ↓
Optimistic Update (add to runs map)
  ↓
Start Polling (every 2s)
  ↓
Update State (on each poll)
  ↓
Stop Polling (on completed/failed)
  ↓
Component Re-render (useRunsStore)
```

---

## 8. Performance Optimizations

### Async Patterns

**Parallel Execution:**
```python
# Bad: Sequential (slow)
await validate_secrets()
await validate_schema()
await test_connection()

# Good: Parallel (fast)
await asyncio.gather(
    validate_secrets(),
    validate_schema(),
    test_connection()
)
```

**Connection Pooling:**
```python
# SQLAlchemy pool settings
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Max connections
    max_overflow=10,       # Additional connections
    pool_pre_ping=True,    # Test connection before use
    pool_recycle=3600      # Recycle after 1 hour
)

# httpx client pooling
provider_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    ),
    timeout=30.0
)
```

**Streaming Response (Future):**
```python
@router.get("/runs/{run_id}/stream")
async def stream_run_output(run_id: str):
    """Stream workflow output in real-time"""
    async def generate():
        async for chunk in workflow_engine.stream_execute(run_id):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 9. Scalability Considerations

### Current (MVP): Single-Node

```
┌─────────────────────────────────┐
│  Docker Compose                 │
│  ┌─────────┐    ┌────────────┐ │
│  │ Next.js │    │  FastAPI   │ │
│  │  :3000  │───▶│   :8000    │ │
│  └─────────┘    └────────────┘ │
│                      │          │
│                      ▼          │
│                 ┌────────┐      │
│                 │ SQLite │      │
│                 └────────┘      │
└─────────────────────────────────┘
```

### Future: Distributed

```
┌──────────────┐
│ Load Balancer│
└──┬────────┬──┘
   │        │
   ▼        ▼
┌──────┐ ┌──────┐
│ Web 1│ │ Web 2│  (Next.js, horizontal scale)
└──┬───┘ └───┬──┘
   │         │
   └────┬────┘
        ▼
┌───────────────┐
│ API Gateway   │
└──┬────────┬───┘
   │        │
   ▼        ▼
┌──────┐ ┌──────┐
│ API 1│ │ API 2│  (FastAPI, horizontal scale)
└──┬───┘ └───┬──┘
   │         │
   └────┬────┘
        ▼
┌───────────────┐
│ Redis Queue   │  (Celery tasks)
└───────┬───────┘
        │
   ┌────┴────┐
   ▼         ▼
┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│  (Workflow execution)
└────────┘ └────────┘
   │         │
   └────┬────┘
        ▼
┌──────────────┐
│ PostgreSQL   │  (Replicated)
└──────────────┘
   │
   ▼
┌──────────────┐
│  S3 Storage  │  (Artifacts)
└──────────────┘
```

---

## Summary: Critical Data Paths

1. **Secret Storage**: Browser → API → Encrypt → DB (never reverse to browser)
2. **Workflow Execution**: API → Queue → Worker → LLM → Artifacts → DB
3. **Status Polling**: Browser → API → DB (2s interval, terminates on completion)
4. **Artifact Retrieval**: Browser → API → FS (or S3) → Stream response

**Next Steps:**
→ Review data flows for security vulnerabilities  
→ Identify bottlenecks for optimization  
→ Design caching strategy for workflow schemas  

---

**Approved By:** _[Pending Review]_  
**Date:** _[Pending]_
