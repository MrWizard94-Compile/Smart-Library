# Smart Library — install git hooks (Windows)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

git config core.hooksPath .githooks

if ($LASTEXITCODE -eq 0) {
    Write-Host "Git hooks installed. core.hooksPath set to .githooks"
    Write-Host "post-commit will seed changed .md/.json files to the API on each commit."
} else {
    Write-Error "Failed to set core.hooksPath"
    exit 1
}