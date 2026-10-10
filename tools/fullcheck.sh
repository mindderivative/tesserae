#!/bin/sh
# The check a commit has to pass: the whole test suite, then the docs build with warnings as errors.
# Run it from anywhere; it uses the repository's .venv. It takes about three minutes.
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python -m pytest -q 2>&1 | tail -4
.venv/bin/python -m mkdocs build --strict 2>&1 | tail -1
