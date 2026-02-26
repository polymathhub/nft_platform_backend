#!/usr/bin/env python3
"""
COMPREHENSIVE PRODUCTION READINESS VERIFICATION
Validates all backend systems, API contracts, and frontend integration.
"""

import asyncio
import sys
import json
from typing import Dict, List, Tuple
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class VerificationReport:
    def __init__(self):
        self.tests: Dict[str, Dict] = {}
        self.categories = {
            "BACKEND_IMPORTS": [],
            "DATABASE_SCHEMA": [],
            "API_ENDPOINTS": [],
            "AUTH_FLOW": [],
            "FRONTEND_CONTRACT": [],
            "TELEGRAM_INTEGRATION": [],
            "ERROR_HANDLING": [],
        }

    def add_test(self, category: str, test_name: str, passed: bool, message: str = ""):
        if category not in self.categories:
            self.categories[category] = []
        
        self.categories[category].append({
            "name": test_name,
            "passed": passed,
            "message": message
        })

    def print_report(self):
        print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}{BLUE}PRODUCTION READINESS VERIFICATION REPORT{RESET}")
        print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
        
        total_tests = 0
        total_passed = 0
        
        for category, tests in self.categories.items():
            if not tests:
                continue
            
            passed_count = sum(1 for t in tests if t["passed"])
            total_tests += len(tests)
            total_passed += passed_count
            
            status_color = GREEN if passed_count == len(tests) else YELLOW if passed_count > 0 else RED
            status_icon = "✓" if passed_count == len(tests) else "⚠" if passed_count > 0 else "✗"
            
            print(f"{status_color}{BOLD}{status_icon} {category}{RESET} ({passed_count}/{len(tests)})")
            for test in tests:
                icon = f"{GREEN}✓{RESET}" if test["passed"] else f"{RED}✗{RESET}"
                print(f"  {icon} {test['name']}")
                if test["message"]:
                    print(f"      {BLUE}→{RESET} {test['message']}")
            print()
        
        print(f"{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"TOTAL: {total_passed}/{total_tests} tests passed")
        
        if total_passed == total_tests:
            print(f"{GREEN}{BOLD}✓ ALL SYSTEMS READY FOR PRODUCTION{RESET}")
            return 0
        else:
            print(f"{RED}{BOLD}✗ SOME SYSTEMS REQUIRE FIXES{RESET}")
            return 1

report = VerificationReport()

# ============================================================================
# TEST 1: BACKEND IMPORTS
# ============================================================================
print(f"{BLUE}[1/7]{RESET} Verifying backend imports...")

try:
    from app.config import get_settings
    report.add_test("BACKEND_IMPORTS", "Config loading", True)
except Exception as e:
    report.add_test("BACKEND_IMPORTS", "Config loading", False, str(e))
    sys.exit(1)

try:
    from app.utils.logger import logger
    report.add_test("BACKEND_IMPORTS", "Logger export", True)
except Exception as e:
    report.add_test("BACKEND_IMPORTS", "Logger export", False, str(e))

try:
    from app.database import init_db, close_db, get_db_session
    report.add_test("BACKEND_IMPORTS", "Database layer", True)
except Exception as e:
    report.add_test("BACKEND_IMPORTS", "Database layer", False, str(e))

try:
    from app.models import User, Wallet, NFT
    report.add_test("BACKEND_IMPORTS", "Core models", True)
except Exception as e:
    report.add_test("BACKEND_IMPORTS", "Core models", False, str(e))

try:
    from app.routers import (
        auth_router, wallet_router, nft_router, 
        marketplace_router, payment_router, referrals_router
    )
    report.add_test("BACKEND_IMPORTS", "All routers", True)
except Exception as e:
    report.add_test("BACKEND_IMPORTS", "All routers", False, str(e))

try:
    from app.services.auth_service import AuthService
    from app.security.auth import get_current_user
    report.add_test("BACKEND_IMPORTS", "Authentication services", True)
except Exception as e:
    report.add_test("BACKEND_IMPORTS", "Authentication services", False, str(e))

# ============================================================================
# TEST 2: DATABASE SCHEMA
# ============================================================================
print(f"{BLUE}[2/7]{RESET} Verifying database schema...")

async def test_database():
    try:
        from app.database import init_db
        from app.models import User, Wallet, NFT, Listing
        
        await init_db()
        report.add_test("DATABASE_SCHEMA", "Database initialization", True)
        
        # Verify key models are defined with correct fields
        from sqlalchemy import inspect as sync_inspect
        from sqlalchemy.orm import declarative_base
        
        # Check User model has required fields
        user_fields = {c.name for c in User.__table__.columns}
        required_user_fields = {"id", "telegram_id", "is_active", "is_verified"}
        
        missing_fields = required_user_fields - user_fields
        
        if not missing_fields:
            report.add_test("DATABASE_SCHEMA", "User model fields", True)
        else:
            report.add_test("DATABASE_SCHEMA", "User model fields", False,
                          f"Missing: {missing_fields}")
        
        # Check other models exist
        required_models = [User, Wallet, NFT, Listing]
        report.add_test("DATABASE_SCHEMA", "Core models defined", True)
        
    except Exception as e:
        report.add_test("DATABASE_SCHEMA", "Database models", False, str(e))

asyncio.run(test_database())

# ============================================================================
# TEST 3: API ENDPOINTS ENUMERATION
# ============================================================================
print(f"{BLUE}[3/7]{RESET} Verifying API endpoints...")

try:
    from app.main import app
    routes = []
    
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({"path": route.path, "methods": route.methods})
    
    # Check key endpoints exist
    critical_endpoints = [
        "/api/v1/telegram/web-app/init",
        "/api/v1/telegram/web-app/user",
        "/api/v1/telegram/web-app/wallets",
        "/api/v1/telegram/web-app/nfts",
        "/api/v1/telegram/web-app/mint",
        "/api/v1/telegram/web-app/marketplace/listings",
        "/api/v1/payments/balance",
        "/api/v1/referrals/me",
    ]
    
    found_routes = {r["path"] for r in routes}
    
    # Use prefix matching for endpoints
    found = sum(1 for endpoint in critical_endpoints 
                if any(endpoint in route for route in found_routes))
    
    report.add_test("API_ENDPOINTS", f"Critical endpoints ({found}/{len(critical_endpoints)})", 
                   found == len(critical_endpoints),
                   f"Total routes available: {len(routes)}")
    
except Exception as e:
    report.add_test("API_ENDPOINTS", "Endpoint enumeration", False, str(e))

# ============================================================================
# TEST 4: AUTH FLOW CONTRACT
# ============================================================================
print(f"{BLUE}[4/7]{RESET} Verifying auth flow contract...")

try:
    # Check initSession endpoint signature
    from app.routers.telegram_mint_router import web_app_init
    report.add_test("AUTH_FLOW", "Web app init endpoint exists", True)
except Exception as e:
    report.add_test("AUTH_FLOW", "Web app init endpoint exists", False, str(e))

try:
    from app.services.auth_service import AuthService
    methods = dir(AuthService)
    
    required_methods = ["authenticate_telegram", "register_user", "authenticate_user"]
    missing = [m for m in required_methods if not hasattr(AuthService, m)]
    
    if not missing:
        report.add_test("AUTH_FLOW", "Auth service methods", True)
    else:
        report.add_test("AUTH_FLOW", "Auth service methods", False, f"Missing: {missing}")
        
except Exception as e:
    report.add_test("AUTH_FLOW", "Auth service methods", False, str(e))

# ============================================================================
# TEST 5: FRONTEND CONTRACT
# ============================================================================
print(f"{BLUE}[5/7]{RESET} Verifying frontend integration contract...")

try:
    app_js_path = Path("app/static/webapp/app.js")
    if app_js_path.exists():
        content = app_js_path.read_text()
        
        # Check for mock data
        has_mock = any(phrase in content for phrase in 
                      ["mock", "dummy", "test_user", "hardcoded", "TODO"])
        
        if has_mock:
            report.add_test("FRONTEND_CONTRACT", "No mock data", False, 
                          "Mock or test data found in app.js")
        else:
            report.add_test("FRONTEND_CONTRACT", "No mock data", True)
        
        # Check API calls use real endpoints
        has_api_calls = "fetch" in content and "API_BASE" in content
        report.add_test("FRONTEND_CONTRACT", "Real API calls", has_api_calls)
        
        # Check Telegram integration
        has_telegram = "Telegram.WebApp" in content
        report.add_test("FRONTEND_CONTRACT", "Telegram integration", has_telegram)
        
        # Check error handling
        has_error_handling = "catch" in content and "error" in content.lower()
        report.add_test("FRONTEND_CONTRACT", "Error handling", has_error_handling)
        
    else:
        report.add_test("FRONTEND_CONTRACT", "app.js exists", False, "File not found")
        
except Exception as e:
    report.add_test("FRONTEND_CONTRACT", "Frontend verification", False, str(e))

# ============================================================================
# TEST 6: TELEGRAM INTEGRATION
# ============================================================================
print(f"{BLUE}[6/7]{RESET} Verifying Telegram integration...")

try:
    settings = get_settings()
    
    has_token = bool(settings.telegram_bot_token)
    report.add_test("TELEGRAM_INTEGRATION", "Bot token configured", has_token)
    
    has_webapp_url = bool(settings.telegram_webapp_url)
    report.add_test("TELEGRAM_INTEGRATION", "WebApp URL configured", has_webapp_url)
    
    if has_webapp_url:
        valid_url = settings.telegram_webapp_url.startswith(("http://", "https://"))
        report.add_test("TELEGRAM_INTEGRATION", "WebApp URL valid", valid_url)
    
except Exception as e:
    report.add_test("TELEGRAM_INTEGRATION", "Settings check", False, str(e))

try:
    from app.routers.telegram_mint_router import verify_telegram_signature
    report.add_test("TELEGRAM_INTEGRATION", "Signature verification available", True)
except Exception as e:
    report.add_test("TELEGRAM_INTEGRATION", "Signature verification", False, str(e))

# ============================================================================
# TEST 7: ERROR HANDLING & STABILITY
# ============================================================================
print(f"{BLUE}[7/7]{RESET} Verifying error handling and stability...")

try:
    from app.main import app
    
    # Check exception handlers exist
    handlers = len(app.exception_handlers)
    has_handlers = handlers > 0
    
    report.add_test("ERROR_HANDLING", f"Exception handlers ({handlers})", has_handlers)
    
except Exception as e:
    report.add_test("ERROR_HANDLING", "Exception handlers", False, str(e))

try:
    # Check middleware
    from app.security_middleware import RequestBodyCachingMiddleware, SecurityHeadersMiddleware
    report.add_test("ERROR_HANDLING", "Security middleware loaded", True)
except Exception as e:
    report.add_test("ERROR_HANDLING", "Security middleware", False, str(e))

# ============================================================================
# FINAL REPORT
# ============================================================================
exit_code = report.print_report()
sys.exit(exit_code)
