# Requires: PowerShell 5.1
# One-shot helper: make the APMCM_2026 repository private.
# Authenticates with GitHub (device flow) if needed, then flips the visibility
# and verifies the result.
#
# Run it in your own terminal window, not through an agent session:
#   powershell -ExecutionPolicy Bypass -File scripts\make-private.ps1
#
# Keep this file pure ASCII (PowerShell 5.1 reads BOM-less scripts as ANSI).

param(
    [string]$Repo = "SimonYoungxy/APMCM_2026"
)

$ErrorActionPreference = "Stop"

# ---- locate gh
$candidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\gh\bin\gh.exe"),
    "gh"
)
$gh = $null
foreach ($c in $candidates) {
    if ($c -eq "gh") {
        $cmd = Get-Command gh -ErrorAction SilentlyContinue
        if ($cmd) { $gh = $cmd.Source; break }
    } elseif (Test-Path -LiteralPath $c) {
        $gh = $c
        break
    }
}
if (-not $gh) {
    Write-Host "gh CLI not found. Expected at:" -ForegroundColor Red
    Write-Host ("  " + (Join-Path $env:LOCALAPPDATA "Programs\gh\bin\gh.exe"))
    exit 1
}
Write-Host ("using gh: " + $gh)

# ---- authenticate if needed
$status = & $gh auth status 2>&1
if ($status -notmatch "Logged in to github.com") {
    Write-Host "Not authenticated. Starting GitHub device login..." -ForegroundColor Yellow
    & $gh auth login -h github.com -p https -w --scopes repo
    $status = & $gh auth status 2>&1
    if ($status -notmatch "Logged in to github.com") {
        Write-Host "Authentication failed; aborting." -ForegroundColor Red
        exit 1
    }
}
Write-Host "authenticated" -ForegroundColor Green

# ---- flip visibility
Write-Host ("changing visibility of " + $Repo + " to private ...")
& $gh repo edit $Repo --visibility private --accept-visibility-change-consequences

# ---- verify
$json = & $gh repo view $Repo --json visibility,nameWithOwner,isPrivate 2>&1
Write-Host "result:" -ForegroundColor Green
Write-Host $json
