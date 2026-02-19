#!/usr/bin/env python3
"""
Test API endpoints with proper authentication
"""
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 80)
print("TESTING API ENDPOINTS")
print("=" * 80)

# Simulate minimal Telegram init_data
mock_init_data = "query_id=test&user=%7B%22id%22%3A123%7D&auth_date=1234567890&hash=abc"

print("\n1. Testing GET /api/v1/telegram/web-app/init with init_data...")
response = client.get(f"/api/v1/telegram/web-app/init?init_data={mock_init_data}")
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   Response: {response.text[:200]}")

print("\n2. Testing POST /api/v1/telegram/web-app/create-wallet...")
response = client.post(
    "/api/v1/telegram/web-app/create-wallet",
    json={
        "blockchain": "ethereum",
        "wallet_type": "custodial",
        "is_primary": False,
        "init_data": mock_init_data
    }
)
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    data = response.json() if response.headers.get('content-type') == 'application/json' else {}
    print(f"   Response: {json.dumps(data, indent=2)[:300]}")

print("\n3. Testing GET /api/v1/telegram/web-app/wallets...")
response = client.get(f"/api/v1/telegram/web-app/wallets?user_id=123&init_data={mock_init_data}")
print(f"   Status: {response.status_code}")
if response.status_code not in [200, 401]:
    print(f"   Response: {response.text[:200]}")

print("\n4. Testing raw `/telegram/` prefix...")
response = client.get(f"/telegram/web-app/init?init_data={mock_init_data}")
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   Response: {response.text[:200]}")

print("\n" + "=" * 80)
