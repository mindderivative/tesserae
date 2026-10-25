#!/bin/sh
# PostToolUse (Edit|Write): refresh the knowledge graph after a source edit, in the background, at most once every 60 seconds.
cd "$CLAUDE_PROJECT_DIR" || exit 0
f=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')
case "$f" in */src/*.py) ;; *) exit 0 ;; esac
stamp=${TMPDIR:-/tmp}/tesserae_graphify.stamp
now=$(date +%s)
[ -f "$stamp" ] && [ $((now - $(cat "$stamp"))) -lt 60 ] && exit 0
echo "$now" > "$stamp"
(graphify update . >/dev/null 2>&1 &)
exit 0
