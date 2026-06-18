#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

git config core.hooksPath .githooks
echo "Git hooks installed. core.hooksPath set to .githooks"
echo "post-commit will seed changed .md/.json files to the API on each commit."