"""Tests for smart_code_lib.sandbox.code_runner helpers and sandbox behavior."""

import json
from unittest.mock import MagicMock, patch

import pytest

from smart_code_lib.sandbox.code_runner import (
    DOCKER_UNAVAILABLE_MSG,
    SelfHealingSandbox,
    _parse_llm_json,
    _strip_markdown_fences,
)


def test_strip_markdown_fences_plain_json():
    """Plain JSON passes through unchanged."""
    raw = '{"fixed_code": "x=1"}'
    assert _strip_markdown_fences(raw) == raw


def test_strip_markdown_fences_json_fence():
    """```json fences are removed."""
    raw = '```json\n{"fixed_code": "x=1"}\n```'
    assert _strip_markdown_fences(raw) == '{"fixed_code": "x=1"}'


def test_strip_markdown_fences_generic_fence():
    """Generic ``` fences are removed."""
    raw = '```\nprint("hi")\n```'
    assert _strip_markdown_fences(raw) == 'print("hi")'


def test_strip_markdown_fences_stray_backticks():
    """Surrounding backticks without fences are stripped."""
    raw = '`{"fixed_code": "x=1"}`'
    assert _strip_markdown_fences(raw) == '{"fixed_code": "x=1"}'


def test_strip_markdown_fences_multiline_code_block():
    """Multi-line fenced blocks preserve inner newlines."""
    raw = '```\na = 1\nb = 2\n```'
    assert _strip_markdown_fences(raw) == "a = 1\nb = 2"


def test_parse_llm_json_valid():
    """Valid JSON dict is parsed."""
    content = '{"fixed_code": "x=1", "explanation": "added x"}'
    assert _parse_llm_json(content) == {"fixed_code": "x=1", "explanation": "added x"}


def test_parse_llm_json_fenced():
    """Fenced JSON is parsed after fence stripping."""
    content = '```json\n{"fixed_code": "y=2"}\n```'
    assert _parse_llm_json(content) == {"fixed_code": "y=2"}


def test_parse_llm_json_invalid_returns_none():
    """Invalid JSON returns None."""
    assert _parse_llm_json("not json at all") is None


@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(False, "down"))
def test_sandbox_init_raises_when_ollama_unavailable(mock_check):
    """Constructor refuses to start when Ollama check fails."""
    with pytest.raises(ValueError, match="down"):
        SelfHealingSandbox(vector_db=MagicMock())


@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_safely_execute_python_uses_docker_on_success(mock_check, mock_llm):
    """Docker path returns successful container output."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    docker_result = {"success": True, "stdout": "ok\n", "error_traceback": None}

    with patch.object(sandbox, "execute_in_docker", return_value=docker_result) as mock_docker:
        result = sandbox.safely_execute_python("print('ok')")

    assert result == docker_result
    mock_docker.assert_called_once()


@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_safely_execute_python_falls_back_when_docker_unavailable(mock_check, mock_llm):
    """In-process fallback runs when Docker is unavailable."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    docker_result = {
        "success": False,
        "stdout": "",
        "error_traceback": DOCKER_UNAVAILABLE_MSG,
    }

    with (
        patch.object(sandbox, "execute_in_docker", return_value=docker_result),
        patch.object(
            sandbox,
            "_execute_in_process",
            return_value={"success": True, "stdout": "fallback\n", "error_traceback": None},
        ) as mock_in_process,
    ):
        result = sandbox.safely_execute_python("print('ok')")

    assert result["success"] is True
    assert result["stdout"] == "fallback\n"
    mock_in_process.assert_called_once()


@patch("smart_code_lib.sandbox.code_runner.get_sandbox_fail_closed", return_value=True)
@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_safely_execute_python_fail_closed_blocks_fallback(mock_check, mock_llm, mock_fail_closed):
    """SANDBOX_FAIL_CLOSED prevents in-process fallback."""
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
        result = sandbox.safely_execute_python("print('ok')")

    assert result["success"] is False
    assert "SANDBOX_FAIL_CLOSED=true" in result["error_traceback"]
    mock_in_process.assert_not_called()


@patch.dict("os.environ", {"USE_DOCKER_SANDBOX": "false"})
@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_safely_execute_python_in_process_when_docker_disabled(mock_check, mock_llm):
    """USE_DOCKER_SANDBOX=false skips Docker entirely."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())

    with (
        patch.object(sandbox, "execute_in_docker") as mock_docker,
        patch.object(
            sandbox,
            "_execute_in_process",
            return_value={"success": True, "stdout": "direct\n", "error_traceback": None},
        ) as mock_in_process,
    ):
        result = sandbox.safely_execute_python("print('ok')")

    assert result["stdout"] == "direct\n"
    mock_docker.assert_not_called()
    mock_in_process.assert_called_once()


@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_heal_and_verify_success_first_attempt(mock_check, mock_llm):
    """Healing returns immediately when first execution succeeds."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    sandbox.llm = MagicMock()

    with patch.object(
        sandbox,
        "safely_execute_python",
        return_value={"success": True, "stdout": "done\n", "error_traceback": None},
    ):
        report = sandbox.heal_and_verify("print('done')")

    assert report["status"] == "Healed"
    assert report["attempts"] == 1
    sandbox.llm.invoke.assert_not_called()


@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_heal_and_verify_repairs_then_succeeds(mock_check, mock_llm):
    """LLM fix is applied and retried until execution succeeds."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = MagicMock(
        content=json.dumps({"fixed_code": "print('fixed')", "explanation": "defined var"})
    )
    sandbox.llm = mock_llm_instance
    sandbox.db = MagicMock()

    outcomes = [
        {"success": False, "stdout": "", "error_traceback": "NameError"},
        {"success": True, "stdout": "fixed\n", "error_traceback": None},
    ]

    with patch.object(sandbox, "safely_execute_python", side_effect=outcomes):
        report = sandbox.heal_and_verify("print(greeting)")

    assert report["status"] == "Healed"
    assert report["code"] == "print('fixed')"
    assert report["attempts"] == 2
    sandbox.db.insert_reference.assert_called_once()


@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_heal_and_verify_fails_on_invalid_llm_json(mock_check, mock_llm):
    """Invalid LLM JSON stops healing with parse_error."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = MagicMock(content="not valid json")
    sandbox.llm = mock_llm_instance

    with patch.object(
        sandbox,
        "safely_execute_python",
        return_value={"success": False, "stdout": "", "error_traceback": "SyntaxError"},
    ):
        report = sandbox.heal_and_verify("bad code")

    assert report["status"] == "Failed"
    assert "parse_error" in report


@patch("smart_code_lib.sandbox.code_runner.get_chat_llm")
@patch("smart_code_lib.sandbox.code_runner.check_ollama_available", return_value=(True, ""))
def test_heal_and_verify_exhausts_max_attempts(mock_check, mock_llm):
    """Healing fails after max_attempts without a successful run."""
    sandbox = SelfHealingSandbox(vector_db=MagicMock())
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = MagicMock(
        content=json.dumps({"fixed_code": "still broken", "explanation": "noop"})
    )
    sandbox.llm = mock_llm_instance
    sandbox.db = MagicMock()

    with patch.object(
        sandbox,
        "safely_execute_python",
        return_value={"success": False, "stdout": "", "error_traceback": "still failing"},
    ):
        report = sandbox.heal_and_verify("broken", max_attempts=2)

    assert report["status"] == "Failed"
    assert report["attempts"] == 2