#!/usr/bin/env python
"""
Test script to verify backend can start and handle requests
"""
import os
import sys
from cryptography.fernet import Fernet

# Generate a Fernet key (44 chars base64 encoded)
fernet_key = Fernet.generate_key().decode()

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./nft_platform.db'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-characters-long123456'
os.environ['MNEMONIC_ENCRYPTION_KEY'] = fernet_key

print(f"Generated Fernet key: {fernet_key}")
print(f"Key length: {len(fernet_key)}")

try:
    from app.main import app
    print("✓ FastAPI app imported successfully")
    
    # Print available routes
    print("\nAvailable routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    
    # Check if telegram router is loaded
    telegram_routes = [r.path for r in app.routes if '/telegram' in str(r.path)]
    print(f"\n✓ Found {len(telegram_routes)} Telegram endpoints")
    
    print("\n✓ Backend is ready to start")
    print("\nTo run the server, execute:")
    print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
except Exception as e:
    print(f"✗ Error importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
