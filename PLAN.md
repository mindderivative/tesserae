# PLAN — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

*(Replaces the prior M27 + M28 plan in this file — both are complete, committed.)*

## Goal

User direction, relayed through a handoff from the `tre` session: "Tesserae should not be pushing files directly to tre. It should be pushing spec information and handling the files itself." Tesserae owns reading, parsing, decoding and watching files; `tre` gets specs and bytes. Five phases, in the handoff's order: (1) `spec=` handoff with no YAML-text round-trip, (2) image decoding in Tesserae, (3) Tesserae-owned hot reload, (4) theme/stylesheet/font loading (blocked on `tre` M86), (5) docs.

## Status

**In progress — Phase 1 of 5 done.**

Phase 1: `load_view` and `instantiate` now hand `tre` the expanded dict via `spec=`; `expand_components_to_spec` is the primary entry point, with `expand_components` kept as a text wrapper. `include:` is resolved in Tesserae (a straight port of `tre`'s `include.rs`), since `tre` only splices it on its text path. `tre`'s `ValueError`s are re-raised naming the source file. One real regression the handoff didn't mention was found and closed: unquoted dates (`2026-09-24`) load as `datetime.date`, which `spec=` rejects, so they're normalized back to the same string the old text path produced.

One real change to the handoff's sequencing: `path` still reaches `tre` for now. Under `spec=`, `tre` uses it only as the base directory for `image.src:` and as `poll_reload`'s watch target; dropping it before Phases 2 and 3 exist would break both. Removing it is now Phase 3's last step.

Also this session (user-directed): `ci.yml`'s `tre` checkout pinned to `0.3.2`, fixing CI's 9 failing M27 tests.

`pytest tests/` 172 passed (+15). Committed locally; not pushed.

**Up next:** Phase 2 (image decoding) — needs the user's decision on adding a Pillow dependency. Phase 3 needs a decision on file watching (plain poll loop vs. `watchfiles`).
