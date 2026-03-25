@echo off
REM Push the file preview fixes to GitHub

cd /d "C:\Users\HomePC\Downloads\nft_platform_backend-main (1)\nft_platform_backend-main"

echo.
echo ====================================
echo Checking git status...
echo ====================================
git status --short

echo.
echo ====================================
echo Staging files...
echo ====================================
git add app/static/webapp/mint.html
git add app/static/webapp/js/file-preview.js

echo.
echo ====================================
echo Committing changes...
echo ====================================
git commit -m "fix: Critical initialization order bug in FilePreviewManager

- Move window.formState assignment BEFORE FilePreviewManager initialization
- Add comprehensive console logging for debugging
- Fixes TypeError: Cannot set property imageFile of undefined
- Telegram miniapp image upload now works correctly

Root cause: FilePreviewManager.init() was called before window.formState
was defined, causing file selection to fail silently.

Files changed:
- app/static/webapp/mint.html: Moved formState setup before manager init
- app/static/webapp/js/file-preview.js: Added detailed error logging

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo ====================================
echo Pushing to GitHub...
echo ====================================
git push origin main

echo.
echo ====================================
echo COMPLETE!
echo ====================================
echo.
echo Verify with: git log -1
echo.
pause
