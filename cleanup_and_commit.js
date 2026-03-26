#!/usr/bin/env node
const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const projectDir = `C:\\Users\\HomePC\\Downloads\\nft_platform_backend-main (1)\\nft_platform_backend-main`;

// Change to project directory
process.chdir(projectDir);
console.log(`Working directory: ${process.cwd()}`);

// Files to delete
const filesToDelete = [
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
];

// Delete files
console.log("\n=== DELETING FILES ===");
let deletedCount = 0;
filesToDelete.forEach((file) => {
  const filePath = path.join(projectDir, file);
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
      console.log(`✓ Deleted: ${file}`);
      deletedCount++;
    }
  } catch (error) {
    console.log(`✗ Could not delete ${file}: ${error.message}`);
  }
});

console.log(`\nTotal deleted: ${deletedCount}/${filesToDelete.length}`);

// Git operations
try {
  console.log("\n=== GIT ADD -A ===");
  const addResult = execSync("git add -A", { encoding: "utf-8" });
  console.log(addResult || "Files staged successfully");

  console.log("\n=== GIT COMMIT ===");
  const commitMessage = `feat: Add user profile pictures and real-time Socket.io notifications

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

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`;

  const commitResult = execSync(`git commit -m "${commitMessage.replace(/"/g, '\\"')}"`, { encoding: "utf-8" });
  console.log(commitResult || "Commit created successfully");

  console.log("\n=== GIT PUSH ORIGIN MAIN ===");
  const pushResult = execSync("git push origin main", { encoding: "utf-8" });
  console.log(pushResult || "Push completed successfully");

  console.log("\n=== GIT STATUS ===");
  const statusResult = execSync("git status", { encoding: "utf-8" });
  console.log(statusResult);

  console.log("\n=== GIT LOG (Last 5 commits) ===");
  const logResult = execSync("git log --oneline -n 5", { encoding: "utf-8" });
  console.log(logResult);

  console.log("\n✓ OPERATION COMPLETE ===");
} catch (error) {
  console.error("\nError during git operations:");
  console.error(error.message);
  if (error.stdout) console.log("STDOUT:", error.stdout);
  if (error.stderr) console.log("STDERR:", error.stderr);
}
