#!/usr/bin/env python3
import os
import subprocess
import sys

# Change to the project directory
os.chdir(r"C:\Users\HomePC\Downloads\nft_platform_backend-main (1)\nft_platform_backend-main")

# List of files to delete
files_to_delete = [
    "ACTION_REQUIRED.md",
    "ALEMBIC_COLUMN_SIZE_FIX.md",
    "alembic_error.log",
    "alembic_migration.log",
    "ALEMBIC_MIGRATION_STANDARDS.md",
    "alembic_output.log",
    "alembic_upgrade.log",
    "API_ENDPOINTS_FIXED.md",
    "API_FIX_COMPLETE.md",
    "AUTHENTICATION_AND_ROUTING_FIX.md",
    "DEPLOYMENT_COMPLETE.md",
    "DEPLOYMENT_READY.md",
    "DEPLOYMENT_TRIGGER.md",
    "DETAILED_MIGRATION_FIXES.md",
    "FRONTEND_BACKEND_AUDIT_REPORT.md",
    "FRONTEND_BACKEND_FIXES_APPLIED.md",
    "GIT_COMMIT_GUIDE.md",
    "INTEGRATION_STATUS.md",
    "migration_output.log",
    "migration_output2.log",
    "migration_output3.log",
    "NAVIGATION_REDIRECT_FIXES.md",
    "NFT_MINTING_FIXES.md",
    "README_MIGRATION_FIXES.md",
    "RESTART_REQUIRED.md",
    "SECURITY_FIXES_APPLIED.md",
    "SECURITY_VULNERABILITIES.md",
    "SECURITY_VULNERABILITY_AUDIT.md",
    "TELEGRAM_AUTH_DEBUG.md",
    "TELEGRAM_AUTH_IMPLEMENTATION.md",
    "TELEGRAM_AUTH_MIGRATION_FIXES.md",
    "TELEGRAM_AUTH_REFACTOR_COMPLETE.md",
    "TELEGRAM_MINI_APP_FIX.md",
    "TELEGRAM_MINI_APP_SETUP.md",
    "TONCONNECT_TELEGRAM_VERIFICATION_REPORT.md",
    "commit_changes.bat",
    "fix_alembic_column_size.ps1",
    "run_git.js",
    "run_git.py",
    "run_git_commands.bat",
    "PUSH_CHANGES.bat",
    "push_frontend_changes.bat",
    "push_changes.js",
    "push_changes.py",
    "app.log",
]

# Delete files
deleted_count = 0
for file_to_delete in files_to_delete:
    try:
        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)
            print(f"Deleted: {file_to_delete}")
            deleted_count += 1
    except Exception as e:
        print(f"Error deleting {file_to_delete}: {e}")

print(f"\nTotal files deleted: {deleted_count}/{len(files_to_delete)}")

# Run git add -A
print("\nRunning: git add -A")
result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
print(result.stdout if result.stdout else "No output")
if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

# Run git commit
print("\nRunning: git commit")
commit_message = """feat: Add user profile pictures and real-time Socket.io notifications

Features:
- Display actual user profile pictures in header and profile page
- Implement Socket.io real-time notifications system
- Centralized NotificationManager for all event types
- Beautiful toast notifications with animations

Pages Updated:
- profile.html: Profile picture loading, Socket.io integration
- mint.html: Real-time minting notifications
- wallet.html: Wallet connection notifications
- navbar.js: Header avatar with profile picture

Notifications Supported:
- nft:minted - NFT creation notifications
- nft:listed - NFT listing notifications
- nft:sold - Sale confirmations
- referral:earned - Referral earnings
- wallet:connected - Wallet connection confirmations

Technical Details:
- Socket.io integration with Telegram auth
- Auto-reconnection with exponential backoff
- Production-grade error handling
- Mobile-first responsive design
- No emojis, production-standard code

Files Created:
- app/static/webapp/js/notifications.js - NotificationManager class

Cleanup:
- Removed all instruction and fix documentation files
- Kept only production code and necessary configs

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"""

result = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
print(result.stdout if result.stdout else "Commit created")
if result.returncode != 0 and "nothing to commit" not in result.stdout.lower():
    print(f"Error: {result.stderr}")
    sys.exit(1)

# Run git push
print("\nRunning: git push origin main")
result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
print(result.stdout if result.stdout else "Push completed")
if result.returncode != 0:
    print(f"Error: {result.stderr}")

# Show git status
print("\n=== GIT STATUS ===")
result = subprocess.run(["git", "status"], capture_output=True, text=True)
print(result.stdout)

# Show git log
print("\n=== GIT LOG (Last 5 commits) ===")
result = subprocess.run(["git", "log", "--oneline", "-n", "5"], capture_output=True, text=True)
print(result.stdout)

print("\n=== OPERATION COMPLETE ===")
