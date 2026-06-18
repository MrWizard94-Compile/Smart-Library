#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "Starting Smart Code Library API (local models, reload enabled, port 8000)..."
echo "Ensure Ollama is running and model is pulled: ./scripts/setup-ollama.sh"
exec uvicorn smart_code_lib.main:app --reload --port 8000