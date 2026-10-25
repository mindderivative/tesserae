#!/bin/sh
# PostToolUse (Edit|Write): pyflakes-level ruff check (syntax errors, unused or undefined names) of the edited file. Report only: no auto-fix, since an unused import may be a re-export.
cd "$CLAUDE_PROJECT_DIR" || exit 0
f=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')
case "$f" in
  */src/*.py|*/tools/*.py) ;;
  *) exit 0 ;;
esac
ruff=.venv/bin/ruff; [ -x "$ruff" ] || ruff=$(command -v ruff) || exit 0
out=$("$ruff" check --isolated --select E9,F --quiet "$f" 2>&1) || { printf '%s\n' "$out" >&2; exit 2; }
exit 0
