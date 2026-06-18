# Smart Library — Windows development server helper
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found at $envFile. Create one with OPENAI_API_KEY=your-key"
    exit 1
}

Write-Host "Starting Smart Code Library API (reload enabled, port 8000)..."
uvicorn smart_code_lib.main:app --reload --port 8000