param(
    [ValidateSet("full","test","backtest","research","comparison","comparison-historical","doctor","doctor-data","historical","ingest-massive","fidelity-historical")]
    [string]$Mode = "full",
    [int]$Bars = 200,
    [string]$DataDir = "data/processed",
    [string]$Config = "configs/base.yaml",
    [string]$Start = "2026-06-01",
    [string]$End = "2026-09-30",
    [string]$RawDir = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

# Never silently fall back to sample fixtures for historical research commands
if ($Mode -notin @("historical", "comparison-historical", "doctor-data", "ingest-massive", "fidelity-historical")) {
    if ($DataDir -eq "data/processed" -and -not (Test-Path (Join-Path $Root $DataDir)) -and (Test-Path (Join-Path $Root "data/sample_historical"))) {
        $DataDir = "data/sample_historical"
    }
}


# If Config is base.yaml and running historical commands, choose 1m or daily config based on dataset manifest
if ($Config -eq "configs/base.yaml" -and ($Mode -in "historical", "doctor-data", "comparison-historical", "fidelity-historical")) {
    $manifestPath = Join-Path $Root (Join-Path $DataDir "dataset_manifest.json")
    if (Test-Path $manifestPath) {
        try {
            $manifestJson = Get-Content $manifestPath -Raw | ConvertFrom-Json
            if ($manifestJson.bar_resolution -eq "1m" -and (Test-Path (Join-Path $Root "configs/historical_1m.yaml"))) {
                $Config = "configs/historical_1m.yaml"
            } elseif (Test-Path (Join-Path $Root "configs/historical_daily.yaml")) {
                $Config = "configs/historical_daily.yaml"
            }
        } catch {
            if (Test-Path (Join-Path $Root "configs/historical_daily.yaml")) {
                $Config = "configs/historical_daily.yaml"
            }
        }
    } elseif (Test-Path (Join-Path $Root "configs/historical_daily.yaml")) {
        $Config = "configs/historical_daily.yaml"
    }
}


function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Python {
    & $Python $args
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

    "doctor-data" {
        Write-Step "Historical data integrity check and diagnostics"
        Invoke-Python -m tactical_engine.data.doctor --config $Config --data-dir $DataDir
        break
    }

    "historical" {
        Write-Step "Historical market-data research run (REFUSES if required real data missing)"
        Invoke-Python -m tactical_engine.historical_runner --config $Config --data-dir $DataDir
        break
    }

    "comparison-historical" {
        Write-Step "Historical 3-variant strategy comparison (REFUSES if required data missing)"
        Invoke-Python -m tactical_engine.research.historical_comparison --config $Config --data-dir $DataDir
        break
    }

    "fidelity-historical" {
        Write-Step "Historical Reddit strategy fidelity experiment matrix"
        Invoke-Python -m tactical_engine.research.fidelity_runner --config $Config --data-dir $DataDir
        break
    }

    "ingest-massive" {
        Write-Step "Ingesting historical market data from Massive Stocks REST API"
        $cmdArgs = @("-m", "tactical_engine.data.massive", "--data-dir", $DataDir, "--start", $Start, "--end", $End)
        if ($RawDir) {
            $cmdArgs += @("--raw-dir", $RawDir)
        }
        Invoke-Python @cmdArgs
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
