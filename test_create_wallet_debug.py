#!/usr/bin/env python3
"""
Test create wallet endpoint with detailed logging
"""

import asyncio
import httpx
import json
import logging
import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fake Telegram init_data for testing
def get_test_init_data():
    """Generate test Telegram init_data"""
    import hashlib
    import hmac
    from urllib.parse import urlencode
    
    # Simulate Telegram data
    test_user = {
        "id": 123456789,
        "is_bot": False,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "en"
    }
    
    import json
    user_json = json.dumps(test_user, separators=(',', ':'), sort_keys=True)
    
    data = {
        "user": user_json,
        "auth_date": str(int(datetime.now().timestamp())),
        "hash": "dummy"
    }
    
    # Sign with dummy secret or just return as-is for testing
    init_data = urlencode(data)
    return init_data


async def test_create_wallet():
    """Test create wallet endpoint"""
    
    BASE_URL = "http://localhost:8000"
    
    # Test data
    init_data = get_test_init_data()
    
    request_body = {
        "blockchain": "ethereum",
        "wallet_type": "custodial",
        "init_data": init_data,
    }
    
    logger.info(f"Testing create wallet endpoint")
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"Request body: {json.dumps(request_body, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/web-app/create-wallet",
                json=request_body,
                headers={"Content-Type": "application/json"},
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                logger.info(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except Exception as e:
                logger.error(f"Failed to parse response as JSON: {e}")
                logger.info(f"Response text: {response.text[:500]}")
            
            if response.status_code != 200:
                logger.error(f"Create wallet failed with status {response.status_code}")
                return False
            
            logger.info("Create wallet test passed!")
            return True
            
    except httpx.ConnectError:
        logger.error(f"Failed to connect to {BASE_URL}")
        logger.info("Make sure the backend is running with: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    result = asyncio.run(test_create_wallet())
    sys.exit(0 if result else 1)
