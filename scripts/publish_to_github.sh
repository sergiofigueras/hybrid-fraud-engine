#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

repository_url="${1:-https://github.com/sergiofigueras/hybrid-fraud-engine.git}"

if [[ ! -f pyproject.toml || ! -f README.md || ! -d fraud_engine ]]; then
  echo "This script must be run from the prepared project." >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required but was not found." >&2
  exit 1
fi

if ! git config user.name >/dev/null || ! git config user.email >/dev/null; then
  cat >&2 <<'EOF'
Git author information is missing. Configure it first:

  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"
EOF
  exit 1
fi

if [[ ! -d .git ]]; then
  git init
fi

git branch -M main
git add .

if ! git diff --cached --quiet; then
  git commit -m "feat: publish hybrid fraud evaluation engine"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$repository_url"
else
  git remote add origin "$repository_url"
fi

echo "Publishing to $repository_url"
git push -u origin main
