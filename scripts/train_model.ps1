param(
    [Parameter(Mandatory=$true)][string]$InputCsv,
    [string]$Version = "1.0.0",
    [string]$PythonExe = "python"
)
$ErrorActionPreference = "Stop"
& $PythonExe -m scripts.train_model --input $InputCsv --output-dir models --version $Version
if ($LASTEXITCODE -ne 0) { throw "Training failed with exit code $LASTEXITCODE" }

