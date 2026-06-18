# Smart Code Library — Local Development Setup

Step-by-step guide to run the Smart Code Library API on your machine.

---

## Prerequisites

| Requirement | Version / Notes |
|-------------|-----------------|
| **Python** | 3.11 or newer |
| **OpenAI API key** | Required for embeddings (`text-embedding-3-small`) and chat (`gpt-4o`) |
| **Git** | For cloning and version control |
| **Docker** (optional) | Only needed for `docker-compose` deployment with Qdrant |

---

## 1. Clone the Repository

```bash
git clone https://github.com/MrWizard94-Compile/Smart-Library.git
cd Smart-Library
```

---

## 2. Create a Virtual Environment

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

## 3. Install Dependencies

From the project root (once `smart_code_lib/requirements.txt` exists):

```bash
pip install -r smart_code_lib/requirements.txt
```

Expected packages:

- `fastapi==0.110.0`
- `uvicorn==0.28.0`
- `langchain==0.1.11`
- `langchain-openai==0.0.8`
- `chromadb==0.4.24`
- `pydantic==2.6.4`
- `python-dotenv==1.0.1`

---

## 4. Configure Environment Variables

Copy the example env file and add your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

> **Never commit `.env`** — it is listed in `.gitignore`.

---

## 5. Run the API Server

From the `smart_code_lib` directory (or project root, depending on layout):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server starts at **http://localhost:8000**.

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 6. Verify Installation

**Health check via seed:**

```bash
curl -X POST http://localhost:8000/seed \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello Smart Library", "category": "Test", "language": "Python"}'
```

**Query:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What test content was seeded?"}'
```

---

## 7. Docker Compose (Optional)

For containerized deployment with Qdrant:

```bash
export OPENAI_API_KEY=sk-your-key   # or set in .env for compose
docker-compose up --build
```

API will be available on port `8000`; Qdrant on port `6333`.

> **Note:** The reference implementation uses ChromaDB locally. Docker Compose includes Qdrant for production-style deployments — see `references/tech-stack.md` for the Chroma vs Qdrant inconsistency.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `OPENAI_API_KEY` not set | Ensure `.env` exists and is loaded; restart uvicorn |
| Chroma permission errors | Check write access to `./.chroma_db` |
| Port 8000 in use | Use `--port 8001` or stop conflicting process |
| Import errors | Confirm venv is active and dependencies installed |

---

## Directory Created at Runtime

| Path | Purpose |
|------|---------|
| `.chroma_db/` | Persistent Chroma vector store (gitignored) |
| `qdrant_storage/` | Qdrant data when using Docker Compose (gitignored) |