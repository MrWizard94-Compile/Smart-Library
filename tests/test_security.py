"""Security tests: payload limits, API key auth, and fail-closed sandbox."""

from unittest.mock import MagicMock, patch

import pytest

from smart_code_lib.sandbox.code_runner import DOCKER_UNAVAILABLE_MSG, SelfHealingSandbox


def test_oversized_code_returns_413(client, monkeypatch):
    """Execute-heal rejects code larger than MAX_CODE_BYTES."""
    monkeypatch.setenv("MAX_CODE_BYTES", "10")
    oversized = "x" * 20

    response = client.post("/execute-heal", json={"code": oversized})

    assert response.status_code == 413
    assert "maximum size" in response.json()["detail"]


def test_api_key_missing_returns_401(client, monkeypatch):
    """Protected endpoints return 401 when API_KEY is set and header is missing."""
    monkeypatch.setenv("API_KEY", "secret-key")

    response = client.post(
        "/seed",
        json={"content": "hello", "category": "test"},
    )

    assert response.status_code == 401
    assert "API key" in response.json()["detail"]


def test_api_key_wrong_returns_401(client, monkeypatch):
    """Wrong X-API-Key header returns 401."""
    monkeypatch.setenv("API_KEY", "secret-key")

    response = client.post(
        "/seed",
        json={"content": "hello", "category": "test"},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401


@patch("smart_code_lib.main.get_api_key", return_value="secret-key")
def test_api_key_correct_allows_write(mock_get_key, client, mock_services):
    """Valid X-API-Key permits protected write endpoints."""
    _, mock_db, _, _ = mock_services

    response = client.post(
        "/seed",
        json={"content": "hello", "category": "test"},
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == 200
    mock_db.insert_reference.assert_called_once()


@patch("smart_code_lib.sandbox.code_runner.get_sandbox_fail_closed", return_value=True)
@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_fail_closed_sandbox_message_when_docker_unavailable(
    mock_check, mock_llm, mock_fail_closed
):
    """SANDBOX_FAIL_CLOSED=true returns Docker unavailable without in-process fallback."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    docker_result = {
        "success": False,
        "stdout": "",
        "error_traceback": DOCKER_UNAVAILABLE_MSG,
    }

    with (
        patch.object(sandbox, "execute_in_docker", return_value=docker_result),
        patch.object(sandbox, "_execute_in_process") as mock_in_process,
    ):
        result = sandbox.safely_execute_python("print(1)")

    assert result["success"] is False
    assert "SANDBOX_FAIL_CLOSED=true" in result["error_traceback"]
    mock_in_process.assert_not_called()