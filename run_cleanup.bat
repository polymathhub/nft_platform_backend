@echo off
cd /d "C:\Users\HomePC\Downloads\nft_platform_backend-main (1)\nft_platform_backend-main"

echo Deleting cleanup scripts...
if exist cleanup_delete.bat del /f /q cleanup_delete.bat
if exist perform_cleanup.py del /f /q perform_cleanup.py
if exist perform_cleanup.sh del /f /q perform_cleanup.sh

echo Deleting instruction and fix files...
del /f /q ACTION_REQUIRED.md 2>nul
del /f /q ALEMBIC_COLUMN_SIZE_FIX.md 2>nul
del /f /q alembic_error.log 2>nul
del /f /q alembic_migration.log 2>nul
del /f /q ALEMBIC_MIGRATION_STANDARDS.md 2>nul
del /f /q alembic_output.log 2>nul
del /f /q alembic_upgrade.log 2>nul
del /f /q API_ENDPOINTS_FIXED.md 2>nul
del /f /q API_FIX_COMPLETE.md 2>nul
del /f /q AUTHENTICATION_AND_ROUTING_FIX.md 2>nul
del /f /q DEPLOYMENT_COMPLETE.md 2>nul
del /f /q DEPLOYMENT_READY.md 2>nul
del /f /q DEPLOYMENT_TRIGGER.md 2>nul
del /f /q DETAILED_MIGRATION_FIXES.md 2>nul
del /f /q FRONTEND_BACKEND_AUDIT_REPORT.md 2>nul
del /f /q FRONTEND_BACKEND_FIXES_APPLIED.md 2>nul
del /f /q GIT_COMMIT_GUIDE.md 2>nul
del /f /q INTEGRATION_STATUS.md 2>nul
del /f /q migration_output.log 2>nul
del /f /q migration_output2.log 2>nul
del /f /q migration_output3.log 2>nul
del /f /q NAVIGATION_REDIRECT_FIXES.md 2>nul
del /f /q NFT_MINTING_FIXES.md 2>nul
del /f /q README_MIGRATION_FIXES.md 2>nul
del /f /q RESTART_REQUIRED.md 2>nul
del /f /q SECURITY_FIXES_APPLIED.md 2>nul
del /f /q SECURITY_VULNERABILITIES.md 2>nul
del /f /q SECURITY_VULNERABILITY_AUDIT.md 2>nul
del /f /q TELEGRAM_AUTH_DEBUG.md 2>nul
del /f /q TELEGRAM_AUTH_IMPLEMENTATION.md 2>nul
del /f /q TELEGRAM_AUTH_MIGRATION_FIXES.md 2>nul
del /f /q TELEGRAM_AUTH_REFACTOR_COMPLETE.md 2>nul
del /f /q TELEGRAM_MINI_APP_FIX.md 2>nul
del /f /q TELEGRAM_MINI_APP_SETUP.md 2>nul
del /f /q TONCONNECT_TELEGRAM_VERIFICATION_REPORT.md 2>nul
del /f /q commit_changes.bat 2>nul
del /f /q fix_alembic_column_size.ps1 2>nul
del /f /q run_git.js 2>nul
del /f /q run_git.py 2>nul
del /f /q run_git_commands.bat 2>nul
del /f /q PUSH_CHANGES.bat 2>nul
del /f /q push_frontend_changes.bat 2>nul
del /f /q push_changes.js 2>nul
del /f /q push_changes.py 2>nul
del /f /q app.log 2>nul

echo Files deleted.
echo.
echo Running git add -A...
git add -A

echo.
echo Running git commit...
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

echo.
echo Running git push origin main...
git push origin main

echo.
echo === GIT STATUS ===
git status

echo.
echo === GIT LOG (Last 5 commits) ===
git log --oneline -n 5

echo.
echo === OPERATION COMPLETE ===
pause
