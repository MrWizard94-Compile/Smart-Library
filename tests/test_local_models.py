"""Tests for smart_code_lib.llm.local_models (mocked urllib, no live Ollama)."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from smart_code_lib.llm import local_models


def test_model_is_available_exact_tag_match():
    """Full model tag matches installed name."""
    installed = {"qwen2.5-coder:7b", "llama3:8b"}
    assert local_models._model_is_available("qwen2.5-coder:7b", installed) is True


def test_model_is_available_base_name_match():
    """Base name matches when tag differs."""
    installed = {"qwen2.5-coder:latest"}
    assert local_models._model_is_available("qwen2.5-coder:7b", installed) is True


def test_model_is_available_no_match():
    """Unknown model is not available."""
    installed = {"llama3:8b"}
    assert local_models._model_is_available("qwen2.5-coder:7b", installed) is False


def test_model_is_available_empty_installed_set():
    """Empty installed set always returns False."""
    assert local_models._model_is_available("qwen2.5-coder:7b", set()) is False


@patch("smart_code_lib.llm.local_models.get_ollama_base_url", return_value="http://localhost:11434")
@patch("smart_code_lib.llm.local_models.get_ollama_model", return_value="qwen2.5-coder:7b")
def test_check_ollama_available_success(mock_model, mock_url):
    """Returns ok when Ollama responds with the configured model."""
    payload = json.dumps({"models": [{"name": "qwen2.5-coder:7b"}]}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = payload
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        ok, message = local_models.check_ollama_available()

    assert ok is True
    assert message == ""


@patch("smart_code_lib.llm.local_models.get_ollama_base_url", return_value="http://localhost:11434")
@patch("smart_code_lib.llm.local_models.get_ollama_model", return_value="qwen2.5-coder:7b")
def test_check_ollama_available_url_error(mock_model, mock_url):
    """URLError yields actionable unreachable message."""
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        ok, message = local_models.check_ollama_available()

    assert ok is False
    assert "Ollama is not reachable" in message
    assert "connection refused" in message


@patch("smart_code_lib.llm.local_models.get_ollama_base_url", return_value="http://localhost:11434")
@patch("smart_code_lib.llm.local_models.get_ollama_model", return_value="qwen2.5-coder:7b")
def test_check_ollama_available_json_decode_error(mock_model, mock_url):
    """Invalid JSON from Ollama tags endpoint is reported."""
    mock_response = MagicMock()
    mock_response.read.return_value = b"not-json"
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        ok, message = local_models.check_ollama_available()

    assert ok is False
    assert "Failed to query Ollama" in message


@patch("smart_code_lib.llm.local_models.get_ollama_base_url", return_value="http://localhost:11434")
@patch("smart_code_lib.llm.local_models.get_ollama_model", return_value="qwen2.5-coder:7b")
def test_check_ollama_available_model_not_installed(mock_model, mock_url):
    """Missing configured model returns pull instructions."""
    payload = json.dumps({"models": [{"name": "llama3:8b"}]}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = payload
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        ok, message = local_models.check_ollama_available()

    assert ok is False
    assert "qwen2.5-coder:7b" in message
    assert "ollama pull" in message


@patch("smart_code_lib.llm.local_models.get_ollama_base_url", return_value="http://localhost:11434")
@patch("smart_code_lib.llm.local_models.get_ollama_model", return_value="qwen2.5-coder:7b")
def test_check_ollama_available_empty_models_list(mock_model, mock_url):
    """Empty models list is treated as model not installed."""
    payload = json.dumps({"models": []}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.read.return_value = payload
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        ok, message = local_models.check_ollama_available()

    assert ok is False
    assert "not installed" in message


@patch("smart_code_lib.llm.local_models.get_ollama_base_url", return_value="http://ollama:11434")
@patch("smart_code_lib.llm.local_models.get_ollama_model", return_value="qwen2.5-coder:7b")
def test_check_ollama_available_os_error(mock_model, mock_url):
    """OSError from urlopen is surfaced in the message."""
    with patch("urllib.request.urlopen", side_effect=OSError("network down")):
        ok, message = local_models.check_ollama_available()

    assert ok is False
    assert "Failed to query Ollama" in message
    assert "network down" in message