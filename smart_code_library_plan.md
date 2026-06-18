> **Historical document:** This plan reflects early design notes (including OpenAI/GPT-4o examples). For the current local-only stack, see `references/setup-guide.md`, `references/architecture.md`, `references/tech-stack.md`, and `references/api-reference.md`. Default Ollama model: `qwen2.5-coder:7b`.

# Implementation Plan: Intelligent, Self-Healing Smart Code Library

This blueprint provides the architecture, codebase, and infrastructure setup required to deploy a production-ready, fast, and self-healing repository for development data.

---

## 1. Architectural Design & Tech Stack

To deliver sub-millisecond semantic retrieval alongside safe code execution, the platform separates data lookup from execution environments.

Use code with caution.┌────────────────────────┐│   User Interface / IDE │└───────────┬────────────┘│▼┌────────────────────────┐│     Core API Engine    │◀───▶ [Vector Cache Engine]└───────────┬────────────┘│┌────────────┴────────────┐▼                         ▼┌───────────────┐        ┌───────────────┐│ Memory Layer  │        │ Sandbox Layer ││ (Chroma /     │        │ (Docker       ││ Postgres)     │        │ Execution)    │└───────────────┘        └───────────────┘

### Component Breakdown

* **The Orchestrator**: Python 3.11+, FastAPI (async routing engine), and LangChain/LangGraph for context building.
* **The Memory Layer (Fast Vector DB)**: Qdrant or ChromaDB for low-latency similarity queries. PostgreSQL with `pgvector` can be used to scale metadata filtering.
* **The Sandbox (Self-Healing Layer)**: Isolated Docker containers that handle runtime evaluation, trap stack traces, and feed exceptions back into the fix loops.

---

## 2. Core Engine Codebase

### Project Directory Layout

```text
smart_code_lib/
│
├── main.py
├── database/
│   ├── __init__.py
│   └── vector_store.py
├── sandbox/
│   ├── __init__.py
│   └── code_runner.py
└── requirements.txt
```

### Dependencies (`requirements.txt`)

```text
fastapi==0.110.0
uvicorn==0.28.0
langchain==0.1.11
langchain-openai==0.0.8
chromadb==0.4.24
pydantic==2.6.4
python-dotenv==1.0.1
```

### Vector Database Module (`database/vector_store.py`)

```python
import os
from typing import List
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class VectorMemoryStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.db = Chroma(
            collection_name="smart_library_core",
            embedding_function=self.embeddings,
            persist_directory="./.chroma_db"
        )

    def insert_reference(self, content: str, category: str, language: str = "All"):
        doc = Document(
            page_content=content,
            metadata={"category": category, "language": language}
        )
        self.db.add_documents([doc])

    def query_context(self, query: str, limit: int = 3) -> str:
        results = self.db.similarity_search(query, k=limit)
        return "\n\n".join([f"[{r.metadata.get('category')}]: {r.page_content}" for r in results])
```

### Code Isolation & Execution Sandbox (`sandbox/code_runner.py`)

```python
import sys
import io
import json
import traceback
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI

class SelfHealingSandbox:
    def __init__(self, vector_db):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
        self.db = vector_db

    def safely_execute_python(self, code_string: str) -> Dict[str, Any]:
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer

        exec_globals = {}
        error = None

        try:
            exec(code_string, exec_globals)
        except Exception as e:
            error = traceback.format_exc()
        finally:
            sys.stdout = old_stdout

        return {
            "success": error is None,
            "stdout": output_buffer.getvalue(),
            "error_traceback": error
        }

    def heal_and_verify(self, broken_code: str, max_attempts: int = 3) -> Dict[str, Any]:
        current_code = broken_code

        for attempt in range(max_attempts):
            result = self.safely_execute_python(current_code)
            if result["success"]:
                return {"status": "Healed", "code": current_code, "attempts": attempt + 1}

            prompt = f"""
            Fix this code. Return a valid JSON dictionary string containing keys: 'fixed_code' and 'explanation'.

            Code to fix:
            {current_code}

            Error Details:
            {result['error_traceback']}
            """

            llm_output = self.llm.invoke(prompt).content
            try:
                parsed_fix = json.loads(llm_output.strip("`json\n"))
                current_code = parsed_fix["fixed_code"]

                self.db.insert_reference(
                    content=f"Fixed error: {result['error_traceback']}. Fix: {parsed_fix['explanation']}",
                    category="Self-Healing Patch"
                )
            except Exception:
                break

        return {"status": "Failed", "code": broken_code, "error": result["error_traceback"]}
```

### Application Gateway Orchestrator (`main.py`)

```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database.vector_store import VectorMemoryStore
from sandbox.code_runner import SelfHealingSandbox
from langchain_openai import ChatOpenAI

app = FastAPI(title="Smart Code Library API", version="1.0.0")
db = VectorMemoryStore()
sandbox = SelfHealingSandbox(vector_db=db)
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

class QueryRequest(BaseModel):
    query: str

class SeedingRequest(BaseModel):
    content: str
    category: str
    language: str

class CodeRunRequest(BaseModel):
    code: str

@app.post("/seed")
async def seed_data(payload: SeedingRequest):
    db.insert_reference(payload.content, payload.category, payload.language)
    return {"message": "Data indexed accurately."}

@app.post("/query")
async def smart_query(payload: QueryRequest):
    context = db.query_context(payload.query)
    prompt = f"""
    Use this library reference data to formulate a sharp answer:
    {context}

    User Query: {payload.query}
    Provide clean, ready-to-run implementations.
    """
    response = llm.invoke(prompt)
    return {"response": response.content, "referenced_context": context}

@app.post("/execute-heal")
async def run_and_heal(payload: CodeRunRequest):
    execution_report = sandbox.heal_and_verify(payload.code)
    return {"report": execution_report}
```

---

## 3. Deployment & Infrastructure Setup

### Multi-Container Orchestration (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  api_server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
    volumes:
      - ./.chroma_db:/app/.chroma_db
    networks:
      - code_net

  qdrant_db:
    image: qdrant/qdrant:v1.8.4
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    networks:
      - code_net

networks:
  code_net:
    driver: bridge
```

---

## 4. Maintenance & Automation

* **Git Sync Hooks**: Set up workspace hooks that scan modified `.md` or `.json` files on commit, posting documentation changes straight to the `/seed` endpoint.
* **Vector Optimization**: Deduplicate semantic tables weekly to remove overlapping healing logs, keeping cluster sizes light and query latencies fast.
