"""Shared pytest fixtures for Smart Code Library API tests."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def mock_db():
    """Mock VectorMemoryStore."""
    return MagicMock()


@pytest.fixture
def mock_sandbox():
    """Mock SelfHealingSandbox."""
    return MagicMock()


@pytest.fixture
def mock_llm():
    """Mock chat LLM."""
    return MagicMock()


def _reload_main_with_patches(mock_db, mock_sandbox, mock_llm, *, startup_error=None):
    """Reload main with mocked constructors, then patch module-level singletons."""
    with (
        patch(
            "smart_code_lib.database.vector_store.VectorMemoryStore",
            return_value=mock_db,
        ),
        patch(
            "smart_code_lib.sandbox.code_runner.SelfHealingSandbox",
            return_value=mock_sandbox,
        ),
        patch("smart_code_lib.main.get_chat_llm", return_value=mock_llm),
        patch("smart_code_lib.main.get_api_key", return_value=None),
    ):
        import smart_code_lib.main as main

        importlib.reload(main)

    main.check_ollama_available = lambda: (True, "")

    if startup_error is not None:
        main.db = None
        main.sandbox = None
        main.llm = None
        main._startup_error = startup_error
    else:
        main.db = mock_db
        main.sandbox = mock_sandbox
        main.llm = mock_llm
        main._startup_error = None

    return main


@pytest.fixture
def mock_services(mock_db, mock_sandbox, mock_llm):
    """Patch db, sandbox, and llm at module level with a successful startup."""
    main = _reload_main_with_patches(mock_db, mock_sandbox, mock_llm)
    yield main, mock_db, mock_sandbox, mock_llm


@pytest.fixture
def client(mock_services):
    """FastAPI TestClient backed by mocked core services."""
    from fastapi.testclient import TestClient

    main, *_ = mock_services
    return TestClient(main.app)


@pytest.fixture
def client_ollama_down(mock_services):
    """TestClient where /health reports degraded Ollama."""
    from fastapi.testclient import TestClient

    main, *_ = mock_services
    main.check_ollama_available = lambda: (False, "Ollama is not reachable")
    return TestClient(main.app)


@pytest.fixture
def client_startup_failed(mock_db, mock_sandbox, mock_llm):
    """TestClient where core services failed to initialize."""
    from fastapi.testclient import TestClient

    main = _reload_main_with_patches(
        mock_db,
        mock_sandbox,
        mock_llm,
        startup_error="Ollama model 'qwen2.5-coder:7b' is not installed.",
    )
    return TestClient(main.app)