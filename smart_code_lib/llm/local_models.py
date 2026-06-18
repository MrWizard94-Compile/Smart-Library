"""Local model providers: HuggingFace embeddings + Ollama chat."""

import json
import os
import urllib.error
import urllib.request

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a local sentence-transformers embedding model."""
    return HuggingFaceEmbeddings(
        model_name=DEFAULT_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_chat_llm() -> ChatOllama:
    """Return a local Ollama chat model."""
    return ChatOllama(
        model=DEFAULT_OLLAMA_MODEL,
        base_url=DEFAULT_OLLAMA_BASE_URL,
        temperature=0,
    )


def check_ollama_available() -> tuple[bool, str]:
    """
    Verify Ollama is reachable and the configured model is available.

    Returns:
        (ok, message) — message is empty when ok, otherwise an actionable error.
    """
    tags_url = f"{DEFAULT_OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return (
            False,
            f"Ollama is not reachable at {DEFAULT_OLLAMA_BASE_URL}. "
            f"Install Ollama (https://ollama.com) and run `ollama serve`, "
            f"or start the ollama service via docker compose. ({exc})",
        )
    except (json.JSONDecodeError, TimeoutError, OSError) as exc:
        return False, f"Failed to query Ollama at {DEFAULT_OLLAMA_BASE_URL}: {exc}"

    models = payload.get("models") or []
    available_names = {m.get("name", "").split(":")[0] for m in models}
    target = DEFAULT_OLLAMA_MODEL.split(":")[0]

    if target not in available_names:
        return (
            False,
            f"Ollama model '{DEFAULT_OLLAMA_MODEL}' is not installed. "
            f"Run: ollama pull {DEFAULT_OLLAMA_MODEL}",
        )

    return True, ""