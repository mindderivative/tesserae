#!/bin/sh
# Stop: if source changed in the working tree but no documentation did, ask once for the documentation update CLAUDE.md requires.
input=$(cat)
printf '%s' "$input" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0
changed=$(git status --porcelain)
printf '%s\n' "$changed" | grep -Eq ' src/.*\.py$' || exit 0
printf '%s\n' "$changed" | grep -Eq ' (docs/|CHANGELOG\.md|LOG\.md)' && exit 0
echo "src/ has uncommitted changes but CHANGELOG.md, LOG.md and docs/ do not. Update the documentation (CLAUDE.md policy), or say why none is needed." >&2
exit 2
