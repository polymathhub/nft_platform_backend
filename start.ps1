param(
    [string]$Env = "development",
    [string]$Port = "8000",
    [int]$Workers = 4,
    [switch]$Reload = $false
)

# Load .env if present (simple parser)
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -and -not $_.StartsWith('#')) {
            $parts = $_ -split '=', 2
            if ($parts.Length -eq 2) { [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process") }
        }
    }
}

if ($Env -ieq 'production') {
    Write-Host "Starting in production mode on :$Port with $Workers workers"
    & python -m uvicorn app.main:app `
        --host 0.0.0.0 `
        --port $Port `
        --workers $Workers
} else {
    Write-Host "Starting in development mode on :$Port (auto-reload enabled)"
    & python -m uvicorn app.main:app `
        --host 0.0.0.0 `
        --port $Port `
        --reload `
        --log-level debug
}
