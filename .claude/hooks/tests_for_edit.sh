#!/bin/sh
# PostToolUse (Edit|Write): after an edit under src/ or tests/, run the tests tools/tests_for.py picks for that file. Silent when they pass or none
# is picked; on a failure the output goes back to the model (exit 2). Capped at 40 seconds: a timeout says so and is not a failure.
cd "$CLAUDE_PROJECT_DIR" || exit 0
f=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')
case "$f" in
  */src/tesserae/*.py|*/src/tesserae/*.yaml|*/tests/test_*.py) ;;
  *) exit 0 ;;
esac
py=.venv/bin/python; [ -x "$py" ] || exit 0
out=$(timeout 40 "$py" -I tools/tests_for.py --run "$f" 2>&1); rc=$?
case $rc in
  0) exit 0 ;;
  124) echo "tests_for: the picked tests for ${f#"$CLAUDE_PROJECT_DIR"/} ran past 40 seconds; run them by hand: python3 -I tools/tests_for.py --run" >&2; exit 0 ;;
  *) printf '%s\n' "$out" | tail -40 >&2; exit 2 ;;
esac
