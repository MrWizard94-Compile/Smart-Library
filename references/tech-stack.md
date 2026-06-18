# Smart Code Library — Tech Stack

Technology choices, versions, and rationale. **All inference runs locally — no cloud API keys.**

---

## Core Stack

| Layer | Technology | Version | Role |
|-------|-----------|---------|------|
| **API** | FastAPI | 0.110.0 | Async HTTP gateway |
| **Server** | Uvicorn | 0.28.0 | ASGI server |
| **Orchestration** | LangChain | 0.1.11 | Prompt chains, document handling |
| **Community integrations** | langchain-community | 0.0.27 | Ollama + HuggingFace wrappers |
| **Vector DB** | ChromaDB | 0.4.24 | Local semantic search |
| **Validation** | Pydantic | 2.6.4 | Request/response schemas |
| **Config** | python-dotenv | 1.0.1 | Optional `.env` overrides |

---

## Local Models (No API Keys)

| Purpose | Model | Provider |
|---------|-------|----------|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace (runs on CPU) |
| Query synthesis | `qwen2.5-coder:7b` (configurable) | Ollama |
| Self-healing fixes | `qwen2.5-coder:7b` (temperature=0) | Ollama |

Configure via environment variables:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Infrastructure

| Component | Technology | Notes |
|-----------|-----------|-------|
| **LLM runtime** | Ollama | Included in `docker-compose.yml` |
| **Code sandbox** | Docker (`python:3.11-slim`) | Isolated execution, no network |
| **Future vector scale** | Qdrant | In compose but not wired in code yet |

### Chroma vs Qdrant

- **Current:** ChromaDB with local HuggingFace embeddings (`./.chroma_db`)
- **Compose:** Qdrant service is provisioned for future migration
- **Action:** Use Chroma for all current development

---

## Dependencies (`requirements.txt`)

```text
fastapi==0.110.0
uvicorn==0.28.0
langchain==0.1.11
langchain-community==0.0.27
chromadb==0.4.24
pydantic==2.6.4
python-dotenv==1.0.1
sentence-transformers>=2.2.0
```