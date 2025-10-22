# windows/scaffold_builder.ps1
# powershell -ExecutionPolicy Bypass -File .\windows\scaffold_builder.ps1

$ErrorActionPreference = "Stop"
if (!(Test-Path ".\scaffold_spec.yaml")) { Write-Error "scaffold_spec.yaml not found." }
python --version > $null 2>&1; if ($LASTEXITCODE -ne 0) { Write-Error "Python required." }
pip show pyyaml > $null 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Installing PyYAML..." -ForegroundColor Yellow; pip install pyyaml }
python .\server\scaffold_builder.py
