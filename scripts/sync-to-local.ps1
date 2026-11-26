# Requires: PowerShell 5.1
# Sync this repository into the local submission folder.
# The repository is the single source of truth; the target folder is generated output.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1 -Target "D:\path\to\APMCM2026_C"
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-local.ps1 -Clean

param(
    [string]$Target = "D:\Grade 2\数学建模\APMCM2026_C",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path -LiteralPath $Target)) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
}

$copied = 0

function Copy-One($src, $dstDir, $dstName) {
    if (-not (Test-Path -LiteralPath $src)) { return }
    if (-not (Test-Path -LiteralPath $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }
    if ($dstName -eq $null) {
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

# ---- single files at the repository root
foreach ($f in @("paper.tex", "ControlSheet.tex", "apmcmthesis.cls",
                 "apmcmthesis.cfg", "requirements.txt", "env.txt")) {
    Copy-One (Join-Path $Repo $f) $Target $null
}

# ---- compiled artefacts
Copy-One (Join-Path $Repo "paper.pdf") $Target "paper.pdf"
Copy-One (Join-Path $Repo "paper.pdf") $Target "Capmcm263XXXXX.pdf"
Copy-One (Join-Path $Repo "ControlSheet.pdf") $Target $null

# ---- generated / analytical directories
foreach ($d in @("code", "results", "eda", "figures", "tables")) {
    Copy-Dir $d
}

# ---- submission README comes from docs/, not from the repository README
Copy-One (Join-Path $Repo "docs\submission-readme.md") $Target "README.md"

# ---- optional cleanup of stale artefacts and leftovers
if ($Clean) {
    $patterns = @("*.aux", "*.log", "*.toc", "*.synctex.gz", "*.out")
    foreach ($p in $patterns) {
        Get-ChildItem -LiteralPath $Target -Filter $p -File -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
    foreach ($stray in @("build", "code\_extract.py", "code\06_figures_extra.py",
                         "code\__pycache__")) {
        $p = Join-Path $Target $stray
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    }
    Write-Host "cleaned stale artefacts"
}

Write-Host ("synced {0} files from {1}" -f $copied, $Repo)
Write-Host ("target: {0}" -f $Target)
