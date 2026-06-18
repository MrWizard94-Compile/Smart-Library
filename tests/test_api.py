"""API integration tests for smart_code_lib.main (mocked, no live API keys)."""

import importlib
from unittest.mock import MagicMock, patch

import pytest


def test_health_ok(client):
    """Health returns ok when startup succeeds."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_degraded():
    """Health returns degraded when module startup fails."""
    with patch(
        "smart_code_lib.database.vector_store.VectorMemoryStore",
        side_effect=ValueError("startup failed"),
    ):
        import smart_code_lib.main as main

        importlib.reload(main)

    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["detail"] == "startup failed"


def test_seed_endpoint(client, mock_services):
    """Seed indexes reference content via VectorMemoryStore.insert_reference."""
    _, mock_db, _, _ = mock_services
    payload = {
        "content": "def hello(): return 'world'",
        "category": "snippets",
        "language": "Python",
    }

    response = client.post("/seed", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Data indexed accurately."}
    mock_db.insert_reference.assert_called_once_with(
        payload["content"],
        payload["category"],
        payload["language"],
    )


def test_query_endpoint(client, mock_services):
    """Query retrieves context and invokes the LLM."""
    _, mock_db, _, mock_llm = mock_services
    mock_db.query_context.return_value = "[snippets]: sample context"
    mock_llm.invoke.return_value = MagicMock(content="Generated implementation")

    response = client.post("/query", json={"query": "hello world example"})

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Generated implementation"
    assert data["referenced_context"] == "[snippets]: sample context"
    mock_db.query_context.assert_called_once_with("hello world example")
    mock_llm.invoke.assert_called_once()


def test_execute_heal_endpoint(client, mock_services):
    """Execute-heal delegates to sandbox.heal_and_verify."""
    _, _, mock_sandbox, _ = mock_services
    heal_report = {
        "status": "Healed",
        "code": "print('ok')",
        "attempts": 1,
        "stdout": "ok\n",
    }
    mock_sandbox.heal_and_verify.return_value = heal_report

    response = client.post("/execute-heal", json={"code": "print('ok')"})

    assert response.status_code == 200
    assert response.json() == {"report": heal_report}
    mock_sandbox.heal_and_verify.assert_called_once_with("print('ok')")


def test_deduplicate_endpoint(client, mock_services):
    """Maintenance deduplicate returns vector store stats."""
    _, mock_db, _, _ = mock_services
    mock_db.deduplicate.return_value = {"removed": 2, "kept": 10, "dry_run": True}

    response = client.post("/maintenance/deduplicate?dry_run=true&threshold=0.9")

    assert response.status_code == 200
    assert response.json() == {"removed": 2, "kept": 10, "dry_run": True}
    mock_db.deduplicate.assert_called_once_with(similarity_threshold=0.9, dry_run=True)