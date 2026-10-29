<#
.SYNOPSIS  tests -> zip -> commit -> tag -> push (origin + github). Χρήση:
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

# 1. VERSION
$v = (Get-Content VERSION -Raw).Trim()
if ($Bump -ne "none") {
  $p = $v.Split("."); [int]$ma=$p[0]; [int]$mi=$p[1]; [int]$pa=$p[2]
  switch ($Bump) { "major" {$ma++;$mi=0;$pa=0} "minor" {$mi++;$pa=0} "patch" {$pa++} }
  $v = "$ma.$mi.$pa"; Set-Content VERSION $v -NoNewline
}
Step "Έκδοση v$v"

# 2. tests
Step "pytest"
& .\.venv\Scripts\python.exe -m pytest -q
Check "pytest"

# 3. zip
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
Write-Host "   $zip"

# 4. git (commit μόνο αν υπάρχουν αλλαγές· αν έγινε merge έτοιμο, μένει μόνο το tag)
Step "git commit + tag"
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  git commit -m "v${v}: $Message"
  Check "git commit"
} else {
  Write-Host "   Καμία νέα αλλαγή για commit."
}
git tag "v$v"
Check "git tag (υπάρχει ήδη;)"

# 5. push
$ok = @()
foreach ($r in @("origin", "github")) {
  if (git remote | Select-String -SimpleMatch -Pattern $r -Quiet) {
    git push $r HEAD --tags
    if ($LASTEXITCODE -eq 0) { $ok += "$r ✔" } else { $ok += "$r ✘"; Write-Host "Push στο $r απέτυχε" -ForegroundColor Red }
  } else { $ok += "$r (δεν υπάρχει remote)" }
}

# 6. περίληψη
Write-Host "`n===== v$v =====" -ForegroundColor Green
Write-Host "zip : $zip"
Write-Host ("push: " + ($ok -join " | "))
