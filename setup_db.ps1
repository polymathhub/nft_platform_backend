# PowerShell script to setup PostgreSQL for NFT Platform Backend
# Run with admin privileges or in pgAdmin Query Tool

$psqlPath = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

if (-not (Test-Path $psqlPath)) {
    Write-Host "psql.exe not found at expected location" -ForegroundColor Red
    Write-Host "Checked: $psqlPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "NFT Platform Backend - Database Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Test postgres connection first
Write-Host "Testing PostgreSQL connection..." -ForegroundColor Yellow
try {
    $testConn = & $psqlPath -U postgres -h localhost -d postgres -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL is accessible as postgres user" -ForegroundColor Green
    } else {
        Write-Host "✗ Cannot connect as postgres user" -ForegroundColor Red
        Write-Host "  You may need to enter the postgres password when prompted" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Error testing connection: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Creating nft_user and nft_db..." -ForegroundColor Yellow

# Create the SQL commands
$sqlCommands = @"
CREATE USER IF NOT EXISTS nft_user WITH PASSWORD 'GiftedForge';
CREATE DATABASE IF NOT EXISTS nft_db OWNER nft_user;
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
GRANT ALL ON SCHEMA public TO nft_user;
SELECT 'Setup complete' as status;
"@

# Execute SQL
Write-Host "Executing setup commands..." -ForegroundColor Yellow
$output = $sqlCommands | & $psqlPath -U postgres -h localhost -d postgres 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Setup completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Database configuration:" -ForegroundColor Cyan
    Write-Host "  Host: localhost" -ForegroundColor White
    Write-Host "  Port: 5432" -ForegroundColor White
    Write-Host "  User: nft_user" -ForegroundColor White
    Write-Host "  Password: GiftedForge" -ForegroundColor White
    Write-Host "  Database: nft_db" -ForegroundColor White
    Write-Host ""
    Write-Host "Your .env file DATABASE_URL is correctly set to:" -ForegroundColor Cyan
    Write-Host "  postgresql+asyncpg://nft_user:GiftedForge@localhost:5432/nft_db" -ForegroundColor White
    Write-Host ""
    Write-Host "You can now run: python startup.py" -ForegroundColor Green
} else {
    Write-Host "✗ Setup failed!" -ForegroundColor Red
    Write-Host "Output:" -ForegroundColor Yellow
    Write-Host $output
    exit 1
}
