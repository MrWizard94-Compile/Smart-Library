# Smart Code Library — Local Development Setup

Step-by-step guide to run the Smart Code Library API on your machine using **local models only** — no cloud API keys required.

---

## Prerequisites

| Requirement | Version / Notes |
|-------------|-----------------|
| **Python** | 3.11 or newer |
| **Ollama** | Local LLM runtime — [https://ollama.com](https://ollama.com) |
| **Git** | For cloning and version control |
| **Docker** (optional) | For sandbox code execution and `docker compose` deployment |

---

## 1. Clone the Repository

```bash
git clone https://github.com/MrWizard94-Compile/Smart-Library.git
cd Smart-Library
```

---

## 2. Install Ollama and Pull the Model

**Windows / macOS / Linux:** Install Ollama from [https://ollama.com](https://ollama.com), then:

```powershell
# Windows
.\scripts\setup-ollama.ps1
```

```bash
# macOS / Linux
./scripts/setup-ollama.sh
```

This pulls `qwen2.5-coder:7b` by default. Override with `OLLAMA_MODEL` in `.env`.

---

## 3. Create a Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 4. Install Dependencies

```bash
pip install -r smart_code_lib/requirements.txt
```

On first run, the embedding model (`all-MiniLM-L6-v2`) downloads automatically (~90 MB).

---

## 5. Configure Environment (Optional)

Copy the example env file for overrides:

```bash
cp .env.example .env
```

Default values (no API keys needed):

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
USE_DOCKER_SANDBOX=true
```

---

## 6. Run the API Server

```powershell
# Windows
.\scripts\run-dev.ps1
```

```bash
# macOS / Linux
./scripts/run-dev.sh
```

The server starts at **http://localhost:8000**.

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## 7. Verify Installation

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/seed \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello Smart Library", "category": "Test", "language": "Python"}'
```

---

## 8. Docker Compose (Optional)

Runs API + Ollama + Qdrant (future) together:

```bash
docker compose up --build
```

After Ollama starts, pull the model inside the container:

```bash
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not reachable | Run `ollama serve` or start Ollama Desktop |
| Model not installed | Run `ollama pull qwen2.5-coder:7b` or `.\scripts\setup-ollama.ps1` |
| Chroma permission errors | Check write access to `./.chroma_db` |
| Docker sandbox unavailable | Set `USE_DOCKER_SANDBOX=false` in `.env` for in-process fallback |
| Port 8000 in use | Use `--port 8001` or stop conflicting process |

---

## Runtime Directories

| Path | Purpose |
|------|---------|
| `.chroma_db/` | Persistent Chroma vector store (gitignored) |
| `.hf_cache/` | HuggingFace embedding model cache (gitignored) |
| `qdrant_storage/` | Qdrant data when using Docker Compose (gitignored) |