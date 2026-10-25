#!/bin/sh
# PostToolUse (Bash): after a local commit, remind the model of the memory policy and move the board.
cmd=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')
printf '%s' "$cmd" | grep -Eq '(^|[;&|[:space:]])git[[:space:]]+commit([[:space:]]|$)' || exit 0
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"A local commit finished. Per CLAUDE.md: if it changed a decision, lesson, standing instruction or the project's status, update the single Tesserae entity in the memory MCP server in place (back up the graph before pruning). If it finished a board issue, run `python3 tools/board.py <n>=review`. Do not log the commit itself."}}
JSON
