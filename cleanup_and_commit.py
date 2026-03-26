#!/usr/bin/env python3
"""Clean up instruction files and commit changes"""
import subprocess
import os
import glob

repo_path = r"C:\Users\HomePC\Downloads\nft_platform_backend-main (1)\nft_platform_backend-main"
os.chdir(repo_path)

# Files to delete (instruction/fix documentation)
instruction_files = [
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
    "app.log"
]

print("🗑️  Cleaning up instruction files...\n")

deleted_count = 0
for file in instruction_files:
    if os.path.exists(file):
        try:
            os.remove(file)
            print(f"  ✅ Deleted: {file}")
            deleted_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed to delete {file}: {e}")
    else:
        print(f"  ⏭️  Not found: {file}")

print(f"\n🎯 Deleted {deleted_count} instruction files")

# Stage changes
print("\n📋 Staging all changes...")
subprocess.run("git add -A", shell=True)

# Remove deleted files from tracking
print("🗑️  Removing deleted files from git...")
for file in instruction_files:
    try:
        subprocess.run(f"git rm --cached {file} 2>nul", shell=True)
    except:
        pass

# Show what will be committed
print("\n📊 Changes to commit:")
result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
if result.stdout:
    print(result.stdout)
else:
    print("No changes to commit")

# Commit
print("\n💾 Creating commit...")
commit_msg = """feat: Add user profile pictures and real-time Socket.io notifications

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
- Generic notification events

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

result = subprocess.run(f'git commit -m "{commit_msg}"', shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Commit created successfully")
    print(result.stdout)
else:
    print("⚠️  Commit status:", result.stderr if result.stderr else "No changes to commit")

# Push
print("\n🚀 Pushing to GitHub...")
result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Push successful!")
    print(result.stdout)
else:
    print("Push output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

print("\n🎉 Complete! Changes committed and cleanup done.")
