# LOG — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

- A `tre` session relayed a user-directed handoff: Tesserae owns all
  file handling, `tre` gets specs and bytes. Recorded as M29 after
  verifying every line reference and `tre` API name against both
  codebases.
- User go-aheads, in order: "pin CI to 0.3.2 and start Phase 1";
  "push it and use Pillow for Phase 2"; "push it and use a poll loop for
  Phase 3"; "Create an issue on tre's github about the hot reload hook"
  ([tre#6](https://github.com/mindderivative/tre/issues/6)); "push it
  and start Phase 4"; "push it and use watchfiles for the watcher";
  "push it and start Phase 5".

## What shipped

1. **Views** — `expand_components_to_spec` → dict; `View(spec=...)`,
   `instantiate("", into, spec=...)`, `reconcile(spec=...)`. `include:`
   ported from `tre`'s `include.rs`. Errors name the source file.
2. **Images** — `tesserae.images.decode_image` (Pillow);
   `spec/images.py` strips `src:`, decodes, `push_frame`s.
3. **Hot reload** — `ViewWatcher` (dependencies recorded during
   expansion): `poll()`, and `start(handle)`/`stop()` with `watchfiles`
   on a background thread, applied via `tre`'s `LoopHandle.call_soon`.
   `App.run(hot_reload=True)`, `App.thread_handle()`.
4. **Themes, stylesheets, fonts** — `load_theme`/`load_stylesheet`,
   `load_view`'s path arguments converted to `*_spec=` dicts,
   `tesserae.register_font`, `FontFallbackWarning`.
5. **Docs** — the rule in `README.md`/`docs/index.md`/architecture
   pages; new guides (Hot Reload, Themes & Fonts); API pages.
6. **CI** — `tre` checkout pinned to an exact commit (`0066203`), after
   CI had been failing since M24 by testing `tre`'s `main`.

## Real findings

- Dropping `path` in Phase 1 would have broken `image.src:` and
  `poll_reload` before their replacements existed — moved to Phase 3.
- PyYAML reads unquoted dates as `datetime.date`, which `spec=` rejects.
- `tre`'s views are single-threaded and its loop had no way in from
  another thread → `tre` issue #6 → `tre` M87.
- GitHub's runner has no display: `App.run()` renders zero frames, so the
  live hot-reload test skips there (verified by unsetting the display
  variables locally: 220 passed, 1 skipped).
- `tre` errors found while *applying* a theme carry no `*_spec=` prefix,
  so Tesserae can only attribute them to the view file.
- The Phase 5 sweep found Tesserae's own `multi_screen` example handing
  `tre` file paths.

Every phase was mutation-checked: disabling the new behaviour made its
tests fail.

## Status

**M29 complete.** `pytest tests/` 221 passed (up from 157); all 3
examples run clean; `mkdocs build --strict` clean. CI green on every
push since the pin.
