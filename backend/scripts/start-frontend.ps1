param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $backendRoot
$frontendRoot = Join-Path $repoRoot "frontend"
Set-Location $frontendRoot

Write-Host "Starting Vue frontend on http://127.0.0.1:$Port" -ForegroundColor Cyan
cmd /c npm run dev -- --host 127.0.0.1 --port $Port
