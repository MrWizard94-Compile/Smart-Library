# AGENTS.md — Supervisory Workflow

Guidance for AI agents and contributors working on the Smart Code Library.

---

## Project Layout

```
smart_code_lib/          # Application package
  main.py                # FastAPI gateway
  config.py              # Environment configuration
  database/              # Chroma vector store
  sandbox/               # Self-healing code runner
tests/                   # Pytest suite (mocked, no live Ollama)
references/              # Architecture, API, setup, security docs
```

---

## Development Workflow

1. **Read** `references/architecture.md` and `references/api-reference.md` before changing behavior.
2. **Implement** in `smart_code_lib/`; keep cloud dependencies out (local Ollama + HuggingFace only).
3. **Test** with `pip install -r smart_code_lib/requirements-dev.txt` then `python -m pytest tests/ -v`.
4. **Document** API or security changes in `references/`.
5. **CI** must pass (`.github/workflows/ci.yml`).

---

## Testing Conventions

- Mock Ollama, Chroma, Docker, and LLM calls — no network in unit tests.
- Use `tests/conftest.py` fixtures: `client`, `mock_services`, `client_ollama_down`, `client_startup_failed`.
- Security behavior lives in `tests/test_security.py`.

---

## Security Rules

- Write endpoints (`/seed`, `/execute-heal`, `/maintenance/deduplicate`) support optional `API_KEY`.
- Enforce `MAX_CODE_BYTES` on code/content payloads.
- Prefer Docker sandbox; respect `SANDBOX_FAIL_CLOSED` in production-like deployments.
- See `references/security.md` for the full threat model.

---

## Agent Roles

| Role | Responsibility |
|------|----------------|
| **Supervisor** | Approves specs, reviews deviations |
| **Implementer** | Writes code + tests per approved spec |
| **Reviewer** | Runs pytest, checks docs and security alignment |

---

## Common Commands

```bash
# Dev install
pip install -r smart_code_lib/requirements-dev.txt

# Run API locally
uvicorn smart_code_lib.main:app --reload

# Full test suite
python -m pytest tests/ -v
```