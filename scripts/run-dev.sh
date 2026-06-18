#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f .env ]]; then
  echo "Error: .env file not found at $PROJECT_ROOT/.env" >&2
  echo "Create one with OPENAI_API_KEY=your-key" >&2
  exit 1
fi

echo "Starting Smart Code Library API (reload enabled, port 8000)..."
exec uvicorn smart_code_lib.main:app --reload --port 8000