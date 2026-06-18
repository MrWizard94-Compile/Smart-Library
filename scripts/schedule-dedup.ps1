# Smart Library — Weekly vector deduplication scheduler
#
# This script documents how to register a Windows Task Scheduler job that runs
# vector deduplication every Sunday at 02:00. Run the schtasks command below
# once from an elevated PowerShell prompt (adjust paths if your install differs).
#
# Prerequisites:
#   - Python on PATH (or use full path to python.exe)
#   - .env with OPENAI_API_KEY in the project root
#   - smart_code_lib dependencies installed (pip install -r smart_code_lib/requirements.txt)
#
# Dry-run preview (manual):
#   python scripts/deduplicate_vectors.py --dry-run
#
# Execute deduplication (manual):
#   python scripts/deduplicate_vectors.py --execute
#
# Example: register weekly task (Sunday 02:00, executes deletions)
#
# $ProjectRoot = "C:\Users\Bulkl\OneDrive\Desktop\Smart Library"
# $Python      = "python"
# $Script      = Join-Path $ProjectRoot "scripts\deduplicate_vectors.py"
# $LogDir      = Join-Path $ProjectRoot "logs"
# New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
#
# schtasks /Create /TN "SmartLibrary-VectorDedup" /SC WEEKLY /D SUN /ST 02:00 `
#   /TR "cmd /c `"$Python`" `"$Script`" --execute --threshold 0.95 >> `"$LogDir\dedup.log`" 2>&1" `
#   /RL HIGHEST /F
#
# Verify:  schtasks /Query /TN "SmartLibrary-VectorDedup" /V /FO LIST
# Remove:  schtasks /Delete /TN "SmartLibrary-VectorDedup" /F

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Project root: $ProjectRoot"
Write-Host "See comment block in this file for schtasks registration example."