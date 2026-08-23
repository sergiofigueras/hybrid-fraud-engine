param(
    [string]$RepositoryUrl = "https://github.com/sergiofigueras/hybrid-fraud-engine.git"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required but was not found in PATH."
}

if (-not (Test-Path "pyproject.toml") -or -not (Test-Path "README.md")) {
    throw "Run this script from the repository root."
}

if (-not (Test-Path ".git")) {
    git init
}

git branch -M main
git add .

$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "feat: publish hybrid financial fraud evaluation engine"
} else {
    Write-Host "No uncommitted files to add."
}

$origin = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    git remote set-url origin $RepositoryUrl
} else {
    git remote add origin $RepositoryUrl
}

Write-Host "Pushing to $RepositoryUrl"
git push -u origin main
