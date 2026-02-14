param(
    [string]$Env = "development",
    [string]$Port = "8000",
    [int]$Workers = 4
)

# Load .env if present (simple parser)
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -and -not $_.StartsWith('#')) {
            $parts = $_ -split '=', 2
            if ($parts.Length -eq 2) { Set-Item -Path Env:$($parts[0].Trim()) -Value $parts[1].Trim() }
        }
    }
}

if ($Env -ieq 'production') {
    Write-Host "Starting in production mode on :$Port"
    & gunicorn app.main:app -w $Workers -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$Port
} else {
    Write-Host "Starting in development mode on :$Port (auto-reload)"
    & uvicorn app.main:app --reload --host 0.0.0.0 --port $Port
}
