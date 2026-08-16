param(
    [Parameter(Mandatory=$true)][string]$InputCsv,
    [string]$Version = "1.0.0",
    [string]$OutputCsv = "output/model_scoring_full_v1.0.0.csv",
    [string]$PythonExe = "python"
)
$ErrorActionPreference = "Stop"
& $PythonExe -m scripts.score_transactions --input $InputCsv --model "models/fraud_model_v$Version.joblib" --metadata "models/fraud_model_v${Version}_metadata.json" --policy configs/risk_policy.yaml --output $OutputCsv
if ($LASTEXITCODE -ne 0) { throw "Scoring failed with exit code $LASTEXITCODE" }
