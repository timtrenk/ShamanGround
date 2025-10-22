param([Parameter(Mandatory=$true)][ValidateSet("init","activate","scaffold","diag","ship")]$cmd)

function Guard([string]$msg) {
  python engine/activate_guard.py
  if ($LASTEXITCODE -ne 0) { throw $msg }
}

switch ($cmd) {
  "init"     { $env:THOTH_PROJECT_ROOT=(Get-Location).Path; python thoth_loader.py }
  "activate" { Guard "Guard failed"; "activate thoth" }
  "scaffold" { Guard "Guard failed"; "build scaffold" }
  "diag"     { Guard "Guard failed"; "run diagnostics persona=thoth_om_builder_v1 show=distortions,gates detail=brief" }
  "ship"     { Guard "Guard failed"; "run diagnostics persona=thoth_om_builder_v1 show=distortions,gates detail=brief"; ">> Crown Verify your artifact in /artifacts" }
}
