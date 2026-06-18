#!/usr/bin/env sh
# Pull the default local LLM model for Smart Library
MODEL="${OLLAMA_MODEL:-llama3.2}"

echo "Pulling Ollama model: $MODEL"
ollama pull "$MODEL"

if [ $? -eq 0 ]; then
  echo "Model ready. Start the API with ./scripts/run-dev.sh"
else
  echo "Failed to pull model. Ensure Ollama is installed and running: https://ollama.com" >&2
  exit 1
fi