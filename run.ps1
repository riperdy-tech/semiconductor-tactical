param(
    [ValidateSet("full","test","backtest","research","comparison","doctor")]
    [string]$Mode = "full",
    [int]$Bars = 200
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $Python @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Write-Step "Preparing Python environment"
if (-not (Test-Path $Python)) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        & $launcher.Source -3 -m venv (Join-Path $Root ".venv")
    } else {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCmd) {
            throw "Python 3 is required. Install Python 3.11+ and rerun .\run.ps1."
        }
        & $pythonCmd.Source -m venv (Join-Path $Root ".venv")
    }
    if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv" }
}

Write-Step "Installing/updating project dependencies"
Invoke-Python -m pip install --disable-pip-version-check -q --upgrade pip
Invoke-Python -m pip install --disable-pip-version-check -q -e ".[dev]"

switch ($Mode) {
    "doctor" {
        Write-Step "Environment and import smoke test"
        Invoke-Python -c "import sys, tactical_engine; print('Python:', sys.version.split()[0]); print('tactical_engine:', tactical_engine.__version__)"
        Invoke-Python -m pytest --collect-only
        break
    }

    "test" {
        Write-Step "Full pytest suite"
        Invoke-Python -m pytest
        break
    }

    "backtest" {
        Write-Step "Fixture backtest (NOT historical market data)"
        Invoke-Python -m tactical_engine --config configs/base.yaml --bars $Bars
        break
    }

    "research" {
        Write-Step "Fixture robustness research (NOT historical market data)"
        Invoke-Python -m tactical_engine.research.cli --config configs/base.yaml --bars $Bars
        break
    }

    "comparison" {
        Write-Step "Fixture strategy comparison (NOT historical market data)"
        Invoke-Python -m tactical_engine.research.report_generator --config configs/base.yaml --bars $Bars
        break
    }

    "full" {
        Write-Step "1/4 — Tests"
        Invoke-Python -m pytest

        Write-Step "2/4 — Fixture backtest"
        Invoke-Python -m tactical_engine --config configs/base.yaml --bars $Bars

        Write-Step "3/4 — Fixture robustness research"
        Invoke-Python -m tactical_engine.research.cli --config configs/base.yaml --bars $Bars

        Write-Step "4/4 — Fixture strategy comparison"
        Invoke-Python -m tactical_engine.research.report_generator --config configs/base.yaml --bars $Bars

        Write-Host ""
        Write-Host "ALL LOCAL CHECKS PASSED." -ForegroundColor Green
        Write-Host "IMPORTANT: current CLI experiments use synthetic fixture data." -ForegroundColor Yellow
        Write-Host "They do NOT constitute the historical semiconductor strategy research yet." -ForegroundColor Yellow
        break
    }
}
