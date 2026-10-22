<#
.SYNOPSIS
  Starts the PREPLINE demo: FastAPI backend on http://127.0.0.1:8000 and the dashboard on http://localhost:5173.

.DESCRIPTION
  Opens the backend and the Vite dev server in two new PowerShell windows, waits until the API answers,
  then opens the dashboard in the default browser. Close the two windows (or press Ctrl+C in them) to stop.
  First run: installs the dashboard's npm packages if dashboard/web/node_modules is missing.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1
#>
param(
    [string]$Python = "python",
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$web = Join-Path $root "dashboard\web"

if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) { throw "Python not found ('$Python'). Pass -Python <path>." }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm not found. Install Node.js 20+." }

if (-not (Test-Path (Join-Path $web "node_modules"))) {
    Write-Host "Installing dashboard packages (first run)..."
    Push-Location $web
    try { npm install } finally { Pop-Location }
}

Write-Host "Starting backend on http://127.0.0.1:8000 ..."
Start-Process powershell -WorkingDirectory $root -ArgumentList @(
    "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'PREPLINE API'; & '$Python' -m uvicorn backend.app:app --host 127.0.0.1 --port 8000"
)

Write-Host "Starting dashboard on http://localhost:5173 ..."
Start-Process powershell -WorkingDirectory $web -ArgumentList @(
    "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'PREPLINE dashboard'; npx vite --port 5173 --strictPort"
)

# The backend loads the embedding stack at import, so give it up to 90 s.
$deadline = (Get-Date).AddSeconds(90)
do {
    Start-Sleep -Seconds 2
    try { $ok = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 "http://127.0.0.1:8000/api/v1/targets").StatusCode -eq 200 } catch { $ok = $false }
} until ($ok -or (Get-Date) -gt $deadline)

if ($ok) { Write-Host "API is up." } else { Write-Warning "API did not answer within 90 s; check the 'PREPLINE API' window." }
if (-not $NoBrowser) { Start-Process "http://localhost:5173" }
Write-Host "Dashboard: http://localhost:5173  (API: http://127.0.0.1:8000/docs)"
