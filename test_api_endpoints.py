#!/usr/bin/env python3
"""
Test script to verify API endpoints are working correctly.
"""

import requests
import json
import asyncio
from urllib.parse import quote

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json() if response.text else 'empty'}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_routes():
    """List all available routes."""
    print("\n=== Available Routes ===")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            routes = list(data.get("paths", {}).keys())
            print(f"Found {len(routes)} routes")
            
            # Filter to telegram routes
            telegram_routes = [r for r in routes if "telegram" in r.lower() or "web-app" in r.lower()]
            print(f"\nTelegram/WebApp routes ({len(telegram_routes)}):")
            for route in sorted(telegram_routes):
                print(f"  {route}")
            return True
        else:
            print(f"Failed to get OpenAPI schema: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_test_user():
    """Test the test-user endpoint (for development)."""
    print("\n=== Testing Test-User Endpoint (Development) ===")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/telegram/web-app/test-user", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return data.get("success", False)
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_marketplace_listings():
    """Test marketplace listings without auth."""
    print("\n=== Testing Marketplace Listings (No Auth) ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/telegram/web-app/marketplace/listings",
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            listings = data.get("listings", [])
            print(f"Found {len(listings)} listings")
            if listings:
                print(f"\nSample listing:")
                print(json.dumps(listings[0], indent=2))
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("API ENDPOINT TEST SUITE")
    print("=" * 60)
    
    results = {
        "Health Check": test_health(),
        "Routes Listing": test_routes(),
        "Test User Creation": test_test_user(),
        "Marketplace Listings": test_marketplace_listings(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed!"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
