# Pull the default local LLM model for Smart Library
$Model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "llama3.2" }

Write-Host "Pulling Ollama model: $Model"
ollama pull $Model

if ($LASTEXITCODE -eq 0) {
    Write-Host "Model ready. Start the API with .\scripts\run-dev.ps1"
} else {
    Write-Error "Failed to pull model. Ensure Ollama is installed and running: https://ollama.com"
    exit 1
}