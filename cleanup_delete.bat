@echo off
setlocal enabledelayedexpansion

REM Delete all the instruction and fix files
for %%F in (
  ACTION_REQUIRED.md
  ALEMBIC_COLUMN_SIZE_FIX.md
  alembic_error.log
  alembic_migration.log
  ALEMBIC_MIGRATION_STANDARDS.md
  alembic_output.log
  alembic_upgrade.log
  API_ENDPOINTS_FIXED.md
  API_FIX_COMPLETE.md
  AUTHENTICATION_AND_ROUTING_FIX.md
  DEPLOYMENT_COMPLETE.md
  DEPLOYMENT_READY.md
  DEPLOYMENT_TRIGGER.md
  DETAILED_MIGRATION_FIXES.md
  FRONTEND_BACKEND_AUDIT_REPORT.md
  FRONTEND_BACKEND_FIXES_APPLIED.md
  GIT_COMMIT_GUIDE.md
  INTEGRATION_STATUS.md
  migration_output.log
  migration_output2.log
  migration_output3.log
  NAVIGATION_REDIRECT_FIXES.md
  NFT_MINTING_FIXES.md
  README_MIGRATION_FIXES.md
  RESTART_REQUIRED.md
  SECURITY_FIXES_APPLIED.md
  SECURITY_VULNERABILITIES.md
  SECURITY_VULNERABILITY_AUDIT.md
  TELEGRAM_AUTH_DEBUG.md
  TELEGRAM_AUTH_IMPLEMENTATION.md
  TELEGRAM_AUTH_MIGRATION_FIXES.md
  TELEGRAM_AUTH_REFACTOR_COMPLETE.md
  TELEGRAM_MINI_APP_FIX.md
  TELEGRAM_MINI_APP_SETUP.md
  TONCONNECT_TELEGRAM_VERIFICATION_REPORT.md
  commit_changes.bat
  fix_alembic_column_size.ps1
  run_git.js
  run_git.py
  run_git_commands.bat
  PUSH_CHANGES.bat
  push_frontend_changes.bat
  push_changes.js
  push_changes.py
  app.log
) do (
  if exist "%%F" del /f /q "%%F"
)

echo Cleanup complete
