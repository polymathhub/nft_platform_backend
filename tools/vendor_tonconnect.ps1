# PowerShell helper to vendor TonConnect UI assets into the repo
# Run this from the repository root (PowerShell)

param(
    [string]$version = "latest"
)

Write-Host "Installing @tonconnect/ui@$version and copying dist files..."
npm install "@tonconnect/ui@$version"
$src = Join-Path -Path "node_modules" -ChildPath "@tonconnect\ui\dist"
$dest = Join-Path -Path "app" -ChildPath "static\vendor\tonconnect"
if (-Not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
Copy-Item -Path (Join-Path $src "*") -Destination $dest -Recurse -Force
Write-Host "Copied files to $dest"
Write-Host "Tip: Commit the files under app/static/vendor/tonconnect so deployments don't rely on CDN."