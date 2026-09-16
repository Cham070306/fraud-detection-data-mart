param(
    [string]$InputCsv,
    [switch]$FromSql,
    [string]$Version = "1.0.0",
    [string]$OutputCsv = "output/model_scoring_full_v1.0.0.csv",
    [string]$PythonExe = "python"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$sourceArgs = @()
if ($FromSql) {
    $sourceArgs += '--from-sql'
} elseif ($InputCsv) {
    $sourceArgs += @('--input', $InputCsv)
} else {
    throw "Use -FromSql (recommended) or provide -InputCsv with SQL keys."
}
& $PythonExe -m scripts.score_transactions @sourceArgs --model "models/fraud_model_v$Version.joblib" --metadata "models/fraud_model_v${Version}_metadata.json" --policy configs/risk_policy.yaml --output $OutputCsv
if ($LASTEXITCODE -ne 0) { throw "Scoring failed with exit code $LASTEXITCODE" }
