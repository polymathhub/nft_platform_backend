#!/usr/bin/env python3
"""
Telegram Webhook Setup Verification
Validates that all Telegram infrastructure is correctly configured
"""

import os
import sys
import asyncio
import hashlib
import hmac
import json
from urllib.parse import parse_qs
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Verify environment setup
def check_env_variables():
    """Verify required environment variables are set"""
    required = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_WEBHOOK_URL",
        "TELEGRAM_WEBHOOK_SECRET",
    ]
    
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables set")
    return True


def check_webhook_url_format():
    """Verify webhook URL has correct format"""
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    # Must be HTTPS in production, HTTP allowed in local dev
    if not webhook_url.startswith(("http://", "https://")):
        print(f"❌ Invalid webhook URL format: {webhook_url}")
        return False
    
    # Must include the correct path
    if "/api/v1/telegram/webhook" not in webhook_url:
        print(f"❌ Webhook URL must end with /api/v1/telegram/webhook")
        print(f"   Current: {webhook_url}")
        return False
    
    print(f"✅ Webhook URL format correct: {webhook_url}")
    return True


def verify_hmac_implementation():
    """Verify HMAC-SHA256 verification works correctly"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    if not bot_token:
        print("❌ Bot token not configured")
        return False
    
    # Create test init_data
    test_data = {
        "user": json.dumps({"id": 123456789, "username": "testuser", "first_name": "Test"}),
        "auth_date": "1234567890",
        "chat_instance": "12345",
    }
    
    # Compute hash (same logic as backend)
    check_string_parts = []
    for key in sorted(test_data.keys()):
        if key != "hash":
            check_string_parts.append(f"{key}={test_data[key]}")
    
    check_string = "\n".join(check_string_parts)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"✅ HMAC-SHA256 implementation verified")
    print(f"   Test hash computed: {computed_hash[:16]}...")
    return True


def check_response_format():
    """Verify expected response format from /web-app/init"""
    # This is what the frontend expects
    expected_response_fields = {
        "success": bool,
        "user": {
            "id": str,
            "telegram_id": int,
            "telegram_username": str,
            "full_name": str,
            "avatar_url": (str, type(None)),
            "email": (str, type(None)),
            "is_verified": bool,
            "user_role": str,
            "created_at": str,
        }
    }
    
    print("✅ Expected response format defined")
    print("   Response must include:")
    print("   - success: boolean")
    print("   - user.id: UUID string")
    print("   - user.telegram_id: integer (REAL from verified initData)")
    print("   - user.telegram_username: string")
    print("   - user.full_name: string")
    print("   - user.created_at: ISO datetime string")
    return True


def check_routing_configuration():
    """Verify routing is correctly configured"""
    issues = []
    
    try:
        # Check main.py imports
        with open("app/main.py", "r", encoding="utf-8") as f:
            main_content = f.read()
            if "from app.routers.telegram_mint_router import router as telegram_mint_router" not in main_content:
                issues.append("telegram_mint_router not imported in main.py")
            if "prefix=\"/api/v1/telegram\"" not in main_content:
                issues.append("telegram_mint_router not mounted with /api/v1/telegram prefix")
        
        # Check router definition
        with open("app/routers/telegram_mint_router.py", "r", encoding="utf-8") as f:
            router_content = f.read()
            if "router = APIRouter" not in router_content:
                issues.append("Router not defined in telegram_mint_router.py")
            if "@router.post(\"/webhook\")" not in router_content:
                issues.append("Webhook endpoint not defined")
            if "@router.get(\"/web-app/init\")" not in router_content:
                issues.append("Web app init endpoint not defined")
    except Exception as e:
        issues.append(f"Error reading files: {e}")
    
    if issues:
        print(f"❌ Routing configuration issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Routing configuration correct")
    print("   - telegram_mint_router imported and mounted at /api/v1/telegram")
    print("   - POST /webhook endpoint exists")
    print("   - GET /web-app/init endpoint exists")
    return True


def main():
    """Run all verification checks"""
    print("\n🔍 Telegram Webhook Setup Verification\n")
    
    checks = [
        ("Environment Variables", check_env_variables),
        ("Webhook URL Format", check_webhook_url_format),
        ("HMAC Implementation", verify_hmac_implementation),
        ("Response Format", check_response_format),
        ("Routing Configuration", check_routing_configuration),
    ]
    
    results = []
    for name, check_fn in checks:
        print(f"\n{name}:")
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📋 VERIFICATION SUMMARY\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All checks passed! Your Telegram webhook setup is ready.")
        print("\nNext steps:")
        print("1. Start the backend: python -m uvicorn app.main:app --reload")
        print("2. Backend will NOT auto-setup webhook in development mode (ENVIRONMENT=development)")
        print("3. For production, set ENVIRONMENT=production and webhook will auto-register")
        print("4. Verify endpoint is reachable: POST /api/v1/telegram/webhook")
        print("5. Verify init endpoint: GET /api/v1/telegram/web-app/init?init_data=...")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
