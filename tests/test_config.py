"""Tests for smart_code_lib.config central configuration."""

import importlib
import os
from pathlib import Path

import pytest

import smart_code_lib.config as config


@pytest.fixture(autouse=True)
def reset_config_module():
    """Reset config module state between tests."""
    importlib.reload(config)
    yield
    importlib.reload(config)


def test_project_root_is_repository_root():
    """PROJECT_ROOT resolves to the repository root (parent of smart_code_lib/)."""
    assert config.PROJECT_ROOT == Path(__file__).resolve().parent.parent
    assert (config.PROJECT_ROOT / "smart_code_lib" / "config.py").is_file()


def test_env_file_lives_under_project_root():
    """ENV_FILE points to .env at the repository root."""
    assert config.ENV_FILE == config.PROJECT_ROOT / ".env"


def test_get_ollama_model_default(monkeypatch):
    """Default Ollama model is qwen2.5-coder:7b when unset."""
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    assert config.get_ollama_model() == "qwen2.5-coder:7b"


def test_get_ollama_base_url_default(monkeypatch):
    """Default Ollama base URL is localhost:11434 when unset."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    assert config.get_ollama_base_url() == "http://localhost:11434"


def test_get_embedding_model_name_default(monkeypatch):
    """Default embedding model is all-MiniLM-L6-v2 when unset."""
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    assert config.get_embedding_model_name() == "sentence-transformers/all-MiniLM-L6-v2"


def test_get_ollama_model_respects_env(monkeypatch):
    """OLLAMA_MODEL environment variable overrides the default."""
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model:1b")
    assert config.get_ollama_model() == "custom-model:1b"


def test_get_ollama_base_url_respects_env(monkeypatch):
    """OLLAMA_BASE_URL environment variable overrides the default."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    assert config.get_ollama_base_url() == "http://ollama:11434"


def test_get_embedding_model_name_respects_env(monkeypatch):
    """EMBEDDING_MODEL environment variable overrides the default."""
    monkeypatch.setenv("EMBEDDING_MODEL", "custom/embeddings")
    assert config.get_embedding_model_name() == "custom/embeddings"


def test_load_env_returns_true_when_dotenv_file_present(tmp_path, monkeypatch):
    """load_env returns True when the .env file exists and is readable."""
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_MODEL=test-from-file\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.setattr(config, "_env_loaded", False)
    assert config.load_env(force=True) is True


def test_load_env_returns_false_when_dotenv_file_missing(tmp_path, monkeypatch):
    """load_env returns False when the .env file does not exist."""
    missing = tmp_path / "missing.env"
    monkeypatch.setattr(config, "ENV_FILE", missing)
    monkeypatch.setattr(config, "_env_loaded", False)
    assert config.load_env(force=True) is False


def test_load_env_skips_second_call_without_force(monkeypatch):
    """load_env calls load_dotenv only once unless force=True."""
    calls = []

    def fake_load_dotenv(path, override=False):
        calls.append((path, override))
        return True

    monkeypatch.setattr(config, "load_dotenv", fake_load_dotenv)
    monkeypatch.setattr(config, "_env_loaded", False)
    config.load_env()
    config.load_env()
    assert len(calls) == 1


def test_load_env_override_false_preserves_existing_env(monkeypatch, tmp_path):
    """load_env passes override=False so pre-set environment variables win."""
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_MODEL=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv("OLLAMA_MODEL", "pre-set")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.setattr(config, "_env_loaded", False)
    captured = {}

    def fake_load_dotenv(path, override=False):
        captured["override"] = override
        return True

    monkeypatch.setattr(config, "load_dotenv", fake_load_dotenv)
    config.load_env(force=True)
    assert captured["override"] is False
    assert os.environ["OLLAMA_MODEL"] == "pre-set"