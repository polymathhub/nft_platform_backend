#!/usr/bin/env python3
"""
Test script to verify API routes are correctly configured
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("✓ Attempting to import app...")
    from app.main import app
    print("✅ App imported successfully\n")
    
    print("📍 Checking registered routes:")
    print("=" * 70)
    
    target_routes = {
        '/api/auth/profile': ['GET'],
        '/api/auth/me': ['GET'],
        '/api/auth/logout': ['POST'],
        '/api/auth/check': ['GET'],
        '/api/v1/me': ['GET'],
        '/api/v1/user/profile': ['GET'],
    }
    
    found_routes = {}
    for route in app.routes:
        path = route.path if hasattr(route, 'path') else str(route)
        methods = route.methods if hasattr(route, 'methods') else set()
        
        # Check if this is one of our target routes
        for target, target_methods in target_routes.items():
            if path == target:
                found_routes[path] = methods
    
    # Print results
    print("\n📋 Auth/Profile Endpoints:")
    print("-" * 70)
    for target, target_methods in target_routes.items():
        if target in found_routes:
            methods = found_routes[target]
            methods_str = ', '.join(sorted(methods)) if methods else 'N/A'
            print(f"✅ {target:<35} Methods: {methods_str}")
        else:
            print(f"❌ {target:<35} NOT FOUND")
    
    print("\n" + "=" * 70)
    print(f"\n✅ Total routes registered: {len(app.routes)}")
    
    # Show some other routes for verification
    print("\n📝 Sample of other routes:")
    print("-" * 70)
    count = 0
    for route in app.routes:
        if count >= 5:
            break
        path = route.path if hasattr(route, 'path') else str(route)
        if not path.startswith('/api/static') and not path.startswith('/openapi'):
            methods = route.methods if hasattr(route, 'methods') else set()
            methods_str = ', '.join(sorted(methods)) if methods else 'N/A'
            print(f"  {path:<40} Methods: {methods_str}")
            count += 1
    
    print("\n" + "=" * 70)
    print("\n✅ Route verification complete!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
