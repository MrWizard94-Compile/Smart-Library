# Smart Library — Windows development server helper
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

Write-Host "Starting Smart Code Library API (local models, reload enabled, port 8000)..."
Write-Host "Ensure Ollama is running and model is pulled: .\scripts\setup-ollama.ps1"
uvicorn smart_code_lib.main:app --reload --port 8000