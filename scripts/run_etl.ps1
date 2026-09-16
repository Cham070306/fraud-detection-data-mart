# scripts/run_etl.ps1
# Entry point chay ETL pipeline cho PaySim Fraud Detection Data Mart
# Tac gia: Khai (TV2)
# Cach chay: .\scripts\run_etl.ps1 [-ChunkSize 200000]

param([int]$ChunkSize = 200000)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== PaySim Fraud Detection ETL ===" -ForegroundColor Cyan
Write-Host "Root: $root"
Write-Host "Chunk size: $ChunkSize"

$pythonArgs = @('-m','src.etl.run_etl','--chunk-size', $ChunkSize)

try {
    python @pythonArgs
    if ($LASTEXITCODE -ne 0) { throw "ETL failed with code $LASTEXITCODE" }
    Write-Host "=== ETL SUCCESS ===" -ForegroundColor Green
} catch {
    Write-Host "=== ETL FAILED ===" -ForegroundColor Red
    Write-Error $_.Exception.Message
    exit 1
}
