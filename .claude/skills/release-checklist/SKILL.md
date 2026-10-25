---
name: release-checklist
description: Use when preparing, checking or cutting a Tesserae release (a version bump, the release commit, the GitHub Release, the PyPI publish), or when asked "is it ready to release". Walks the version, checks, docs and release steps in order and separates what Claude may do from what waits for the user's separate instruction.
---

# Release checklist

The process is written in `DEVELOPING.md` section 6 and `.github/workflows/release.yml`. This skill is the ordered checklist, with the stops that need the user.

**Standing rule (CLAUDE.md): commit locally only. Pushing, fast-forwarding `main`, creating the GitHub Release, approving the `pypi` environment and moving an issue to Done each need the user's separate, explicit instruction. A past approval does not carry over to the next release.**

## 1. Pre-flight (read-only)

- `tools/status.sh` for the overview. Clean `git status`, on the branch the user named. If the branch or version they name is not there, say so and ask before planning anything else.
- Every issue in the release is In review or Done on the board (`python3 tools/board.py status`), each with a comment of what was checked and what was not.
- Anything that could not be verified here (Windows, macOS, other GPUs, other compositors) is listed in the notes as not verified, not dropped.
- The version is free on PyPI: `python3 tools/check_version.py --pypi` (PyPI never accepts a version twice).
- The engine pin: `python3 tools/tre_version_check.py`. A tre release outside `<0.6` is a new Tesserae line, not a bump.

## 2. Version

The version is in `pyproject.toml` and the newest heading of `docs/changelog.md`. Bump both, then `python3 tools/check_version.py --expect X` and search for the old string for other places. Historical "since 0.5.x" notes in the guides stay as they are.

## 3. Checks

```bash
python3 tools/docs_audit.py     # generated pages and schemas current (fast)
python3 tools/check.py          # tests, then mkdocs --strict (about three minutes)
python3 tools/wrapup.py         # what LOG.md, docs, the board, memory are behind on
```

Tests that need a display skip without one: say so. CI also runs Windows and macOS; their results are read from CI, never assumed.

## 4. Documentation

- `docs/changelog.md` (the heading is the version), `LOG.md` (a dated entry in the existing style), the migration page if anything a user writes changed, `README.md` and `docs/installation.md` if install steps changed.

## 5. Commit, then stop

Release commit "Tesserae X" in the repo's style (check `git log`). Tell the user what is ready and wait.

## 6. Steps that wait for the user, in order

1. Push the branch, fast-forward `main`, push it; wait for CI on that commit (Linux, Windows, macOS, Deploy Docs).
2. `gh release create vX --target <sha> --prerelease --title "Tesserae X" --notes-file <changelog section>`.
3. The Release workflow stops at the `pypi` environment: the user approves it. Claude does not.
4. Check PyPI (the index lags a few minutes), install `tesserae-ui==X` in a scratch venv, run a smoke test, add the `LOG.md` entry.
5. Push the log, promote the release (`gh release edit vX --prerelease=false --latest`), move the issues to Done with `tools/board.py move N Done --approved` only after the user approves.

Update the `Tesserae` memory entity only after step 4 has been seen to work. Do not write "released" before that.

## Report

What was run and passed, what was skipped and why, which issues remain held.
