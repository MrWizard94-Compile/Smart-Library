"""Central configuration: project paths and environment variable loading."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
ENV_FILE: Path = PROJECT_ROOT / ".env"
_env_loaded: bool = False

_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
_DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_DEFAULT_MAX_CODE_BYTES = 65536

def load_env(*, force: bool = False) -> bool:
    global _env_loaded
    if _env_loaded and not force:
        return ENV_FILE.is_file()
    loaded = load_dotenv(ENV_FILE, override=False)
    _env_loaded = True
    return loaded

def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)

def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL)

def get_embedding_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL)


def get_max_code_bytes() -> int:
    """Maximum allowed code payload size in bytes (UTF-8 encoded)."""
    raw = os.getenv("MAX_CODE_BYTES", str(_DEFAULT_MAX_CODE_BYTES))
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_MAX_CODE_BYTES
    return max(value, 1)


def get_sandbox_fail_closed() -> bool:
    """When true, refuse in-process fallback if Docker sandbox is unavailable."""
    return os.getenv("SANDBOX_FAIL_CLOSED", "false").lower() in ("true", "1", "yes")


def get_api_key() -> str | None:
    """Optional write API key; None disables authentication."""
    key = os.getenv("API_KEY", "").strip()
    return key or None