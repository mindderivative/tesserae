"""0.3.4 (#83): the docs describe what Tesserae is, not how it got there.

A new reader needn't know which version added a feature or which milestone built it. Only
the changelog and the migration page speak of versions; everywhere else (and on the generated
pages, which come from docstrings) there are no milestone numbers, issue numbers or version numbers.
"""

import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"
ALLOWED = {DOCS / "changelog.md", DOCS / "migration.md"}
HISTORY = [
    (re.compile(r"\bM\d{2,3}\b"), "a milestone number"),
    (re.compile(r"\(M\d+\b|\bM\d+ Phase\b"), "a milestone number"),
    (re.compile(r"\b0\.\d+\.\d+(?:\.\d+)?\b"), "a version number"),
    (re.compile(r"\(#\d+\)|/issues/\d+|\btre#\d+"), "an issue number"),
    (re.compile(r"\b(?:since|before|after|until) (?:tre )?\d+\.\d+", re.IGNORECASE), "a version"),
]
PAGES = sorted(p for p in DOCS.rglob("*.md") if p not in ALLOWED)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(DOCS).as_posix())
def test_a_page_has_no_version_history(page):
    found = []
    for number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
        for pattern, what in HISTORY:
            if pattern.search(line):
                found.append(f"{page.relative_to(DOCS)}:{number}: {what}: {line.strip()[:110]}")
    assert not found, "\n".join(found[:12])
