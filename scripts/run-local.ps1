<#
Run backend and frontend locally without Docker.
Usage:
  PowerShell: .\scripts\run-local.ps1        # runs backend (background) + frontend (foreground)
  PowerShell: .\scripts\run-local.ps1 -NoFrontend  # only start backend

Behavior:
- Creates a venv at backend\.venv (if missing)
- Installs backend requirements
- Reads NEIS_API_KEY from .env (if present) and passes it to the backend process
- Starts backend in a background process and then starts frontend (npm run dev) in the current console
#>
param(
    [switch]$NoFrontend
)

# Move to repo root
Set-Location -Path (Join-Path $PSScriptRoot "..")

# Find python
$pyCmd = $null
try { $tmp = Get-Command python -ErrorAction SilentlyContinue; if ($tmp) { $pyCmd = $tmp.Source } } catch {}
if (-not $pyCmd) { try { $tmp = Get-Command python3 -ErrorAction SilentlyContinue; if ($tmp) { $pyCmd = $tmp.Source } } catch {} }
if (-not $pyCmd) { try { $tmp = Get-Command py -ErrorAction SilentlyContinue; if ($tmp) { $pyCmd = $tmp.Source } } catch {} }
if (-not $pyCmd) {
    # fallback to where.exe
    try {
        $where = & where.exe python 2>$null
        if ($where) { $pyCmd = $where.Split()[0] }
    } catch {}
}

if ($pyCmd) {
    Write-Host "Using python executable: $pyCmd"
} else {
    Write-Error "Python is not found in PATH. Ensure 'python' or 'py' is available, or install Python 3.8+. Also check Windows Settings → App execution aliases and disable the Microsoft Store alias for 'python' if necessary."
    exit 1
}

$venvPath = Join-Path "backend" ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv at $venvPath"
    & $pyCmd -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Expected venv python at $venvPython but not found."
    exit 1
}

Write-Host "Installing backend requirements..."
& $venvPython -m pip install --upgrade pip >/dev/null
& $venvPython -m pip install -r backend\requirements.txt

# Read NEIS_API_KEY from .env if present
$neisKey = $null
if (Test-Path ".env") {
    $envLines = Get-Content .env | Where-Object { $_ -match "^\s*NEIS_API_KEY\s*=" }
    if ($envLines) {
        $neisKey = ($envLines -split "=",2)[1].Trim()
    }
}

# Start backend in background (separate PowerShell process to inherit env)
$backendCmd = "& '$venvPython' -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
if ($neisKey) { $startArgs = "-NoProfile -WindowStyle Minimized -Command `$env:NEIS_API_KEY='$neisKey'; $backendCmd" }
else { $startArgs = "-NoProfile -WindowStyle Minimized -Command $backendCmd" }

Write-Host "Starting backend in background..."
Start-Process -FilePath pwsh -ArgumentList $startArgs -PassThru | Out-Null
Write-Host "Backend started (background)."

if ($NoFrontend) { Write-Host "NoFrontend specified; exiting after starting backend."; exit 0 }

# Frontend: check node
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Warning "npm not found in PATH. Install Node.js to run the frontend locally, or run the frontend separately.";
    exit 0
}

Write-Host "Installing frontend dependencies (if needed)..."
Push-Location frontend
if (-not (Test-Path "node_modules")) {
    npm install
}

Write-Host "Starting frontend dev server (npm run dev). Press Ctrl+C to stop."
npm run dev
Pop-Location
