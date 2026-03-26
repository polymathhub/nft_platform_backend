#!/bin/bash
cd "C:\\Users\\HomePC\\Downloads\\nft_platform_backend-main (1)\\nft_platform_backend-main"

# Array of files to delete
files=(
  "ACTION_REQUIRED.md"
  "ALEMBIC_COLUMN_SIZE_FIX.md"
  "alembic_error.log"
  "alembic_migration.log"
  "ALEMBIC_MIGRATION_STANDARDS.md"
  "alembic_output.log"
  "alembic_upgrade.log"
  "API_ENDPOINTS_FIXED.md"
  "API_FIX_COMPLETE.md"
  "AUTHENTICATION_AND_ROUTING_FIX.md"
  "DEPLOYMENT_COMPLETE.md"
  "DEPLOYMENT_READY.md"
  "DEPLOYMENT_TRIGGER.md"
  "DETAILED_MIGRATION_FIXES.md"
  "FRONTEND_BACKEND_AUDIT_REPORT.md"
  "FRONTEND_BACKEND_FIXES_APPLIED.md"
  "GIT_COMMIT_GUIDE.md"
  "INTEGRATION_STATUS.md"
  "migration_output.log"
  "migration_output2.log"
  "migration_output3.log"
  "NAVIGATION_REDIRECT_FIXES.md"
  "NFT_MINTING_FIXES.md"
  "README_MIGRATION_FIXES.md"
  "RESTART_REQUIRED.md"
  "SECURITY_FIXES_APPLIED.md"
  "SECURITY_VULNERABILITIES.md"
  "SECURITY_VULNERABILITY_AUDIT.md"
  "TELEGRAM_AUTH_DEBUG.md"
  "TELEGRAM_AUTH_IMPLEMENTATION.md"
  "TELEGRAM_AUTH_MIGRATION_FIXES.md"
  "TELEGRAM_AUTH_REFACTOR_COMPLETE.md"
  "TELEGRAM_MINI_APP_FIX.md"
  "TELEGRAM_MINI_APP_SETUP.md"
  "TONCONNECT_TELEGRAM_VERIFICATION_REPORT.md"
  "commit_changes.bat"
  "fix_alembic_column_size.ps1"
  "run_git.js"
  "run_git.py"
  "run_git_commands.bat"
  "PUSH_CHANGES.bat"
  "push_frontend_changes.bat"
  "push_changes.js"
  "push_changes.py"
  "app.log"
)

# Delete files
for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    rm -f "$file"
    echo "Deleted: $file"
  fi
done

# Run git add -A
echo "Running: git add -A"
git add -A

# Run git commit
echo "Running: git commit"
git commit -m "feat: Add user profile pictures and real-time Socket.io notifications

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

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

# Run git push
echo "Running: git push origin main"
git push origin main

# Show git status
echo "=== GIT STATUS ==="
git status

# Show git log
echo "=== GIT LOG (Last 5 commits) ==="
git log --oneline -n 5
