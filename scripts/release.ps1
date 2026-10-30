<#
.SYNOPSIS  tests -> zip -> commit -> tag -> push (required remotes). Χρήση:
  .\scripts\release.ps1 -Message "περιγραφή"            # χρησιμοποιεί το VERSION όπως είναι
  .\scripts\release.ps1 -Bump minor -Message "..."      # patch | minor | major | none
  Τρέχε το από το main, αφού έχεις κάνει merge το branch του AI.
#>
param([string]$Bump = "none", [string]$Message = "release")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$project = "tooldock"

function Step($t) { Write-Host "==> $t" -ForegroundColor Cyan }
function Check($what) { if ($LASTEXITCODE -ne 0) { Write-Host "ΑΠΟΤΥΧΙΑ: $what" -ForegroundColor Red; exit 1 } }

# 1. Έλεγχοι αποθετηρίου
Step "Έλεγχος branch/καθαρού δέντρου"
$branch = (git branch --show-current)
if ($branch -ne "main") { Write-Host "ΑΠΟΤΥΧΙΑ: Το release τρέχει μόνο από main (βρέθηκε: $branch)." -ForegroundColor Red; exit 1 }
if (git status --porcelain) { Write-Host "ΑΠΟΤΥΧΙΑ: Υπάρχουν μη δεσμευμένες αλλαγές." -ForegroundColor Red; exit 1 }

Step "git fetch github"
git fetch github --prune
Check "git fetch github"
$local = (git rev-parse HEAD)
$remote = (git rev-parse "github/main")
if ($local -ne $remote) { Write-Host "ΑΠΟΤΥΧΙΑ: Το τοπικό main ($local) δεν είναι ίδιο με το github/main ($remote)." -ForegroundColor Red; exit 1 }

# 2. Απαιτούμενα remotes από config.json (default: github)
$required = @("github")
if (Test-Path "config.json") {
  try { $cfg = Get-Content "config.json" -Raw | ConvertFrom-Json; if ($cfg.release.required_remotes) { $required = @($cfg.release.required_remotes) } } catch {}
}

# 3. VERSION
$v = (Get-Content VERSION -Raw).Trim()
if ($Bump -ne "none") {
  $p = $v.Split("."); [int]$ma=$p[0]; [int]$mi=$p[1]; [int]$pa=$p[2]
  switch ($Bump) { "major" {$ma++;$mi=0;$pa=0} "minor" {$mi++;$pa=0} "patch" {$pa++} }
  $v = "$ma.$mi.$pa"; Set-Content VERSION $v -NoNewline
}
Step "Έκδοση v$v"

# 4. tests
Step "pytest"
& .\.venv\Scripts\python.exe -m pytest -q
Check "pytest"

# 5. zip
Step "zip"
$dist = "dist"; $stage = Join-Path $dist "stage"; $dest = Join-Path $stage $project
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$exclude = @(".venv", "data", "dist", ".git", "__pycache__", ".pytest_cache", "config.json", "config.json.bad", ".env")
Get-ChildItem -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
  Copy-Item $_.FullName -Destination $dest -Recurse -Force
}
Get-ChildItem $dest -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
$zip = Join-Path $dist "$project-v$v.zip"
Remove-Item $zip -ErrorAction SilentlyContinue
Compress-Archive -Path $dest -DestinationPath $zip
Remove-Item $stage -Recurse -Force
if (-not (Test-Path $zip)) { Write-Host "ΑΠΟΤΥΧΙΑ: Δεν δημιουργήθηκε το zip." -ForegroundColor Red; exit 1 }
Write-Host "   $zip"

# 6. git commit μόνο για tracked αλλαγές
Step "git commit + tag"
$untracked = git ls-files --others --exclude-standard
if ($untracked) { Write-Host "ΑΠΟΤΥΧΙΑ: Υπάρχουν untracked αρχεία. Πρόσθεσέ τα ή πρόσθεσέ τα στο .gitignore:" -ForegroundColor Red; $untracked | ForEach-Object { Write-Host "  $_" }; exit 1 }
git add -u
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  git commit -m "v${v}: $Message"
  Check "git commit"
} else {
  Write-Host "   Καμία νέα αλλαγή για commit."
}
$head = (git rev-parse HEAD)
$existing = git rev-parse -q --verify "refs/tags/v$v"
if ($existing) {
  if ($existing -ne $head) { Write-Host "ΑΠΟΤΥΧΙΑ: Το tag v$v υπάρχει σε άλλο commit ($existing)." -ForegroundColor Red; exit 1 }
  Write-Host "   Το tag v$v υπάρχει ήδη στο ίδιο commit."
} else {
  git tag "v$v"
  Check "git tag"
}

# 7. push + επαλήθευση
$ok = @()
$failed = $false
foreach ($r in $required) {
  if (-not (git remote | Where-Object { $_ -eq $r })) {
    Write-Host "ΑΠΟΤΥΧΙΑ: Λείπει το απαιτούμενο remote '$r'." -ForegroundColor Red; $failed = $true; continue
  }
  git push $r HEAD --tags
  if ($LASTEXITCODE -ne 0) { Write-Host "ΑΠΟΤΥΧΙΑ: Push στο $r." -ForegroundColor Red; $failed = $true; continue }
  $remoteTag = git ls-remote --tags $r "refs/tags/v$v"
  if (-not $remoteTag) { Write-Host "ΑΠΟΤΥΧΙΑ: Το tag v$v δεν βρέθηκε στο $r μετά το push." -ForegroundColor Red; $failed = $true; continue }
  $ok += "$r ✔"
}

# 8. περίληψη
Write-Host "`n===== v$v =====" -ForegroundColor Green
Write-Host "zip : $zip"
Write-Host ("push: " + ($ok -join " | "))
if ($failed) { Write-Host "ΑΠΟΤΥΧΙΑ: Ένα ή περισσότερα remotes απέτυχαν." -ForegroundColor Red; exit 1 }
