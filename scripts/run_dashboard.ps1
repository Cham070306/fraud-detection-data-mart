# run_dashboard.ps1
# TV5 - Launch the Streamlit dashboard (and optionally the FastAPI service).
# Usage:
#   .\scripts\run_dashboard.ps1              # Streamlit only
#   .\scripts\run_dashboard.ps1 -Api         # Streamlit + FastAPI (background)
param(
    [switch]$Api
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if ($Api) {
    Write-Host "Starting FastAPI service on http://localhost:8000 ..." -ForegroundColor Cyan
    Start-Process python -ArgumentList "-m", "uvicorn", "src.api.main:app",
        "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $root
}

Write-Host "Starting Streamlit dashboard on http://localhost:8501 ..." -ForegroundColor Cyan
Set-Location $root
streamlit run dashboard/streamlit/app.py
