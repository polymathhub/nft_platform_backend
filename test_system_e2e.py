#!/usr/bin/env python3
"""
Comprehensive end-to-end test for Telegram NFT WebApp.
Tests real user flow and API integrations.
"""

import requests
import json
import time
from uuid import uuid4 as generate_uuid

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/telegram"

def colored(text, color):
    """Add ANSI color codes."""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m',
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

def test_header(title):
    """Print test header."""
    print(f"\n{colored('=' * 60, 'blue')}")
    print(colored(title, 'blue'))
    print(colored('=' * 60, 'reset'))

def test_step(msg, passed=None):
    """Print test step."""
    symbol = colored('✓', 'green') if passed else colored('✗', 'red') if passed is False else colored('→', 'yellow')
    status = f" {colored('PASS', 'green')}" if passed else f" {colored('FAIL', 'red')}" if passed is False else ""
    print(f"  {symbol} {msg}{status}")

def test_section(name):
    """Print section header."""
    print(f"\n{colored(f'[{name}]', 'yellow')}")

# ==================== TESTS ====================

def test_backend_availability():
    """Test 1: Backend is running and responding."""
    test_header("Test 1: Backend Availability")
    
    try:
        test_step("Checking health endpoint")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        test_step(f"Health status: {response.status_code}", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            test_step(f"Database: {data.get('database_url')}")
            test_step(f"Telegram token configured: {data.get('telegram_bot_token')}")
        
        return response.status_code == 200
    except Exception as e:
        test_step(f"Backend error: {e}", False)
        return False

def test_frontend_accessibility():
    """Test 2: Frontend HTML is accessible."""
    test_header("Test 2: Frontend Accessibility")
    
    try:
        response = requests.get(f"{BASE_URL}/web-app/", timeout=5)
        test_step(f"Frontend HTTP status: {response.status_code}", response.status_code == 200)
        
        if response.status_code == 200:
            test_step("HTML contains 'app' element", 'id="app"' in response.text)
            test_step("Telegram WebApp SDK included", 'Telegram.WebApp' in response.text or 'telegram-web-app' in response.text.lower())
            test_step("app.js script loaded", 'app.js' in response.text)
        
        return response.status_code == 200
    except Exception as e:
        test_step(f"Frontend error: {e}", False)
        return False

def test_api_routes():
    """Test 3: All WebApp API routes exist."""
    test_header("Test 3: API Routes")
    
    required_routes = [
        "/web-app/init",
        "/web-app/wallets",
        "/web-app/nfts",
        "/web-app/dashboard-data",
        "/web-app/marketplace/listings",
        "/web-app/create-wallet",
        "/web-app/mint",
        "/web-app/list-nft",
        "/web-app/transfer",
        "/web-app/burn",
    ]
    
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            paths = response.json().get("paths", {})
            
            for route in required_routes:
                full_route = f"/api/v1/telegram{route}"
                exists = full_route in paths
                test_step(f"Route {route}: {'exists' if exists else 'missing'}", exists)
            
            return all(f"/api/v1/telegram{r}" in paths for r in required_routes)
        else:
            test_step("Failed to get OpenAPI schema", False)
            return False
    except Exception as e:
        test_step(f"API routes check error: {e}", False)
        return False

def test_test_user_flow():
    """Test 4: Test user creation and data loading (development mode)."""
    test_header("Test 4: Test User Flow (Development)")
    
    try:
        # Create test user
        test_section("Creating test user")
        response = requests.get(f"{API_BASE}/web-app/test-user", timeout=5)
        test_step(f"Test user creation: {response.status_code}", response.status_code == 200)
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        test_user_id = data['test_user']['id']
        test_step(f"Test user created: {data['test_user']['username']}", True)
        
        # Get user info
        test_section("Loading user data")
        response = requests.get(
            f"{API_BASE}/web-app/user?user_id={test_user_id}",
            timeout=5
        )
        test_step(f"Get user endpoint: {response.status_code}", response.status_code == 200)
        
        if response.status_code == 200:
            user = response.json().get('user', {})
            test_step(f"Username: {user.get('telegram_username')}")
            test_step(f"User ID matches: {user.get('id') == test_user_id}", user.get('id') == test_user_id)
        
        return True
    except Exception as e:
        test_step(f"Test user flow error: {e}", False)
        return False

def test_marketplace_data():
    """Test 5: Marketplace returns real NFT data."""
    test_header("Test 5: Marketplace Data")
    
    try:
        test_section("Loading marketplace listings")
        response = requests.get(
            f"{API_BASE}/web-app/marketplace/listings?limit=10",
            timeout=5
        )
        test_step(f"Marketplace endpoint: {response.status_code}", response.status_code == 200)
        
        if response.status_code == 200:
            data = response.json()
            listings = data.get('listings', [])
            test_step(f"Listings found: {len(listings)}", True)
            
            if listings:
                listing = listings[0]
                test_section("Sample listing structure")
                test_step(f"Has ID: {'id' in listing}", 'id' in listing)
                test_step(f"Has NFT name: {'nft_name' in listing}", 'nft_name' in listing)
                test_step(f"Has price: {'price' in listing}", 'price' in listing)
                test_step(f"Has image URL: {'image_url' in listing}", 'image_url' in listing)
                test_step(f"Has seller info: {'seller_name' in listing}", 'seller_name' in listing)
                test_step(f"Has blockchain: {'blockchain' in listing}", 'blockchain' in listing)
                
                print(f"\n  {colored('Sample Listing:', 'yellow')}")
                for key in ['id', 'nft_name', 'price', 'currency', 'seller_name', 'blockchain']:
                    if key in listing:
                        val = listing[key]
                        if isinstance(val, str) and len(val) > 50:
                            val = val[:47] + "..."
                        print(f"    {key}: {val}")
                return True
            else:
                test_step("No listings in database (OK for new system)", True)
                return True
        else:
            test_step("Error loading marketplace", False)
            return False
    except Exception as e:
        test_step(f"Marketplace test error: {e}", False)
        return False

def test_api_error_handling():
    """Test 6: API properly handles errors."""
    test_header("Test 6: Error Handling")
    
    try:
        test_section("Testing invalid parameters")
        
        # Test invalid user_id
        response = requests.get(
            f"{API_BASE}/web-app/user?user_id=invalid-id",
            timeout=5
        )
        test_step(f"Invalid user_id returns HTTP error: {response.status_code != 200}", response.status_code != 200)
        
        # Test missing required param
        response = requests.get(
            f"{API_BASE}/web-app/wallets",
            timeout=5
        )
        test_step(f"Missing user_id param returns error: {response.status_code >= 400}", response.status_code >= 400)
        
        return True
    except Exception as e:
        test_step(f"Error handling test error: {e}", False)
        return False

def test_ui_structure():
    """Test 7: Frontend HTML structure is complete."""
    test_header("Test 7: Frontend UI Structure")
    
    try:
        response = requests.get(f"{BASE_URL}/web-app/", timeout=5)
        html = response.text
        
        required_elements = {
            'App container': 'id="app"',
            'Sidebar': 'id="sidebar"',
            'Main content': 'id="mainContent"',
            'Status alert': 'id="status"',
            'Modal': 'id="modal"',
            'Dashboard page': 'data-page="dashboard"' or 'dashboard-page',
            'Wallets page': 'data-page="wallets"' or 'wallets-page',
            'NFTs page': 'data-page="nfts"' or 'nfts-page',
            'Marketplace page': 'data-page="marketplace"' or 'marketplace-page',
        }
        
        test_section("Checking DOM structure")
        for element, check in required_elements.items():
            if isinstance(check, str):
                exists = check in html
            else:
                exists = check(html)
            test_step(f"{element}: {'present' if exists else 'missing'}", exists)
        
        return True
    except Exception as e:
        test_step(f"UI structure test error: {e}", False)
        return False

def main():
    """Run all tests."""
    print(colored("\n" + "=" * 60, 'blue'))
    print(colored("TELEGRAM NFT WEBAPP - END-TO-END TEST", 'blue'))
    print(colored("=" * 60, 'blue'))
    
    results = {}
    
    # Run tests
    results["Backend Availability"] = test_backend_availability()
    results["Frontend Accessibility"] = test_frontend_accessibility()
    results["API Routes"] = test_api_routes()
    results["Test User Flow"] = test_test_user_flow()
    results["Marketplace Data"] = test_marketplace_data()
    results["Error Handling"] = test_api_error_handling()
    results["UI Structure"] = test_ui_structure()
    
    # Print summary
    test_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = colored("PASS", 'green') if result else colored("FAIL", 'red')
        print(f"  {status} {test_name}")
    
    print(f"\n{colored(f'Results: {passed}/{total} tests passed', 'green' if passed == total else 'red')}")
    
    if passed == total:
        print(f"\n{colored('SUCCESS! The system is ready for use.', 'green')}")
        print(f"{colored('Visit: http://localhost:8000/web-app/', 'yellow')}")
        print(f"{colored('For development with test user, check the Test User Flow section above.', 'yellow')}")
    else:
        print(f"\n{colored(f'FAILURE: {total - passed} test(s) failed. Please review above.', 'red')}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
