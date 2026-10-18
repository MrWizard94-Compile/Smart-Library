# AGENTS — Smart Code Library project entry

Accepted GitHub `main` of [WPAI Constitution](https://github.com/MrWizard94-Compile/Agents-Constitution)
is the sole editable quality/process source. This file is Level 4 project law,
not a local Constitution. Historical SOUL files, local packs, generated mirrors
and caches are not independent law. Freeze one accepted revision per top-level
invocation and load its `SKILL.md`, `references/always-load.md` and named law
from that same revision after checking identity/integrity. Each invocation owes
one meaningful canonical improvement through its reviewed evolution process;
continuations are not new invocations. Do not silently substitute another source.

## Mission and layout

Smart Code Library is a local-first semantic code-reference API with a separate
execution/healing sandbox. Keep retrieval and execution independent and keep
cloud-provider dependencies out of the current local Ollama/HuggingFace stack.

- `smart_code_lib/main.py`: FastAPI gateway; `config.py`: environment loading.
- `smart_code_lib/database/`: Chroma vector memory; `sandbox/`: code runner.
- `smart_code_lib/llm/`: local model providers; `tests/`: mocked unit/contract tests.
- `references/`: architecture, API, setup and security source records.

## Development and verification

1. Read `references/architecture.md`, `references/api-reference.md` and
   `references/security.md` before changing behavior.
2. Follow the declared Python 3.11 CI target and pinned runtime requirements;
   do not silently change the stack to fit an existing local environment.
3. Implement in `smart_code_lib/` and synchronize affected API/security docs.
4. Unit tests mock Ollama, Chroma, Docker and LLM calls; no model downloads,
   network-dependent inference or persistent database changes belong in them.
5. Preserve `tests/conftest.py` fixtures `client`, `mock_services`,
   `client_ollama_down`, `client_startup_failed`, and intended security assertions
   in `tests/test_security.py`. Live-model acceptance is a separate gate.
6. Both product CI and independent canonical-source/adoption CI must pass.
   Source diagnostics are not native/runtime/deployment acceptance.

```bash
pip install -r smart_code_lib/requirements-dev.txt
python -m pytest tests/ -v
```

After completing the setup and authorization described in
`references/setup-guide.md`, the development API command is:

```bash
uvicorn smart_code_lib.main:app --reload
```

## Project security and human review

- Preserve optional `API_KEY`/`X-API-Key` protection on `/seed`, `/execute-heal`
  and `/maintenance/deduplicate`, and `MAX_CODE_BYTES` payload enforcement.
- Prefer Docker isolation and respect `SANDBOX_FAIL_CLOSED`. The threat model
  documents Docker-socket exposure and unsafe in-process fallback boundaries.
- Do not copy real `.env`, model caches, vector data or terminal/session files
  into commits or migration artifacts. Config examples must contain no secrets.
- Supervisor: approves specs/deviations. Implementer: code and intended-behavior
  tests. Reviewer: pytest, documentation and security alignment. These are roles,
  not authorization to spawn agents, publish product changes or start services.
- Cross-project law evolves only in the canonical repository. Preserve unique
  project constraints here without weakening that law or overriding safety.
