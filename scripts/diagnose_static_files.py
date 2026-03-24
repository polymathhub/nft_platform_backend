#!/usr/bin/env python3
"""
Diagnostic script to verify static files are properly deployed on Railway
Run this in your app to check if frontend files are accessible
"""
import os
import sys
from pathlib import Path

def check_static_structure():
    """Verify static file structure"""
    print("=" * 70)
    print("STATIC FILES DIAGNOSTIC")
    print("=" * 70)
    
    app_dir = Path(__file__).parent.parent / "app"
    static_dir = app_dir / "static"
    webapp_dir = static_dir / "webapp"
    
    print(f"\n📁 App directory: {app_dir}")
    print(f"   Exists: {app_dir.exists()}")
    
    print(f"\n📁 Static directory: {static_dir}")
    print(f"   Exists: {static_dir.exists()}")
    
    if not static_dir.exists():
        print("   ❌ ERROR: Static directory not found!")
        return False
    
    print(f"\n📁 Webapp directory: {webapp_dir}")
    print(f"   Exists: {webapp_dir.exists()}")
    
    if not webapp_dir.exists():
        print("   ❌ ERROR: Webapp directory not found!")
        return False
    
    # Check HTML files
    print("\n📄 HTML Files:")
    html_files = sorted(webapp_dir.glob("*.html"))
    if html_files:
        for f in html_files:
            print(f"   ✓ {f.name} ({f.stat().st_size} bytes)")
    else:
        print("   ❌ No HTML files found!")
    
    # Check CSS files
    print("\n🎨 CSS Files:")
    css_dir = webapp_dir / "css"
    if css_dir.exists():
        css_files = sorted(css_dir.glob("*.css"))
        if css_files:
            for f in css_files:
                print(f"   ✓ {f.name} ({f.stat().st_size} bytes)")
        else:
            print("   ⚠ CSS directory exists but is empty")
    else:
        print("   ❌ CSS directory not found!")
    
    # Check JS files
    print("\n📜 JS Files:")
    js_dir = webapp_dir / "js"
    if js_dir.exists():
        js_files = sorted(js_dir.glob("*.js"))
        if js_files:
            for f in js_files[:10]:  # Show first 10
                print(f"   ✓ {f.name} ({f.stat().st_size} bytes)")
            if len(js_files) > 10:
                print(f"   ... and {len(js_files) - 10} more JS files")
        else:
            print("   ⚠ JS directory exists but is empty")
    else:
        print("   ❌ JS directory not found!")
    
    # Check vendor files
    print("\n📦 Vendor Files:")
    vendor_dir = static_dir / "vendor"
    if vendor_dir.exists():
        tonconnect_dir = vendor_dir / "tonconnect"
        if tonconnect_dir.exists():
            files = sorted(tonconnect_dir.glob("*"))
            if files:
                for f in files[:5]:
                    print(f"   ✓ vendor/tonconnect/{f.name}")
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more vendor files")
            else:
                print("   ⚠ Vendor directory is empty")
        else:
            print("   ⚠ TONConnect vendor subdirectory not found")
    else:
        print("   ⚠ Vendor directory not found")
    
    # Check permissions
    print("\n🔒 Permissions Check:")
    critical_files = [
        webapp_dir / "dashboard.html",
        css_dir / "styles.css" if css_dir.exists() else None,
        js_dir / "app.js" if js_dir.exists() else None,
    ]
    
    for f in [x for x in critical_files if x]:
        if f.exists():
            mode = oct(f.stat().st_mode)
            readable = os.access(f, os.R_OK)
            print(f"   {f.name}: {mode} {'✓ readable' if readable else '❌ NOT readable'}")
        else:
            print(f"   {f.name}: ⚠ Not found")
    
    print("\n" + "=" * 70)
    return True

if __name__ == "__main__":
    success = check_static_structure()
    sys.exit(0 if success else 1)
