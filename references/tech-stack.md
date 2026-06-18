# Smart Code Library — Tech Stack

Technology choices, pinned versions, and rationale from the implementation plan.

---

## Core Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Runtime** | Python | 3.11+ | Async support, modern typing, LangChain compatibility |
| **API Framework** | FastAPI | 0.110.0 | Async routing, automatic OpenAPI docs, Pydantic integration |
| **ASGI Server** | Uvicorn | 0.28.0 | Production-grade ASGI server for FastAPI |
| **LLM Orchestration** | LangChain | 0.1.11 | Document abstractions, vector store integrations |
| **OpenAI Integration** | langchain-openai | 0.0.8 | Embeddings + ChatOpenAI wrappers |
| **Validation** | Pydantic | 2.6.4 | Request/response models with strict typing |
| **Config** | python-dotenv | 1.0.1 | Load `OPENAI_API_KEY` from `.env` |

---

## AI Models

| Use Case | Model | Provider |
|----------|-------|----------|
| Embeddings | `text-embedding-3-small` | OpenAI |
| Query synthesis | `gpt-4o` | OpenAI |
| Self-healing fixes | `gpt-4o` (temperature=0) | OpenAI |

---

## Data & Memory

| Component | Technology | Role |
|-----------|------------|------|
| **Primary (dev)** | ChromaDB 0.4.24 | Local persistent vector store at `./.chroma_db` |
| **Alternative (scale)** | Qdrant v1.8.4 | Low-latency similarity search in Docker |
| **Metadata scale-out** | PostgreSQL + pgvector | Optional filtered metadata at scale |

### Collection Details (Chroma)

- Collection name: `smart_library_core`
- Embedding function: `OpenAIEmbeddings`
- Metadata fields: `category`, `language`

---

## Execution & Isolation

| Environment | Approach |
|-------------|----------|
| **Development** | In-process `exec()` with stdout capture |
| **Production target** | Docker-isolated sandbox containers |

The plan describes Docker execution for trapping stack traces safely; the initial codebase uses in-process execution for simplicity.

---

## Infrastructure

| Tool | Purpose |
|------|---------|
| **Docker Compose** | Multi-container orchestration (API + Qdrant) |
| **Git** | Version control; future hooks for auto-seeding docs |

### Docker Compose Services

```yaml
api_server   → FastAPI on port 8000
qdrant_db    → Qdrant on port 6333
```

Network: `code_net` (bridge)

---

## Known Inconsistencies

### ChromaDB vs Qdrant

| Aspect | Code (`vector_store.py`) | Infrastructure (`docker-compose.yml`) |
|--------|--------------------------|--------------------------------------|
| Vector DB | **ChromaDB** with local persistence | **Qdrant** container provisioned |
| Connection | `./.chroma_db` on disk | `qdrant_storage` volume, port 6333 |

**Impact:** Running `docker-compose up` starts Qdrant, but the application code does not connect to it unless refactored. Local dev uses Chroma exclusively.

**Resolution paths:**

1. Migrate `VectorMemoryStore` to Qdrant client for production parity
2. Remove Qdrant from compose until migration is complete
3. Support both via environment flag (`VECTOR_BACKEND=chroma|qdrant`)

### LangChain Community Import

The plan references `langchain_community.vectorstores.Chroma` but `requirements.txt` lists only `langchain` and `chromadb`. You may need `langchain-community` as an explicit dependency when implementing.

---

## Future / Planned

| Feature | Description |
|---------|-------------|
| Git sync hooks | Auto-post `.md`/`.json` changes to `/seed` on commit |
| Vector deduplication | Weekly cleanup of overlapping healing logs |
| pgvector | Metadata filtering at PostgreSQL scale |

---

## Full `requirements.txt` (Pinned)

```text
fastapi==0.110.0
uvicorn==0.28.0
langchain==0.1.11
langchain-openai==0.0.8
chromadb==0.4.24
pydantic==2.6.4
python-dotenv==1.0.1
```