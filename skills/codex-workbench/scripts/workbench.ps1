param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

$scriptDir = if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
  Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
  $PSScriptRoot
}

$engine = Join-Path $scriptDir "workbench.py"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source $engine @Args
  exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source $engine @Args
  exit $LASTEXITCODE
}

$python = Get-Command python3 -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source $engine @Args
  exit $LASTEXITCODE
}

throw "Python was not found. Install Python 3 and retry."
