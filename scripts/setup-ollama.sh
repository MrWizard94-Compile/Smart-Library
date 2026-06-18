#!/usr/bin/env sh
# Pull the default local LLM model for Smart Library
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL="qwen2.5-coder:7b"

if [ -n "$OLLAMA_MODEL" ]; then
  MODEL="$OLLAMA_MODEL"
elif [ -f "$PROJECT_ROOT/.env" ]; then
  line=$(grep -E '^[[:space:]]*OLLAMA_MODEL[[:space:]]*=' "$PROJECT_ROOT/.env" | head -n 1)
  if [ -n "$line" ]; then
    MODEL=$(printf '%s' "$line" | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs)
  fi
fi

echo "Pulling Ollama model: $MODEL"
ollama pull "$MODEL"

if [ $? -eq 0 ]; then
  echo "Model ready. Start the API with ./scripts/run-dev.sh"
else
  echo "Failed to pull model. Ensure Ollama is installed and running: https://ollama.com" >&2
  exit 1
fi