"""Local model providers: HuggingFace embeddings + Ollama chat."""

import json
import urllib.error
import urllib.request

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

from smart_code_lib.config import (
    get_embedding_model_name,
    get_ollama_base_url,
    get_ollama_model,
)

__all__ = [
    "check_ollama_available",
    "get_chat_llm",
    "get_embedding_model_name",
    "get_embeddings",
    "get_ollama_base_url",
    "get_ollama_model",
]


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a local sentence-transformers embedding model."""
    return HuggingFaceEmbeddings(
        model_name=get_embedding_model_name(),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_chat_llm() -> ChatOllama:
    """Return a local Ollama chat model."""
    return ChatOllama(
        model=get_ollama_model(),
        base_url=get_ollama_base_url(),
        temperature=0,
    )


def _model_is_available(requested: str, installed_names: set[str]) -> bool:
    """Match full tag (e.g. qwen2.5-coder:7b) or base name (qwen2.5-coder)."""
    if requested in installed_names:
        return True
    base = requested.split(":")[0]
    return base in {name.split(":")[0] for name in installed_names}


def check_ollama_available() -> tuple[bool, str]:
    """
    Verify Ollama is reachable and the configured model is available.

    Returns:
        (ok, message) — message is empty when ok, otherwise an actionable error.
    """
    base_url = get_ollama_base_url()
    model = get_ollama_model()
    tags_url = f"{base_url.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return (
            False,
            f"Ollama is not reachable at {base_url}. "
            f"Install Ollama (https://ollama.com) and run `ollama serve`, "
            f"or start the ollama service via docker compose. ({exc})",
        )
    except (json.JSONDecodeError, TimeoutError, OSError) as exc:
        return False, f"Failed to query Ollama at {base_url}: {exc}"

    models = payload.get("models") or []
    installed_names = {m.get("name", "") for m in models}

    if not _model_is_available(model, installed_names):
        return (
            False,
            f"Ollama model '{model}' is not installed. "
            f"Run: ollama pull {model}",
        )

    return True, ""