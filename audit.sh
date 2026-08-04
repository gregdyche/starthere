#!/usr/bin/env bash
#
# audit.sh — pre-push safety check for a PUBLIC repo.
#
# Usage:   ./audit.sh
# Run it before every `git push`. Exit code 0 = clear to push.
#
# This is a second net, not the only net. Your pre-commit hooks run first,
# and GitHub push protection runs last.

set -uo pipefail

FAIL=0
WARN=0

red()   { printf "\033[0;31m%s\033[0m\n" "$1"; }
green() { printf "\033[0;32m%s\033[0m\n" "$1"; }
yell()  { printf "\033[0;33m%s\033[0m\n" "$1"; }
head_() { printf "\n\033[1m== %s ==\033[0m\n" "$1"; }

fail() { red   "  FAIL: $1"; FAIL=$((FAIL+1)); }
warn() { yell  "  WARN: $1"; WARN=$((WARN+1)); }
ok()   { green "  ok:   $1"; }

# ---------------------------------------------------------------
head_ "1. Repository sanity"
# ---------------------------------------------------------------
if [ ! -d .git ]; then
  red "Not a git repository. Run this from the repo root."
  exit 1
fi
ok "in a git repo: $(pwd)"

if [ ! -f .gitignore ]; then
  fail ".gitignore is missing"
else
  ok ".gitignore present"
fi

# ---------------------------------------------------------------
head_ "2. Tracked files that should never be tracked"
# ---------------------------------------------------------------
# Note: checks what git is ACTUALLY tracking, not what's on disk.
DANGER_PATTERNS='(^|/)\.env($|\.)|\.key$|\.pem$|\.p12$|(^|/)secrets\.json$|(^|/)credentials\.json$|service-account.*\.json$|(^|/)\.venv/|(^|/)\.DS_Store$'

TRACKED_BAD=$(git ls-files | grep -E "$DANGER_PATTERNS" || true)
if [ -n "$TRACKED_BAD" ]; then
  fail "these files are tracked by git and should not be:"
  echo "$TRACKED_BAD" | sed 's/^/          /'
  echo "        Fix with: git rm --cached <file>   (then commit)"
else
  ok "no dangerous file types are tracked"
fi

# ---------------------------------------------------------------
head_ "3. Secret patterns in tracked content"
# ---------------------------------------------------------------
scan_tracked() {
  local label="$1" pattern="$2" level="$3" ignore="${4:-}"
  local hits
  hits=$(git grep -n -I -E "$pattern" -- . 2>/dev/null || true)
  # Optional 4th arg: matches that are known-harmless template text. Blank
  # them out, then re-test the line — so a line is only cleared when EVERY
  # match on it was a placeholder, never when a real one sits alongside.
  if [ -n "$hits" ] && [ -n "$ignore" ]; then
    hits=$(printf '%s\n' "$hits" \
      | sed -E "s@$ignore@__PLACEHOLDER__@g" \
      | grep -E "$pattern" || true)
  fi
  if [ -n "$hits" ]; then
    if [ "$level" = "fail" ]; then
      fail "$label"
    else
      warn "$label"
    fi
    echo "$hits" | head -n 10 | sed 's/^/          /'
  else
    ok "no match: $label"
  fi
}

# Google Apps Script deployment endpoints — an unauthenticated write pipe.
scan_tracked "Apps Script /exec endpoint" \
  'script\.google\.com/macros/s/[A-Za-z0-9_-]{20,}' fail

# Google Doc / Drive document IDs
scan_tracked "Google Docs or Drive document URL" \
  'docs\.google\.com/(document|spreadsheets)/d/[A-Za-z0-9_-]{20,}' fail

# Local absolute paths leak your username and folder layout. Conventional
# placeholder account names are template text, not a real account, so they
# are exempt (case-insensitive). Any other account name still fails.
scan_tracked "absolute /Users/ path (leaks your username)" \
  '/Users/[A-Za-z0-9._-]+/' fail \
  '/Users/([Yy][Oo][Uu]|[Uu][Ss][Ee][Rr]|[Uu][Ss][Ee][Rr][Nn][Aa][Mm][Ee]|[Yy][Oo][Uu][Rr][Nn][Aa][Mm][Ee])/'

# Generic API keys / tokens
scan_tracked "API key or token assignment" \
  '(api[_-]?key|apikey|secret|token|password|passwd|bearer)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"']{12,}' fail

# Well-known vendor key shapes
scan_tracked "vendor key pattern (AWS / Google / GitHub / OpenAI / Slack)" \
  'AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}' fail

# Personal email addresses
scan_tracked "email address" \
  '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' warn

# ---------------------------------------------------------------
head_ "4. detect-secrets baseline scan"
# ---------------------------------------------------------------
# Use detect-secrets-hook, NOT `detect-secrets scan --baseline`.
#
# `scan --baseline FILE` is not a check. Verified experimentally: it exits 0
# even when it finds a secret that is not in the baseline, and it REWRITES
# FILE in place, silently adding that secret to the baseline. Running this
# audit would have laundered a real secret into the baseline and reported
# "nothing new" on every run thereafter.
#
# detect-secrets-hook is the pre-commit entry point: exit 1 on anything not
# already in the baseline, exit 0 when clean, and it never writes the file.
if command -v detect-secrets-hook >/dev/null 2>&1; then
  if [ -f .secrets.baseline ]; then
    if [ -z "$(git ls-files)" ]; then
      warn "no tracked files — detect-secrets has nothing to scan"
    elif DS_OUT=$(git ls-files -z \
           | xargs -0 detect-secrets-hook --baseline .secrets.baseline 2>&1); then
      ok "detect-secrets found nothing new"
    else
      fail "detect-secrets found something not in the baseline"
      echo "$DS_OUT" | head -n 20 | sed 's/^/          /'
      echo "        Review with: detect-secrets audit .secrets.baseline"
    fi
  else
    warn ".secrets.baseline missing — create it: detect-secrets scan > .secrets.baseline"
  fi
else
  warn "detect-secrets-hook not on PATH — is the venv active?"
fi

# ---------------------------------------------------------------
head_ "5. Pre-commit hook actually installed"
# ---------------------------------------------------------------
if [ -f .git/hooks/pre-commit ]; then
  ok "pre-commit hook is installed"
else
  warn "no pre-commit hook in .git/hooks — run: pre-commit install"
fi

# ---------------------------------------------------------------
head_ "6. What you are about to push"
# ---------------------------------------------------------------
echo "  Files tracked in this repo:"
git ls-files | sed 's/^/          /'
echo
echo "  Commits not yet on the remote:"
if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
  UNPUSHED=$(git log --oneline '@{u}..HEAD' 2>/dev/null || true)
  if [ -n "$UNPUSHED" ]; then
    echo "$UNPUSHED" | sed 's/^/          /'
  else
    echo "          (none — up to date with remote)"
  fi
else
  echo "          (no upstream set yet — this would be the first push)"
fi

# ---------------------------------------------------------------
head_ "Result"
# ---------------------------------------------------------------
if [ "$FAIL" -gt 0 ]; then
  red "$FAIL failure(s), $WARN warning(s). DO NOT PUSH until these are resolved."
  echo
  echo "Reminder: if a secret is already in a PUSHED commit, removing it in a new"
  echo "commit does not help. Rotate the credential — assume it is compromised."
  exit 1
elif [ "$WARN" -gt 0 ]; then
  yell "$WARN warning(s), 0 failures. Read them, then decide."
  exit 0
else
  green "All checks passed. Clear to push."
  exit 0
fi
