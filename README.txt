Smart Code Library
==================

Local-first semantic code reference, retrieval and sandboxed self-healing API.
The repository contains a FastAPI gateway, Chroma memory, local model providers
and a separate execution sandbox. A passing mocked suite is not proof of live
model, sandbox-isolation or production deployment acceptance.

Source: https://github.com/MrWizard94-Compile/Smart-Library
Quality/process SSOT: https://github.com/MrWizard94-Compile/Agents-Constitution
Start with AGENTS.md for the canonical loader and preserved project workflow.
Do not load a local pack, SOUL variant or cache as a second Constitution.

Read before changing or running the project:

- references/architecture.md: component boundaries and request flow.
- references/api-reference.md: API bodies, responses and authentication.
- references/security.md: sandbox, Docker socket and optional-key threat model.
- references/setup-guide.md: Python 3.11+, model preparation and startup.
- references/governance-adoption.md: source pin, migration checks and limits.

Development unit checks (mocked services, no live model calls):

    pip install -r smart_code_lib/requirements-dev.txt
    python -m pytest tests/ -v

Run uvicorn smart_code_lib.main:app --reload only after the documented setup.
First real model use can download artifacts; do not start services or touch
persistent vector data merely to validate a governance change. Keep real .env,
model caches, database files and terminal/session data out of Git.

CI requires independent Constitution source/adoption validation and the full
published product test suite. Consult the migration report for any unresolved
gate; a green legacy job must not be presented as warning-clean acceptance.
