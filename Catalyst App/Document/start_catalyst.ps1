# Catalyst Serve Cleanup and Start Script
# This script handles Windows file locks and starts Catalyst development server

Write-Host "Stopping any running Python/Node processes related to Catalyst..." -ForegroundColor Yellow

# Stop Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait for processes to fully terminate
Start-Sleep -Seconds 2

# Remove .build folder forcefully
Write-Host "Removing .build folder..." -ForegroundColor Yellow
if (Test-Path '.build') {
    # Try normal removal first
    Remove-Item -Recurse -Force '.build' -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1

    # If still exists, use cmd.exe rd which handles locks better
    if (Test-Path '.build') {
        Write-Host "Using cmd.exe for stubborn locks..." -ForegroundColor Yellow
        cmd /c "rd /s /q .build" 2>$null
        Start-Sleep -Seconds 2
    }

    # Final check
    if (Test-Path '.build') {
        Write-Host "WARNING: .build folder still exists. Trying catalyst serve anyway..." -ForegroundColor Red
    } else {
        Write-Host ".build folder removed successfully!" -ForegroundColor Green
    }
} else {
    Write-Host ".build folder does not exist." -ForegroundColor Green
}

# Start Catalyst serve
Write-Host "`nStarting Catalyst development server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Gray

catalyst serve
