# Pull the default local LLM model for Smart Library
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$Model = "qwen2.5-coder:7b"

if ($env:OLLAMA_MODEL) {
    $Model = $env:OLLAMA_MODEL
} elseif (Test-Path $EnvFile) {
    $line = Get-Content $EnvFile | Where-Object { $_ -match '^\s*OLLAMA_MODEL\s*=' } | Select-Object -First 1
    if ($line) {
        $Model = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    }
}

Write-Host "Pulling Ollama model: $Model"
ollama pull $Model

if ($LASTEXITCODE -eq 0) {
    Write-Host "Model ready. Start the API with .\scripts\run-dev.ps1"
} else {
    Write-Error "Failed to pull model. Ensure Ollama is installed and running: https://ollama.com"
    exit 1
}