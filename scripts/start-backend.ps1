param(
    [string]$DbUrl = "",
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$envFile = Join-Path $projectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim().Trim("'`"")
        if ($name -and -not (Test-Path "Env:$name")) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
    Write-Host "Loaded environment values from .env" -ForegroundColor Green
}

if ($DbUrl) {
    $env:CTPATH_DB_URL = $DbUrl
    Write-Host "Using MySQL mode via CTPATH_DB_URL" -ForegroundColor Green
} elseif ($env:CTPATH_DB_URL) {
    Write-Host "Using existing CTPATH_DB_URL from environment" -ForegroundColor Green
} else {
    Write-Host "CTPATH_DB_URL not set. Backend will fall back to demo mode if MySQL is unavailable." -ForegroundColor Yellow
}

if ($env:CTPATH_LLM_ENABLED -eq "true" -and $env:DEEPSEEK_API_KEY) {
    Write-Host "DeepSeek advice is enabled from environment configuration." -ForegroundColor Green
} else {
    Write-Host "DeepSeek advice is not enabled. Backend will use placeholder advice." -ForegroundColor Yellow
}

Write-Host "Starting FastAPI backend on http://$Host`:$Port" -ForegroundColor Cyan
uvicorn app.main:app --host $Host --port $Port --reload
