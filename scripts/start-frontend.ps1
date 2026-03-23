param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot "frontend"
Set-Location $frontendRoot

Write-Host "Starting Vue frontend on http://127.0.0.1:$Port" -ForegroundColor Cyan
cmd /c npm run dev -- --host 127.0.0.1 --port $Port
