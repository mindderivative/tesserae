# PLAN — M32: Migrate to `tre` 0.3.3

*(Replaces the M30 plan in this file — M30 is complete, committed and pushed. `LOG.md` still holds M30's record until M32 work starts.)*

## Goal

User-directed: "scope the 0.3.3 migration as M32". Move Tesserae from `tre` v0.3.2 to the released v0.3.3 (M90's renames, M91's fix for issue #8 and `View.set_stylesheet`, M92). Unblocks M31.

## Status

**Scoped, not started — waiting on user decisions (Phase 1).**

Sized against the real v0.3.3 release (built from its tag into a scratch venv): 81 of 233 tests and all 3 examples fail unmodified. `tre`'s migration script would change 58 of 72 YAML files and 8 `.py` files with embedded YAML; Python dict specs, Python calls and the docs' Markdown are manual.

Plan (full detail in `BUILD_TRACKER.md` Milestone 32):

1. **Decide** — recommended: follow `tre` 0.3.3's names in `tesserae.widgets` (`switch(selected=)`, `divider(orientation=)`, `link(content=)`, `dialog(supporting_text=)`, `toolbar(vibrant=)`); rename `Switch`'s `is_on` fragment param to `selected`; pin `.venv` to the `tre` v0.3.3 release instead of `tre`'s source tree.
2. **YAML migration** — run `tre`'s script, review and commit it separately, then hand-migrate dict specs.
3. **Python API migration** — `tesserae.widgets`, the rest of `src/`, the tests.
4. **Verify** — 0 failures on v0.3.3, examples clean, CI pinned to `v0.3.3`, M91's fix confirmed through Tesserae's hot reload.
5. **Docs and tracker** — every snippet in `docs/` updated, a note on the cascade change, gaps closed.
