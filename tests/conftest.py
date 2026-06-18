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

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")


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
        patch("smart_code_lib.main.ChatOpenAI", return_value=mock_llm),
    ):
        import smart_code_lib.main as main

        importlib.reload(main)

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
def mock_services():
    """Patch db, sandbox, and llm at module level with a successful startup."""
    mock_db = MagicMock()
    mock_sandbox = MagicMock()
    mock_llm = MagicMock()
    main = _reload_main_with_patches(mock_db, mock_sandbox, mock_llm)
    yield main, mock_db, mock_sandbox, mock_llm


@pytest.fixture
def client(mock_services):
    """FastAPI TestClient backed by mocked core services."""
    from fastapi.testclient import TestClient

    main, *_ = mock_services
    return TestClient(main.app)