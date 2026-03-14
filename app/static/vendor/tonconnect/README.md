Vendor TonConnect assets

Purpose:
- Provide local fallback copies of the TonConnect UI JavaScript and CSS so the web app works when CDN fetches fail (e.g., inside Telegram WebApp).

Files expected here:
- tonconnect-ui.js
- tonconnect-ui.css

How to create these files locally:
1. Using npm (recommended):
   - npm install @tonconnect/ui@latest
   - Copy the distributable files from node_modules/@tonconnect/ui/dist/ to this directory.
     Example (PowerShell):
       npm install @tonconnect/ui@latest
       Copy-Item -Path node_modules\@tonconnect\ui\dist\* -Destination app\static\vendor\tonconnect\ -Recurse -Force

2. Alternatively, download release artifacts manually and place them here.

After placing files:
- Commit and push the files so the production deployment serves them at /static/vendor/tonconnect/.
- The app exposes a health check at /health/tonconnect to verify presence of these files and manifest reachability.
