# PLAN — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

*(Replaces the prior M27 + M28 plan in this file — both are complete, committed.)*

## Goal

User direction, relayed through a handoff from the `tre` session: "Tesserae should not be pushing files directly to tre. It should be pushing spec information and handling the files itself." Tesserae owns reading, parsing, decoding and watching files; `tre` gets specs and bytes. Five phases, in the handoff's order: (1) `spec=` handoff with no YAML-text round-trip, (2) image decoding in Tesserae, (3) Tesserae-owned hot reload, (4) theme/stylesheet/font loading (blocked on `tre` M86), (5) docs.

## Status

**In progress — Phases 1–4 of 5 done.**

Phase 1: `load_view` and `instantiate` now hand `tre` the expanded dict via `spec=`; `expand_components_to_spec` is the primary entry point, with `expand_components` kept as a text wrapper. `include:` is resolved in Tesserae (a straight port of `tre`'s `include.rs`), since `tre` only splices it on its text path. `tre`'s `ValueError`s are re-raised naming the source file. One real regression the handoff didn't mention was found and closed: unquoted dates (`2026-09-24`) load as `datetime.date`, which `spec=` rejects, so they're normalized back to the same string the old text path produced.

One real change to the handoff's sequencing: `path` still reaches `tre` for now. Under `spec=`, `tre` uses it only as the base directory for `image.src:` and as `poll_reload`'s watch target; dropping it before Phases 2 and 3 exist would break both. Removing it is now Phase 3's last step.

Phase 2 (user chose Pillow): Tesserae decodes every image itself and hands `tre` only RGBA bytes. `widgets.image` uses `add_image_from_bytes`; for views, every `kind: Image`'s `src:` is removed after expansion (so hand-written images and the `Image` fragment are handled the same way, and the fragment needed no change), resolved with `tre`'s own path rules, decoded, and pushed onto the built node with `push_frame`. With both `include:` and `image.src:` now in Tesserae, `instantiate` gives `tre` no path at all; `load_view` still passes one, only for `poll_reload`.

Phase 3 (user chose a plain poll loop): new `tesserae.spec.ViewWatcher`. `poll()` compares the modification time and size of every file the view was built from — the view, its includes, the fragments it used, its images — and on a change rebuilds through the same `build_view_spec` pipeline `load_view` uses and calls `view.reconcile(spec=...)`. Errors raise once per edit, naming the file. `load_view` now gives `tre` no path at all, so Tesserae hands `tre` no file path anywhere. Real limit found: `tre`'s `View` is single-threaded and `App.run()`'s event loop has no periodic Python hook, so the watcher works in an app-controlled loop but can't run inside `App.run()` yet — needs a `tre` addition.

Phase 3b (after `tre` M87 closed `tre` issue #6; user chose `watchfiles`): `App.run(hot_reload=True)` watches every `load()`ed screen while the app runs. Each gets a `ViewWatcher` on a background thread that listens for file-change events, rebuilds the spec off the UI thread, and queues only `reconcile`/`push_frame` through `tre`'s thread-safe `App.thread_handle()`. New `App.thread_handle()` exposes that handle to apps. The live test runs `App.run()` in a subprocess and skips without a display (GitHub's runner has none).

Phase 4: `load_view`'s `stylesheet=`/`default_theme=`/`custom_theme=` still take file paths, but Tesserae reads them and hands `tre` only `*_spec=` dicts (tre M86); new `load_theme`/`load_stylesheet` do the same for `set_theme`. New `tesserae.register_font(path)` reads a font file and hands `tre` the bytes. Because `tre` silently substitutes a bundled face for an unknown `font_family`, Tesserae warns (`FontFallbackWarning`) when a theme or view names a family that isn't bundled (Roboto, Noto Sans Arabic, Hack Nerd Font Mono — read from `tre` itself) or registered. Limits recorded: `App.load()` still takes no theme arguments, `ViewWatcher` doesn't watch theme files, and `tre`'s apply-time theme errors can only be attributed to the view file.

Also this session: `ci.yml`'s `tre` checkout pinned to `0.3.2` (user-directed), fixing CI's 9 failing M27 tests — green on push, twice. Then pinned to the exact commit `d6c30ef` instead, relayed from the `tre` session as user-directed there.

`pytest tests/` 221 passed (+7 for Phase 3b). Everything through Phase 4 and the `0066203` CI pin is pushed; Phase 3b committed locally, not pushed.

**Up next:** Phase 5 — a final docs pass (the user-facing rule "give Tesserae paths; Tesserae never gives `tre` one" stated once, clearly, plus `ARCHITECTURE.md`'s layering). Much of it already landed phase by phase. Hot reload inside `App.run()` is done (Phase 3b).
