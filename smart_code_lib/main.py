"""FastAPI gateway for the Smart Code Library core engine."""

from smart_code_lib.config import load_env

load_env()

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from smart_code_lib.config import get_api_key, get_max_code_bytes
from smart_code_lib.database.vector_store import VectorMemoryStore
from smart_code_lib.llm.local_models import (
    check_ollama_available,
    get_chat_llm,
    get_embedding_model_name,
    get_ollama_model,
)
from smart_code_lib.sandbox.code_runner import SelfHealingSandbox

app = FastAPI(title="Smart Code Library API", version="1.0.0")

try:
    db = VectorMemoryStore()
    llm = get_chat_llm()
    sandbox = SelfHealingSandbox(vector_db=db)
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


def _validate_code_size(code: str) -> None:
    """Raise HTTP 413 if code exceeds MAX_CODE_BYTES."""
    encoded = code.encode("utf-8")
    limit = get_max_code_bytes()
    if len(encoded) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"Code payload exceeds maximum size of {limit} bytes.",
        )


def require_write_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Require X-API-Key header when API_KEY is configured."""
    expected = get_api_key()
    if expected is None:
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@app.get("/health")
async def health_check():
    """Liveness probe for deployment and monitoring."""
    if _startup_error:
        return {"status": "degraded", "detail": _startup_error}

    ollama_ok, ollama_msg = check_ollama_available()
    if not ollama_ok:
        return {"status": "degraded", "detail": ollama_msg}

    return {
        "status": "ok",
        "llm": f"ollama/{get_ollama_model()}",
        "embeddings": get_embedding_model_name(),
    }


@app.post("/seed")
async def seed_data(
    payload: SeedingRequest,
    _: None = Depends(require_write_api_key),
):
    """Index reference content into the vector memory store."""
    _ensure_ready()
    _validate_code_size(payload.content)
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
async def run_and_heal(
    payload: CodeRunRequest,
    _: None = Depends(require_write_api_key),
):
    """Execute Python code in the self-healing sandbox."""
    _ensure_ready()
    _validate_code_size(payload.code)
    execution_report = sandbox.heal_and_verify(payload.code)
    return {"report": execution_report}


@app.post("/maintenance/deduplicate")
async def deduplicate_vectors(
    dry_run: bool = True,
    threshold: float = 0.95,
    _: None = Depends(require_write_api_key),
):
    """Remove exact and near-duplicate documents from the vector store."""
    _ensure_ready()
    return db.deduplicate(similarity_threshold=threshold, dry_run=dry_run)