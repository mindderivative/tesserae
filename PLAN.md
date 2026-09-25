# PLAN — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

*(Replaces the prior M27 + M28 plan in this file — both are complete, committed.)*

## Goal

User direction, relayed through a handoff from the `tre` session: "Tesserae should not be pushing files directly to tre. It should be pushing spec information and handling the files itself." Tesserae owns reading, parsing, decoding and watching files; `tre` gets specs and bytes.

## Status

**Complete (2026-09-25).** Tesserae gives `tre` no file path anywhere.

- **Phase 1 — views as data.** `load_view`/`instantiate` hand `tre` one finished dict via `spec=` (no YAML-text round-trip). `include:` resolved in Tesserae with `tre`'s own rules, before `component:` expansion. `tre`'s errors re-raised naming the source file. Unquoted YAML dates normalized (they break `spec=`).
- **Phase 2 — images (Pillow).** `widgets.image` → `add_image_from_bytes`; every `kind: Image` `src:` removed after expansion, decoded, and pushed with `push_frame`.
- **Phase 3 — hot reload (poll).** `ViewWatcher` tracks every file a view is built from; `poll()` for app-controlled loops. `load_view` stops passing `tre` a path.
- **Phase 3b — hot reload inside `App.run()` (`watchfiles`).** After `tre` M87 (from `tre` issue #6, which this milestone opened): `ViewWatcher.start(handle)` watches for file events on a background thread and applies changes through `App.thread_handle()`; `app.run(hot_reload=True)`.
- **Phase 4 — themes, stylesheets, fonts.** Read by Tesserae and passed as `*_spec=` dicts (`tre` M86); `tesserae.register_font(path)`; `FontFallbackWarning` where `tre` would silently substitute a font.
- **Phase 5 — docs.** The rule stated in `README.md`, `docs/index.md` and both architecture pages; `ARCHITECTURE.md` gained a "Files and data" table. The sweep found Tesserae's own `multi_screen` example still using `tre.View(path)` — fixed.

CI's `tre` checkout is pinned to `0066203` (tip of `0.3.2`, with M84/M86/M87); switch to `main` or the `v0.3.2` tag once released.

`pytest tests/` 221 passed (up from 157). All 3 examples run clean; `mkdocs build --strict` clean.

**Up next:** nothing scoped. Named candidates: theme arguments on `App.load()`; hot reload for theme/stylesheet files; hot reload for `App.register()`ed screens (Tesserae doesn't know their file); conditional per-item styling for the 5 Rust-internal-coloring widgets.
