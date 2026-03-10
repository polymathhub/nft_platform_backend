# PowerShell startup script for NFT Platform Backend
# Handles enum type initialization, Alembic migrations, and FastAPI server startup

param(
    [switch]$NoVenv = $false
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"

# Activate virtual environment if it exists
if (-not $NoVenv -and (Test-Path $venvPath)) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "Virtual environment not found or -NoVenv specified" -ForegroundColor Yellow
}

# Run the startup script
Write-Host "Running startup script with database initialization..." -ForegroundColor Green
python "$scriptDir\startup.py"
