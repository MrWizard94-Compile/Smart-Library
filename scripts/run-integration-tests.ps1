# Smart Library — live Ollama integration smoke tests (Windows)
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

$ollamaBase = $env:OLLAMA_BASE_URL
if (-not $ollamaBase) {
    $ollamaBase = "http://localhost:11434"
}

$tagsUrl = "$($ollamaBase.TrimEnd('/'))/api/tags"
Write-Host "Checking Ollama at $tagsUrl ..."
try {
    Invoke-WebRequest -Uri $tagsUrl -TimeoutSec 5 -UseBasicParsing | Out-Null
} catch {
    Write-Error "Ollama is not reachable at $ollamaBase. Start Ollama and pull the model (.\scripts\setup-ollama.ps1)."
    exit 1
}

if ($env:INTEGRATION_FULL -eq "1") {
    $marker = "integration_full"
    Write-Host "Running integration_full smoke tests ..."
} else {
    $marker = "integration"
    Write-Host "Running lean integration smoke tests ..."
}

python -m pytest tests/test_integration_ollama.py -m $marker --run-integration -v
exit $LASTEXITCODE