$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Create it first with: py -3.11 -m venv .venv" -ForegroundColor Yellow
    exit 2
}
$Python = ".\.venv\Scripts\python.exe"
Write-Host "Running NewsPilot AI model-free live validation..." -ForegroundColor Cyan
& $Python -m src.live_validation @args
$Code = $LASTEXITCODE
Write-Host "`nOpen output\live_validation_report.json for the detailed report."
exit $Code
