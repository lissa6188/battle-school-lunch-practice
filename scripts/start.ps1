<#
Starts the application stack using Docker Compose.
Usage:
  PowerShell: .\scripts\start.ps1            # run in foreground
  PowerShell: .\scripts\start.ps1 -Detach   # run in background (docker compose -d)
#>
param(
    [switch]$Detach
)

# Move to repository root (one level up from scripts)
Set-Location -Path (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI not found in PATH. Please install Docker and ensure 'docker' is available."
    exit 1
}

$composeArgs = @("compose", "up", "--build")
if ($Detach) { $composeArgs += "-d" }

Write-Host "Running: docker $($composeArgs -join ' ')"

$proc = Start-Process -FilePath docker -ArgumentList $composeArgs -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Error "docker compose exited with code $($proc.ExitCode)"
    exit $proc.ExitCode
}

Write-Host "Services started. Use 'docker compose down' to stop them."