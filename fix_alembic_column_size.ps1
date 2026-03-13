#!/usr/bin/env pwsh
# Fix for Alembic Version Column Size Error
# Windows PowerShell Script

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   ALEMBIC COLUMN SIZE FIX" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "alembic" -PathType Container)) {
    Write-Host "ERROR: alembic/ directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Step 1: Activating Python virtual environment..." -ForegroundColor Yellow
$venv_script = ".\.venv\Scripts\Activate.ps1"

if (-not (Test-Path $venv_script)) {
    Write-Host "ERROR: Virtual environment not found at $venv_script" -ForegroundColor Red
    Write-Host "Please create a virtual environment first." -ForegroundColor Yellow
    exit 1
}

& $venv_script
Write-Host "✓ Virtual environment activated`n" -ForegroundColor Green

# Run the comprehensive fix
Write-Host "Step 2: Running comprehensive migration fix..." -ForegroundColor Yellow
Write-Host "This will:" -ForegroundColor Gray
Write-Host "  - Expand alembic_version.version_num column" -ForegroundColor Gray
Write-Host "  - Run all pending migrations" -ForegroundColor Gray
Write-Host "  - Report success/failure" -ForegroundColor Gray
Write-Host ""

python comprehensive_migration_fix.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ FIX COMPLETED SUCCESSFULLY!`n" -ForegroundColor Green
    Write-Host "Your database is now ready. You can start the application:" -ForegroundColor Cyan
    Write-Host "  python startup.py" -ForegroundColor Gray
} else {
    Write-Host "`n❌ FIX FAILED" -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    Write-Host "`nFor manual fix instructions, see: ALEMBIC_COLUMN_SIZE_FIX.md" -ForegroundColor Gray
    exit 1
}
