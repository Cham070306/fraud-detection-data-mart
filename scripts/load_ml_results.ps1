param(
    [string]$Scores = "output/model_scoring_full_v1.0.0.csv",
    [string]$Metadata = "models/fraud_model_v1.0.0_metadata.json",
    [string]$Policy = "configs/risk_policy.yaml",
    [int]$ChunkSize = 50000,
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

& $PythonExe scripts/load_ml_results.py --scores $Scores --metadata $Metadata `
    --policy $Policy --chunk-size $ChunkSize
if ($LASTEXITCODE -ne 0) { throw "ML result load failed with exit code $LASTEXITCODE" }
