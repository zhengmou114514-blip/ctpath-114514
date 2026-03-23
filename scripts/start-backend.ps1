param(
    [string]$DbUrl = "",
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if ($DbUrl) {
    $env:CTPATH_DB_URL = $DbUrl
    Write-Host "Using MySQL mode via CTPATH_DB_URL" -ForegroundColor Green
} elseif ($env:CTPATH_DB_URL) {
    Write-Host "Using existing CTPATH_DB_URL from environment" -ForegroundColor Green
} else {
    Write-Host "CTPATH_DB_URL not set. Backend will fall back to demo mode if MySQL is unavailable." -ForegroundColor Yellow
}

Write-Host "Starting FastAPI backend on http://$Host`:$Port" -ForegroundColor Cyan
uvicorn app.main:app --host $Host --port $Port --reload
