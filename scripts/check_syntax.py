#!/usr/bin/env python3
"""
Pre-flight syntax check - validates all Python files can be imported
Runs before Docker container starts to catch syntax errors early
"""
import sys
import py_compile
import os
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    """Scan all Python files in app/ directory"""
    errors = []
    files_checked = 0
    app_dir = Path('/app/app')
    
    if not app_dir.exists():
        print("[⚠️ WARNING] /app/app directory not found")
        return 0
    
    # Recursively find all .py files
    py_files = list(app_dir.rglob('*.py'))
    
    if not py_files:
        print("[⚠️ WARNING] No Python files found in /app/app")
        return 0
    
    print(f"[CHECK] Validating syntax for {len(py_files)} Python files...")
    
    for py_file in sorted(py_files):
        # Skip __pycache__
        if '__pycache__' in str(py_file):
            continue
        
        files_checked += 1
        is_valid, error = check_syntax(py_file)
        
        if is_valid:
            print(f"  ✅ {py_file.relative_to('/app')}")
        else:
            print(f"  ❌ {py_file.relative_to('/app')}")
            errors.append({
                'file': str(py_file.relative_to('/app')),
                'error': error
            })
    
    print(f"\n[RESULT] Checked {files_checked} files")
    
    if errors:
        print(f"\n[ERROR] Found {len(errors)} syntax errors:\n")
        for err in errors:
            print(f"  📄 {err['file']}")
            print(f"     {err['error']}\n")
        return 1
    
    print("✅ All Python files are syntactically valid!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
