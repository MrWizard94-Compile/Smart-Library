"""Local LLM and embedding providers (no cloud API keys)."""

from smart_code_lib.llm.local_models import (
    check_ollama_available,
    get_chat_llm,
    get_embeddings,
)

__all__ = ["check_ollama_available", "get_chat_llm", "get_embeddings"]