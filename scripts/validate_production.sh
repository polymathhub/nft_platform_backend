#!/usr/bin/env bash
# Pre-deployment validation script for production
# Validates the entire project before Docker build

set -e

echo "========================================="
echo "  Pre-Deployment Validation Script"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

# 1. Check Python syntax
echo "[1/7] Checking Python syntax..."
python3 -m py_compile app/utils/auth.py 2>/dev/null && \
    print_result 0 "auth.py syntax is valid" || \
    print_result 1 "auth.py has syntax errors"

# 2. Check all Python files
echo "[2/7] Scanning all Python files for syntax errors..."
find app -name "*.py" -type f | while read file; do
    python3 -m py_compile "$file" 2>/dev/null || {
        echo "  ⚠️  Syntax error in: $file"
        return 1
    }
done
[ $? -eq 0 ] && print_result 0 "All Python files are valid" || print_result 1 "Some Python files have syntax errors"

# 3. Check requirements.txt
echo "[3/7] Checking requirements.txt..."
[ -f requirements.txt ] && \
    print_result 0 "requirements.txt exists" || \
    print_result 1 "requirements.txt missing"

# 4. Check Dockerfile
echo "[4/7] Checking Dockerfile..."
[ -f Dockerfile ] && \
    print_result 0 "Dockerfile exists" || \
    print_result 1 "Dockerfile missing"

# 5. Check entrypoint.sh
echo "[5/7] Checking entrypoint.sh..."
[ -x entrypoint.sh ] && \
    print_result 0 "entrypoint.sh is executable" || \
    print_result 1 "entrypoint.sh not executable or missing"

# 6. Check Git status
echo "[6/7] Checking Git status..."
if git status --porcelain | grep -q ""; then
    print_result 1 "Uncommitted changes detected - commit before deployment"
else
    print_result 0 "Git working directory is clean"
fi

# 7. Check for debug code
echo "[7/7] Scanning for debug statements (print, console.log, etc)..."
DEBUG_FOUND=$(grep -r "print(" app --include="*.py" | grep -v "logger" | grep -v "def print" | wc -l)
if [ "$DEBUG_FOUND" -gt 0 ]; then
    print_result 1 "Found $DEBUG_FOUND debug print statements"
else
    print_result 0 "No debug print statements found"
fi

# Summary
echo ""
echo "========================================="
echo "  Validation Summary"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready for deployment.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Build Docker image: docker build --no-cache -t nft-platform:latest ."
    echo "  2. Test locally: docker run --rm nft-platform:latest"
    echo "  3. Push to registry and deploy"
    exit 0
else
    echo -e "${RED}❌ Validation failed! Fix issues before deploying.${NC}"
    exit 1
fi
