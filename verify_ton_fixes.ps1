# Verification script for TON Connect and wallet UUID fixes (PowerShell)

Write-Host "===== TON Connect & Wallet Fixes Verification =====" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check manifest endpoint
Write-Host "1. Testing TON Connect Manifest Endpoint..." -ForegroundColor Green
Write-Host "   Endpoint: /tonconnect-manifest.json"
Write-Host ""
Write-Host "   Expected Response:"
Write-Host "   {`"url`": `"https://nftplatformbackend-production-9081.up.railway.app`", ...}"
Write-Host ""
Write-Host "   Command:"
Write-Host "   Invoke-WebRequest -Uri 'https://nftplatformbackend-production-9081.up.railway.app/tonconnect-manifest.json' | ConvertFrom-Json | Select-Object -ExpandProperty url"
Write-Host ""

# Test 2: Check wallet list with invalid UUID
Write-Host "2. Testing Wallet List UUID Validation..." -ForegroundColor Green
Write-Host "   Endpoint: /wallets?user_id=INVALID_UUID"
Write-Host ""
Write-Host "   Expected Response (400 Bad Request):"
Write-Host "   {`"detail`": `"Invalid user_id format. Must be a valid UUID...`"}"
Write-Host ""
Write-Host "   Command:"
Write-Host "   `$resp = Invoke-WebRequest -Uri 'https://nftplatformbackend-production-9081.up.railway.app/wallets?user_id=invalid' -ErrorAction SilentlyContinue"
Write-Host "   `$resp.Content | ConvertFrom-Json | Select-Object -ExpandProperty detail"
Write-Host ""

# Test 3: Check wallet list with valid UUID
Write-Host "3. Testing Wallet List with Valid UUID..." -ForegroundColor Green
Write-Host "   Endpoint: /wallets?user_id=550e8400-e29b-41d4-a716-446655440000"
Write-Host ""
Write-Host "   Expected Response (Success or 404 if user doesn't exist, NOT UUID error):"
Write-Host "   [...] or {`"detail`": `"User not found`"}"
Write-Host ""
Write-Host "   Command:"
Write-Host "   Invoke-WebRequest -Uri 'https://nftplatformbackend-production-9081.up.railway.app/wallets?user_id=550e8400-e29b-41d4-a716-446655440000' | ConvertFrom-Json"
Write-Host ""

Write-Host "===== Frontend TON Connect Button Check =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "To verify the TON Connect button is working:"
Write-Host "1. Open the web app: https://nftplatformbackend-production-9081.up.railway.app/webapp/"
Write-Host "2. Check Browser DevTools Console (F12)"
Write-Host "3. Look for these messages:"
Write-Host "   ✓ TonConnect manifest loaded: https://nftplatformbackend-production-9081.up.railway.app" -ForegroundColor Green
Write-Host "   ✅ TonConnect UI initialized" -ForegroundColor Green
Write-Host ""
Write-Host "4. Click the 'Connect TON Wallet' button"
Write-Host "5. You should see the wallet selection modal (NOT 'connection failed')"
Write-Host ""

Write-Host "===== Logs Check =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "Look for these logs (GOOD - should appear):"
Write-Host "   INFO - TonConnect manifest origin: https://nftplatformbackend-production-9081.up.railway.app" -ForegroundColor Green
Write-Host ""
Write-Host "Should NOT see:"
Write-Host "   ERROR - List wallets error: badly formed hexadecimal UUID string" -ForegroundColor Red
Write-Host ""

Write-Host "===== Summary =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fixes Applied:" -ForegroundColor Yellow
Write-Host "  ✅ 1. Frontend: Changed manifest path from /static/tonconnect-manifest.json to /tonconnect-manifest.json"
Write-Host "  ✅ 2. Backend: Added APP_URL to .env configuration"
Write-Host "  ✅ 3. Backend: Added fallback logic for manifest origin determination"
Write-Host "  ✅ 4. Backend: Added proper UUID validation in wallet list endpoint"
Write-Host ""
Write-Host "Expected Result:"
Write-Host "  ✅ TON Connect button shows wallet selection dialog (not 'connection failed')"
Write-Host "  ✅ Manifest endpoint returns correct production origin"
Write-Host "  ✅ Wallet list endpoint returns 400 with clear message for invalid UUIDs"
Write-Host "  ✅ Application logs no longer show UUID errors"
