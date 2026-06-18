# Smart Code Library — Architecture Overview

The Smart Code Library is a self-healing, semantic code reference platform. It separates **data lookup** (vector memory) from **code execution** (sandbox), enabling fast retrieval and safe runtime evaluation with automatic error recovery.

## High-Level Component Diagram

```mermaid
flowchart TB
    subgraph Client["User Interface / IDE"]
        UI[Client]
    end

    subgraph API["Core API Engine (FastAPI)"]
        ORCH[Orchestrator]
        SEED["/seed"]
        QUERY["/query"]
        HEAL["/execute-heal"]
    end

    subgraph Memory["Memory Layer"]
        VDB[(ChromaDB / Qdrant)]
        PG[(PostgreSQL + pgvector — optional scale)]
    end

    subgraph Sandbox["Sandbox Layer"]
        RUN[Code Runner]
        HEAL_LOOP[heal_and_verify Loop]
        LLM[OpenAI GPT-4o]
    end

    UI --> ORCH
    ORCH --> SEED
    ORCH --> QUERY
    ORCH --> HEAL
    SEED --> VDB
    QUERY --> VDB
    QUERY --> LLM
    HEAL --> RUN
    HEAL --> HEAL_LOOP
    HEAL_LOOP --> LLM
    HEAL_LOOP --> VDB
```

## ASCII Overview

```
┌────────────────────────┐
│   User Interface / IDE │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     Core API Engine    │◀───▶ [Vector Cache Engine]
└───────────┬────────────┘
            │
┌───────────┴────────────┐
▼                        ▼
┌───────────────┐        ┌───────────────┐
│ Memory Layer  │        │ Sandbox Layer │
│ (Chroma /     │        │ (Docker /     │
│ Postgres)     │        │ In-process)   │
└───────────────┘        └───────────────┘
```

## Components

### 1. Orchestrator (`main.py`)

The FastAPI application coordinates all requests:

- **Async routing** for `/seed`, `/query`, and `/execute-heal`
- Wires together `VectorMemoryStore` and `SelfHealingSandbox`
- Uses LangChain `ChatOpenAI` for query synthesis and healing prompts

### 2. Memory Layer (`database/vector_store.py`)

- **VectorMemoryStore** wraps ChromaDB with OpenAI `text-embedding-3-small` embeddings
- Persists to `./.chroma_db`
- Supports `insert_reference()` and `query_context()` with category/language metadata
- Optional production path: Qdrant or PostgreSQL with `pgvector` for metadata filtering at scale

### 3. Sandbox Layer (`sandbox/code_runner.py`)

- **SelfHealingSandbox** executes Python in an isolated `exec()` context with captured stdout
- On failure, invokes GPT-4o to produce JSON with `fixed_code` and `explanation`
- Successful patches are written back to the vector store as `"Self-Healing Patch"` entries
- Production target: Docker-isolated containers for stronger isolation

## Request Flows

| Endpoint | Flow |
|----------|------|
| `POST /seed` | Client → Orchestrator → VectorMemoryStore → ChromaDB |
| `POST /query` | Client → Orchestrator → similarity search → LLM answer with context |
| `POST /execute-heal` | Client → Sandbox execute → (on error) LLM fix loop → optional vector write-back |

## Project Layout

```text
smart_code_lib/
├── main.py
├── database/
│   ├── __init__.py
│   └── vector_store.py
├── sandbox/
│   ├── __init__.py
│   └── code_runner.py
└── requirements.txt
```

## Design Principles

1. **Separation of concerns** — Retrieval and execution are independent subsystems.
2. **Self-improvement** — Failed runs that get fixed enrich the library for future queries.
3. **Low latency** — Local Chroma persistence avoids network round-trips in development.
4. **Production readiness** — Docker Compose bundles API + Qdrant for containerized deployment.