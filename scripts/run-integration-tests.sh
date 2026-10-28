#!/usr/bin/env bash
# Smart Library — live Ollama integration smoke tests (macOS / Linux)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
TAGS_URL="${OLLAMA_BASE_URL%/}/api/tags"

echo "Checking Ollama at ${TAGS_URL} ..."
if ! curl -fsS --max-time 5 "${TAGS_URL}" >/dev/null; then
  echo "Ollama is not reachable at ${OLLAMA_BASE_URL}. Start Ollama and pull the model (./scripts/setup-ollama.sh)." >&2
  exit 1
fi

if [[ "${INTEGRATION_FULL:-0}" == "1" ]]; then
  MARKER="integration_full"
  echo "Running integration_full smoke tests ..."
else
  MARKER="integration"
  echo "Running lean integration smoke tests ..."
fi

python -m pytest tests/test_integration_ollama.py -m "${MARKER}" --run-integration -v