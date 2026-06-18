# Smart Code Library — Security

Threat model and hardening controls for the local-first API.

---

## Threat Model

| Threat | Vector | Impact | Mitigation |
|--------|--------|--------|------------|
| **Arbitrary code execution** | `POST /execute-heal` runs user-supplied Python | Host compromise, data exfiltration | Docker-isolated sandbox (no network, read-only root, dropped caps, non-root user). Optional `SANDBOX_FAIL_CLOSED=true` disables in-process fallback. |
| **Docker socket exposure** | API container mounts `/var/run/docker.sock` | Container can control host Docker daemon | Document risk in `docker-compose.yml`; restrict deployment to trusted environments; prefer dedicated sandbox hosts. |
| **Unauthenticated writes** | `POST /seed`, `/execute-heal`, `/maintenance/deduplicate` mutate state | Poisoned embeddings, resource exhaustion | Optional `API_KEY` + `X-API-Key` header on write endpoints. |
| **Oversized payloads** | Large `code` or `content` bodies | Memory pressure, DoS | `MAX_CODE_BYTES` (default 65536) enforced via HTTP 413. |
| **LLM prompt injection** | Malicious content in seed/query context | Unsafe generated code | Treat LLM output as untrusted; sandbox all execution; review healed patches. |
| **Dependency / supply chain** | Third-party packages (LangChain, Chroma, etc.) | Vulnerable transitive deps | Pin versions in `requirements.txt`; run CI tests on every change. |

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `USE_DOCKER_SANDBOX` | `true` | Docker-isolated execution (recommended). |
| `SANDBOX_FAIL_CLOSED` | `false` | When `true`, refuse in-process fallback if Docker is unavailable. |
| `MAX_CODE_BYTES` | `65536` | Maximum UTF-8 byte size for code/content on write endpoints. |
| `API_KEY` | *(unset)* | When set, write endpoints require matching `X-API-Key` header. |

---

## Endpoint Protection

| Endpoint | Auth (`API_KEY`) | Size limit |
|----------|------------------|------------|
| `GET /health` | No | — |
| `POST /query` | No | — |
| `POST /seed` | Yes (if configured) | Yes (`content`) |
| `POST /execute-heal` | Yes (if configured) | Yes (`code`) |
| `POST /maintenance/deduplicate` | Yes (if configured) | — |

---

## Operational Guidance

1. **Production:** Set `API_KEY`, keep `USE_DOCKER_SANDBOX=true`, consider `SANDBOX_FAIL_CLOSED=true`.
2. **Development:** Leave `API_KEY` unset for frictionless local testing.
3. **Never** expose the Docker socket to untrusted networks without additional isolation.
4. Rotate `API_KEY` if leaked; restrict write endpoints behind a reverse proxy when possible.