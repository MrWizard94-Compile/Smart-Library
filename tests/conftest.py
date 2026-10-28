"""Shared pytest fixtures for Smart Code Library API tests."""

import importlib
import os
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


# --- Integration test hooks and fixtures (live Ollama) ---


def pytest_addoption(parser):
    """Register CLI flags for opt-in integration test runs."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require live Ollama",
    )
    parser.addoption(
        "--strict-integration",
        action="store_true",
        default=False,
        help="Fail (do not skip) integration tests when Ollama is unavailable",
    )


def _integration_explicitly_selected(config) -> bool:
    """Return True when the user opted into integration collection."""
    if config.getoption("--run-integration"):
        return True
    markexpr = config.getoption("-m", default="") or ""
    return "integration" in markexpr


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless explicitly selected."""
    if _integration_explicitly_selected(config):
        return

    skip_integration = pytest.mark.skip(
        reason=(
            "Integration tests skipped by default. "
            "Use -m integration --run-integration, -m integration_full, "
            "or scripts/run-integration-tests."
        )
    )
    for item in items:
        if item.get_closest_marker("integration") or item.get_closest_marker(
            "integration_full"
        ):
            item.add_marker(skip_integration)


@pytest.fixture(scope="session", autouse=True)
def ensure_project_env():
    """Load project .env and set cache paths before any test module imports."""
    from smart_code_lib.config import load_env

    load_env(force=True)
    os.environ.setdefault("HF_HOME", str(ROOT / ".hf_cache"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(ROOT / ".hf_cache"))


@pytest.fixture(scope="session")
def ollama_status():
    """Probe live Ollama availability once per session."""
    from smart_code_lib.llm.local_models import check_ollama_available

    return check_ollama_available()


@pytest.fixture
def require_live_ollama(request, ollama_status):
    """Skip or fail when Ollama is not reachable with the configured model."""
    ok, message = ollama_status
    if ok:
        return

    if request.config.getoption("--strict-integration"):
        pytest.fail(f"Ollama required but unavailable: {message}")
    pytest.skip(f"Ollama unavailable: {message}")


@pytest.fixture
def live_api_client(require_live_ollama, tmp_path):
    """TestClient backed by real LLM/embeddings and an isolated Chroma directory."""
    from fastapi.testclient import TestClient

    from smart_code_lib.database.vector_store import VectorMemoryStore

    persist_dir = str(tmp_path / "chroma_integration")
    real_cls = VectorMemoryStore

    class _TempVectorStore(real_cls):
        """Vector store that always writes to a per-test temp directory."""

        def __init__(self, persist_directory="./.chroma_db"):
            super().__init__(persist_directory=persist_dir)

    with patch("smart_code_lib.main.VectorMemoryStore", _TempVectorStore):
        import smart_code_lib.main as main

        importlib.reload(main)
        yield TestClient(main.app)