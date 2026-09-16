param(
    [switch]$Rebuild,
    [switch]$Migrate,
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$ddlArgs = @("scripts/run_ddl.py")
if ($Rebuild) { $ddlArgs += "--rebuild" }
if ($Migrate) { $ddlArgs += "--migrate" }

Write-Host "Creating or migrating FraudDW..." -ForegroundColor Cyan
& $PythonExe @ddlArgs
if ($LASTEXITCODE -ne 0) {
    throw "Database setup failed with exit code $LASTEXITCODE"
}
Write-Host "FraudDW setup completed." -ForegroundColor Green
