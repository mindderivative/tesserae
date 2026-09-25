# LOG — M32: Migrate to `tre` 0.3.3 (in progress)

*(Replaces M30's log — M30 is complete, committed and pushed.)*

- User: "scope the 0.3.3 migration as M32", then "go with your
  recommendations for M32", then "push it and start Phase 2", then "accept both drops, send the questions, and start Phase 3".

## Phase 1 — decisions

`tesserae.widgets` follows `tre` 0.3.3's names; `Switch`'s `is_on`
becomes `selected`; `.venv` pinned to the `tre` v0.3.3 release.

## Phase 2 — YAML migration

1. `.venv` pinned: v0.3.3 wheel built offline from the tag, installed
   in place of the `tre.pth` source-tree link. Verified it's the
   release (has `set_stylesheet`, lacks 0.3.4's `create`).
2. `tre`'s `migrate_views_0_3_3.py`: 66 files, committed unedited
   (`1d0b932`). Found a bug in it: three `kind: Rect` nodes inside `.py`
   strings got `background` -> `foreground`. All `.yaml` files were right.
   Fixed separately (`c951f0f`).
3. By hand: dict specs and assertions, a split Text style, `Switch`'s
   `is_on` -> `selected`, `Image`'s stale PascalCase note.
4. Docs: yaml snippets via the tool's `migrate_text()`, one mislabelled
   fence fixed, installation/README rewritten for v0.3.3.

81 -> 13 failures on `tre` 0.3.3; the 13 left are Python-API renames.

## Phase 3 — Python API migration

1. `tesserae.widgets` renamed to `tre` 0.3.3's names, checked against
   the wheel's own signatures: `switch(selected=)`,
   `divider(orientation=)`, `link(content)`, `dialog(supporting_text)`,
   `toolbar(vibrant=)`; `icon`/`loading_indicator` pass `foreground=`
   through (translations removed).
2. Tests follow (`"value"`, `get_selected`, same-name parity tests).
   `test_themes`' real-font test silently skipped under the pinned
   wheel (no `.ttf` shipped); now also honors `TRE_SOURCE_DIR`.
3. Docs: widget-catalog renames table; ARCHITECTURE binding names.

**233 passed, 0 failed** on `tre` 0.3.3 (81 before M32); examples clean.
