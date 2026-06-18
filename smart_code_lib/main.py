"""FastAPI gateway for the Smart Code Library core engine."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from smart_code_lib.database.vector_store import VectorMemoryStore
from smart_code_lib.sandbox.code_runner import SelfHealingSandbox

load_dotenv()

app = FastAPI(title="Smart Code Library API", version="1.0.0")

try:
    db = VectorMemoryStore()
    sandbox = SelfHealingSandbox(vector_db=db)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
except ValueError as exc:
    db = None
    sandbox = None
    llm = None
    _startup_error = str(exc)
else:
    _startup_error = None


class QueryRequest(BaseModel):
    """Request body for semantic library queries."""

    query: str


class SeedingRequest(BaseModel):
    """Request body for seeding reference content into the vector store."""

    content: str
    category: str
    language: str = "All"


class CodeRunRequest(BaseModel):
    """Request body for execute-and-heal sandbox runs."""

    code: str


def _ensure_ready() -> None:
    """Raise HTTP 503 if core services failed to initialize."""
    if _startup_error:
        raise HTTPException(status_code=503, detail=_startup_error)


@app.get("/health")
async def health_check():
    """Liveness probe for deployment and monitoring."""
    if _startup_error:
        return {"status": "degraded", "detail": _startup_error}
    return {"status": "ok"}


@app.post("/seed")
async def seed_data(payload: SeedingRequest):
    """Index reference content into the vector memory store."""
    _ensure_ready()
    db.insert_reference(payload.content, payload.category, payload.language)
    return {"message": "Data indexed accurately."}


@app.post("/query")
async def smart_query(payload: QueryRequest):
    """Retrieve relevant context and generate an implementation-focused answer."""
    _ensure_ready()
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
    """Execute Python code in the self-healing sandbox."""
    _ensure_ready()
    execution_report = sandbox.heal_and_verify(payload.code)
    return {"report": execution_report}


@app.post("/maintenance/deduplicate")
async def deduplicate_vectors(dry_run: bool = True, threshold: float = 0.95):
    """Remove exact and near-duplicate documents from the vector store."""
    _ensure_ready()
    return db.deduplicate(similarity_threshold=threshold, dry_run=dry_run)