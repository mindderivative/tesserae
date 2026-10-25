#!/bin/sh
# PreToolUse (Bash): CLAUDE.md allows local commits only. Block `git push`; before a `git commit`, check the staged Python files (pyflakes level, so old findings elsewhere do not block).
cd "$CLAUDE_PROJECT_DIR" || exit 0
cmd=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')
if printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*push([[:space:]]|$)'; then
  echo "Blocked: pushing needs a separate, human-gated instruction (CLAUDE.md). Commit locally only." >&2
  exit 2
fi
if printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+commit([[:space:]]|$)'; then
  ruff=.venv/bin/ruff; [ -x "$ruff" ] || ruff=$(command -v ruff)
  staged=$(git diff --cached --name-only --diff-filter=ACM -- '*.py')
  if [ -n "$ruff" ] && [ -n "$staged" ]; then
    out=$(printf '%s\n' "$staged" | xargs "$ruff" check --isolated --select E9,F --quiet 2>&1) || { printf 'ruff found problems in staged files:\n%s\n' "$out" >&2; exit 2; }
  fi
fi
exit 0
