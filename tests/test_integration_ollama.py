"""Live Ollama integration smoke tests (opt-in; excluded from default CI)."""

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import pytest

from smart_code_lib.llm.local_models import get_chat_llm


def _integration_llm_timeout() -> int:
    raw = os.getenv("INTEGRATION_LLM_TIMEOUT", "120")
    try:
        return max(int(raw), 1)
    except ValueError:
        return 120


def _invoke_llm_with_timeout(llm, prompt: str):
    """Invoke the chat LLM with a hard timeout to avoid hanging CI/dev runs."""
    timeout = _integration_llm_timeout()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(llm.invoke, prompt)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            raise AssertionError(
                f"LLM invoke timed out after {timeout}s"
            ) from exc


@pytest.mark.integration
def test_ollama_status_reports_ready(require_live_ollama, ollama_status):
    """Configured Ollama endpoint and model are reachable."""
    ok, message = ollama_status
    assert ok is True
    assert message == ""


@pytest.mark.integration
def test_chat_llm_invoke_returns_content(require_live_ollama):
    """Chat model returns non-empty content for a minimal prompt."""
    llm = get_chat_llm()
    response = _invoke_llm_with_timeout(
        llm,
        "Reply with exactly the word OK and nothing else.",
    )
    content = getattr(response, "content", "") or ""
    assert content.strip()


@pytest.mark.integration
def test_live_health_endpoint_ok(live_api_client):
    """Live API /health reports ok when Ollama and startup succeed."""
    response = live_api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm"].startswith("ollama/")
    assert "embeddings" in body


@pytest.mark.integration_full
def test_live_seed_indexes_content(live_api_client):
    """POST /seed indexes reference content against live embeddings."""
    payload = {
        "content": "def integration_smoke(): return 42",
        "category": "IntegrationSmoke",
        "language": "Python",
    }
    response = live_api_client.post("/seed", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Data indexed accurately."


@pytest.mark.integration_full
def test_live_query_returns_llm_response(live_api_client):
    """POST /query runs retrieval and live Ollama generation end-to-end."""
    seed_payload = {
        "content": "def greet(name): return f'hello {name}'",
        "category": "IntegrationSmoke",
        "language": "Python",
    }
    seed_response = live_api_client.post("/seed", json=seed_payload)
    assert seed_response.status_code == 200

    timeout = _integration_llm_timeout()
    query_response = live_api_client.post(
        "/query",
        json={"query": "Show a short Python greet function example."},
        timeout=timeout,
    )
    assert query_response.status_code == 200
    body = query_response.json()
    assert body["response"].strip()
    assert "referenced_context" in body