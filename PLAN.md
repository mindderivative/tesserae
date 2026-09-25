# PLAN — M32: Migrate to `tre` 0.3.3

*(Replaces the M30 plan in this file — M30 is complete, committed and pushed.)*

## Goal

User-directed: "scope the 0.3.3 migration as M32". Move Tesserae from `tre` v0.3.2 to the released v0.3.3 (M90's renames, M91's fix for issue #8 and `View.set_stylesheet`, M92). Unblocks M31.

## Status

**Complete (2026-09-25).** 81 of 233 tests and all 3 examples failed unmodified on 0.3.3; now 0 fail, and CI (pinned to `v0.3.3`) is green.

1. **Decisions** (user took all three recommendations): `tesserae.widgets` follows `tre` 0.3.3's names; `Switch`'s `is_on` → `selected`; `.venv` pinned to the v0.3.3 release.
2. **YAML** — `.venv` pinned (a wheel built offline from the tag, replacing the source-tree link); `tre`'s migration script run and committed unedited, then reviewed: it wrongly rewrote three Rect `background`s inside `.py` strings (fixed); dict specs and docs by hand.
3. **Python API** — `switch(selected=)`, `divider(orientation=)`, `link(content)`, `dialog(supporting_text)`, `toolbar(vibrant=)`; translations removed; renames table in the widget catalog.
4. **Verify** — CI pinned to `v0.3.3` and green; a regression test proves bound values survive hot reload (M91; it failed on v0.3.2).
5. **Docs and tracker** — cascade note (stylesheet layout rules now apply); gaps closed; M31 unblocked.

**Up next:** M31 (theme/stylesheet hot reload), waiting on the user's go-ahead. Then `tre`'s building-block program (a large Tesserae-side program, not yet scoped).
