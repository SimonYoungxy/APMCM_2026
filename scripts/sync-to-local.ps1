# Requires: PowerShell 5.1
# Sync this repository into the local submission folder.
# The repository is the single source of truth; the target folder is generated output.
#
# NOTE: keep this file pure ASCII. Windows PowerShell 5.1 reads script files as ANSI
# when they have no UTF-8 BOM, which corrupts any non-ASCII literal (including paths).
# The default target is therefore derived from the repository location, not hard-coded.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1 -Clean
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1 -Target "D:\some\dir"

param(
    [string]$Target,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $PSScriptRoot
if (-not $Target) {
    $Target = Join-Path (Split-Path -Parent $Repo) "APMCM2026_C"
}

if (-not (Test-Path -LiteralPath $Target)) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
}

$copied = 0

function Copy-One($src, $dstDir, $dstName) {
    if (-not (Test-Path -LiteralPath $src)) { return }
    if (-not (Test-Path -LiteralPath $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }
    if ($null -eq $dstName) {
        Copy-Item -LiteralPath $src -Destination $dstDir -Force
    } else {
        Copy-Item -LiteralPath $src -Destination (Join-Path $dstDir $dstName) -Force
    }
    $script:copied = $script:copied + 1
}

function Copy-Dir($name) {
    $src = Join-Path $Repo $name
    if (-not (Test-Path -LiteralPath $src)) { return }
    $dst = Join-Path $Target $name
    if (-not (Test-Path -LiteralPath $dst)) {
        New-Item -ItemType Directory -Path $dst -Force | Out-Null
    }
    Get-ChildItem -LiteralPath $src -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $dst -Force
        $script:copied = $script:copied + 1
    }
}

# root-level sources
foreach ($f in @("paper.tex", "ControlSheet.tex", "AI_Tool_Usage_Details.tex",
                 "apmcmthesis.cls",
                 "apmcmthesis.cfg", "requirements.txt", "env.txt")) {
    Copy-One (Join-Path $Repo $f) $Target $null
}

# compiled artefacts
Copy-One (Join-Path $Repo "paper.pdf") $Target "paper.pdf"
Copy-One (Join-Path $Repo "paper.pdf") $Target "Capmcm263XXXXX.pdf"
Copy-One (Join-Path $Repo "ControlSheet.pdf") $Target $null
Copy-One (Join-Path $Repo "AI_Tool_Usage_Details.pdf") $Target "AI-Tool-Usage-Details.pdf"

# generated / analytical directories
foreach ($d in @("code", "results", "eda", "figures", "tables")) {
    Copy-Dir $d
}

# submission README lives in docs/, not at the repository root
Copy-One (Join-Path $Repo "docs\submission-readme.md") $Target "README.md"

if ($Clean) {
    foreach ($p in @("*.aux", "*.log", "*.toc", "*.synctex.gz", "*.out", "chk.pdf")) {
        Get-ChildItem -LiteralPath $Target -Filter $p -File -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
    foreach ($stray in @("build", "code\_extract.py", "code\06_figures_extra.py",
                         "code\__pycache__")) {
        $p = Join-Path $Target $stray
        if (Test-Path -LiteralPath $p) {
            Remove-Item -LiteralPath $p -Recurse -Force
            Write-Host ("removed {0}" -f $stray)
        }
    }
}

Write-Host ("synced {0} files" -f $copied)
Write-Host ("source: {0}" -f $Repo)
Write-Host ("target: {0}" -f $Target)
