# WPAI Constitution adoption — Smart Code Library

Accepted [WPAI Constitution main](https://github.com/MrWizard94-Compile/Agents-Constitution)
is the sole editable quality/process source. Project AGENTS retains the
published supervisory workflow, local-only architecture, unit fixtures and
security contracts. Root README now routes to those actual source records
rather than telling agents this existing repository is blank.

## Canonical check

CI pins accepted 6.16.3 at `89f8771df5a6fa8627cb9576afca1eefd0486d27` and
validates its manifest/source/tests before auditing this project. This is a
reproducible tool pin, not a permanent invocation-law freeze. Every future
top-level invocation resolves its own accepted law under the canonical loader.
No project historical-reference exception or scanner filter is introduced.

```powershell
python <verified-canonical-root>/tools/check-adoption.py <project-root>
python -m pytest tests/ -v
```

## Preservation and scope

The published baseline is `ddffc06d7fec1779309786ef349d9b734d5f2d56` on master.
Migration is isolated from the primary checkout's six modified and five
untracked files. These were copied to private hash-verified recovery, excluding
real .env, model caches, vector data and runtime/session files. They are not
authorized for publication by this adoption.

The primary's untracked pre-pack SOUL has SHA-256
`ad3137994b46b5581584b9a43049c4fb31173361d49eb1d872ccdbbcb1e2539e`:
the already inventoried generic Claude Constitution variant, not unique project
law. Its short successor pointer also still routes to the old pack. Neither is
removed from the primary until consumer migration and recoverability are
verified. Project constraints are recovered from the published AGENTS rather
than discarded with the generic law.

## Baseline finding — October 18, 2026

The unchanged baseline has an old green CI run, `27733286463`. That is not
warning-clean acceptance: a fresh strict diagnostic fails at TestClient setup
with httpx's deprecated `app` shortcut, called by the pinned FastAPI/Starlette
cohort. The primary's unpublished pytest configuration also adds a blanket
DeprecationWarning filter; it is not copied into this branch.

The local environment is Python 3.10.11, below the declared Python 3.11 CI
target, and its dependencies pass `pip check`. That local diagnostic does not
replace Python 3.11 CI. No model download, live LLM execution, Docker service
startup or product assertion change was used to obtain the finding.

The director has been asked whether to include a focused compatible dependency
repair and warning-as-error CI in this adoption. Product requirements and test
assertions remain unchanged while that scope decision is pending. Do not merge
or claim completed adoption based only on the legacy green check.

The official [FastAPI 0.110.1 release record](https://fastapi.tiangolo.com/release-notes/#01101)
identifies the Starlette upgrade that removed its own internal warning filter.
This establishes the compatibility boundary, not a recommendation to ship an
old patch without dependency/security review. Any chosen repair needs fresh
verification against the project's intended API behavior.
