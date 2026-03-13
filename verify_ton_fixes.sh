#!/bin/bash
# Verification script for TON Connect and wallet UUID fixes

echo "===== TON Connect & Wallet Fixes Verification ====="
echo ""

# Test 1: Check manifest endpoint
echo "1. Testing TON Connect Manifest Endpoint..."
echo "   Endpoint: /tonconnect-manifest.json"
echo ""
echo "   Expected Response:"
echo "   {\"url\": \"https://nftplatformbackend-production-9081.up.railway.app\", ...}"
echo ""
echo "   Command:"
echo "   curl -s https://nftplatformbackend-production-9081.up.railway.app/tonconnect-manifest.json | jq '.url'"
echo ""

# Test 2: Check wallet list with invalid UUID
echo "2. Testing Wallet List UUID Validation..."
echo "   Endpoint: /wallets?user_id=INVALID_UUID"
echo ""
echo "   Expected Response (400 Bad Request):"
echo "   {\"detail\": \"Invalid user_id format. Must be a valid UUID...\"}"
echo ""
echo "   Command:"
echo "   curl -s 'https://nftplatformbackend-production-9081.up.railway.app/wallets?user_id=invalid' | jq '.detail'"
echo ""

# Test 3: Check wallet list with valid UUID
echo "3. Testing Wallet List with Valid UUID..."
echo "   Endpoint: /wallets?user_id=550e8400-e29b-41d4-a716-446655440000"
echo ""
echo "   Expected Response (Success or 404 if user doesn't exist, NOT UUID error):"
echo "   [...] or {\"detail\": \"User not found\"}"
echo ""
echo "   Command:"
echo "   curl -s 'https://nftplatformbackend-production-9081.up.railway.app/wallets?user_id=550e8400-e29b-41d4-a716-446655440000' | jq ."
echo ""

echo "===== Frontend TON Connect Button Check ====="
echo ""
echo "To verify the TON Connect button is working:"
echo "1. Open the web app in your browser"
echo "2. Check Browser DevTools Console (F12)"
echo "3. Look for these messages:"
echo "   ✓ TonConnect manifest loaded: https://nftplatformbackend-production-9081.up.railway.app"
echo "   ✅ TonConnect UI initialized"
echo ""
echo "4. Click the 'Connect TON Wallet' button"
echo "5. You should see the wallet selection modal (NOT 'connection failed')"
echo ""

echo "===== Logs Check ====="
echo ""
echo "Look for these logs (should appear, NOT UUID errors):"
echo "   INFO - TonConnect manifest origin: https://nftplatformbackend-production-9081.up.railway.app"
echo ""
echo "Should NOT see:"
echo "   ERROR - List wallets error: badly formed hexadecimal UUID string"
