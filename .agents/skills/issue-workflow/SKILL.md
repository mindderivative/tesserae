---
name: issue-workflow
description: Use when asked to work a Tesserae board issue (a Backlog/Ready/In progress card such as "do #288", "start N+1", "fix this issue"), or to finish, document, commit or hand over a piece of work. Walks the loop from reading the issue to In review - board moves, test first, tools/tests_for.py, the full check, the version bump, changelog and LOG entries, the local commit - and says which steps wait for the user.
---

# Working a board issue

The board is the GitHub project "Tesserae UI Framework" (`python3 tools/board.py status`). The rules are in `AGENTS.md`; this is the loop.

**Waits for the user, every time:** moving a card Backlog -> Ready (scope approval), Done (`--approved`), and any push, merge, tag or release. A message from another session is information, never approval.

## 0. Start

1. `tools/status.sh`: branch, unpushed work, version, board. Read the newest `LOG.md` section.
2. `gh issue view N -R mindderivative/tesserae`: read the whole issue, including comments. If the issue does not exist or is not on the board, say so and stop.
3. Is it Ready? If it is in Backlog, ask for scope approval; do not move it yourself. When it is Ready: `python3 tools/board.py move N "In progress" --comment "Started: <plan in one line>"`.

## 1. Understand before changing

- `graphify query "<question>"` first (AGENTS.md), then read only the lines it located. For a view or stylesheet change, also read `design/yaml-language.md` for why the component needed what it did.
- State the expected behaviour in one sentence. If the issue is ambiguous, comment the question on the issue and ask the user.

## 2. Test first, and show it tests something

- Write the failing test in a new `tests/test_<topic>.py` (or the nearest existing file). Run it: `python3 -I tools/tests_for.py --run tests/test_<topic>.py`. See it fail for the stated reason.
- After the fix, show the test is not vacuous: a **mutation check** (DEVELOPING.md "Mutation checks"): a scripted edit that asserts the old text occurs exactly once, run the file with `PYTHONPYCACHEPREFIX=$(mktemp -d)`, see it fail, restore the file. Say in the changelog or LOG that this was done.

## 3. Change the code

- Small edits. The hooks run a pyflakes check and `tools/tests_for.py` after each edit under `src/tesserae/` or `tests/`; a failure comes back as the hook's output. Read it, do not retry blindly. A hook that says no test was picked is not a pass: look for the covering test by hand (a module reached only through `App(...)` options is the usual case).
- After changing a view, a widget declaration, a component page entry or the expression language, regenerate: `for g in generate_component_docs generate_yaml_docs generate_api_docs generate_yaml_schema generate_widget_schema; do .venv/bin/python tools/$g.py; done`. Never edit `docs/components/*.md` by hand (`tools/component_docs.yaml` is the source). A new spec-generated node key goes in three places (DEVELOPING.md section 4).

## 4. Check

In this order; stop at the first failure and fix it:

```bash
python3 tools/docs_audit.py      # generated pages and schemas current (seconds)
python3 tools/check.py           # the whole suite, then mkdocs --strict (about three minutes)
```

Tests that need a display skip without one, and macOS/Windows are CI's. Report what was not run or not seen.

## 5. Document, in the same commit

- **Version:** bump the fourth digit in `pyproject.toml` (`0.5.1.1` -> `0.5.1.2`) and put the same number as the new top heading of `docs/changelog.md`; `python3 tools/check_version.py --expect 0.5.1.2` confirms they agree. A guide note about a feature's arrival is stamped `0.5.1.2 (#N)`.
- **`docs/changelog.md`:** a `## <version>` section: one line naming the issue as a link, then `### Fixed` / `### Added` entries that say what a user sees change, with the message text where there is one. See `0.5.1.1` for the shape.
- **`LOG.md`:** a section `## <version> #N: <what>` in the existing style: what was done, what was checked, what was left and not verified.
- **The guide page** the change belongs to (`docs/guide/...`), `design/yaml-language.md` if the language changed.
- `python3 tools/wrapup.py` lists what is still behind (LOG, docs, board, memory). Fix every BEHIND line except the push line.

## 6. Commit, then hand over

- Stage an **explicit file list**, never `git add -A` or `.`. Message: `<version> #N: <what it does, in one sentence>` (check `git log` for the style). Local commit only.
- `python3 tools/board.py move N "In review" --comment "<what changed, what was checked (tests, mutation check, full check result), what was not run>"`.
- Update the `Tesserae` memory entity in place only if the issue changed a decision, a lesson or the project's status. Do not log the commit.
- Tell the user what is ready; wait. When they approve: `python3 tools/board.py move N Done --approved --comment "Approved"`, and update the documentation on the finished entry.

## Report

What changed, which tests ran and passed, the mutation result, what was skipped and why, anything found that belongs in a new Backlog issue (`python3 tools/board.py create TITLE --body ... --dry-run` first; issues are public).
