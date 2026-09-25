# LOG — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

- A `tre` session relayed a user-directed handoff: Tesserae owns all
  file handling, `tre` gets specs and bytes. Recorded as M29 in
  `BUILD_TRACKER.md` after verifying every line reference and every
  `tre` API name against both codebases (`65e9d5a`).
- User: "pin CI to 0.3.2 and start Phase 1", then "push it and use Pillow for Phase 2", then "push it and use a poll loop for Phase 3", then "Create an issue on tre's github about the hot reload hook" ([tre#6](https://github.com/mindderivative/tre/issues/6)), then "push it and start Phase 4", then "push it and use watchfiles for the watcher".

## What shipped

1. CI: `ci.yml`'s `tre` checkout pinned to `ref: "0.3.2"`. Unpinned,
   CI tested `tre`'s `main` (v0.3.1), which lacks `tre`'s M84, and
   failed M27's 9 fragment tests. Switch to the `v0.3.2` tag once it
   ships.
2. Phase 1, `spec=` handoff:
   - `expand_components_to_spec(...) -> dict` is the primary entry
     point; `expand_components` is now a thin text wrapper.
   - `load_view` → `View(str(path), spec=dict)`; `instantiate` →
     `parent.instantiate(str(path), into, spec=dict)`.
   - `include:` resolved in Tesserae, ported from `tre`'s `include.rs`
     with identical rules (sole key, relative to the including file,
     confined, cycle-checked, depth 8). Resolved before `component:`
     expansion, so an included file can now use `component:`.
     Rejected inside `*_Component.yaml` fragments.
   - `tre`'s `ValueError`s re-raised as `"<path>: <message>"`.
   - Found and fixed: unquoted YAML dates became `datetime.date`,
     which `spec=` rejects (confirmed directly); normalized with
     `str()`, matching the old text path's output exactly.
3. Sequencing change from the handoff: `path` still passed to `tre`
   as the `image.src:` base directory and `poll_reload` target (both
   confirmed in `tre`'s `View.__new__`). Dropping it now would break
   images and hot reload; moved to Phase 3's last step.
4. Phase 2, image decoding (Pillow):
   - `tesserae.images.decode_image` → straight-alpha RGBA bytes plus
     pixel size, raising `OSError` naming the file.
   - `widgets.image` → `add_image_from_bytes`.
   - `spec/images.py`: every `kind: Image`'s `src:` removed after
     expansion, resolved with `tre`'s rules, decoded, pushed with
     `push_frame` once `tre` builds the node. `Image_Component.yaml`
     needed no change.
   - `instantiate` now passes `path=""` -- `tre` gets no file path for
     embedded components. `load_view` keeps `path` only for
     `poll_reload`.
   - Mutation-checked: disabling `src:` removal fails 3 of 4 end-to-end
     tests, with `tre` visibly opening the file itself.
5. Phase 3, hot reload (poll loop):
   - `tesserae.spec.ViewWatcher(view, path)`: `poll()` checks
     `(mtime_ns, size)` of every file the build read -- view,
     includes, fragments, images -- and on change rebuilds via the
     shared `build_view_spec` and calls `view.reconcile(spec=...)`.
   - Errors raise once per edit, naming the file; view left as it was.
   - `load_view` → `View(spec=...)` with no path: Tesserae now gives
     `tre` no file path anywhere.
   - Found: `tre`'s `View` is single-threaded and `App.run()` has no
     periodic Python hook, so the watcher can't run inside
     `App.run()` yet. Recorded as a known gap.
   - Mutation-checked: watching only the view file fails exactly the 4
     include/fragment/image tests.
6. Phase 4, themes, stylesheets and fonts:
   - `load_theme`/`load_stylesheet` read YAML into `tre`'s `*_spec=`
     dicts; `load_view`'s theme/stylesheet path arguments now go
     through them, so `tre` gets only dicts.
   - `tesserae.register_font(path)` reads a font file and hands `tre`
     the bytes.
   - `FontFallbackWarning` for any theme or view `font_family` that's
     neither bundled nor registered (`tre` would substitute silently).
   - Bundled families read from `tre` itself: Roboto, Noto Sans
     Arabic, Hack Nerd Font Mono.
   - Mutation-checked: passing theme paths through to `tre` again
     fails the "only dicts" test.
7. Phase 3b, hot reload inside `App.run()` (`watchfiles` + `tre` M87):
   - `ViewWatcher.start(handle)`/`stop()`: background thread, file
     events via `watchfiles`, rebuild off the UI thread, only
     `reconcile`/`push_frame` queued with `call_soon`. Failures are
     queued as raising callables, logged by `tre`.
   - `App.run(hot_reload=True)` and a new `App.thread_handle()`.
   - Live test in a subprocess; skips with no display (GitHub CI).
     Mutation-checked: `hot_reload=False` never sees the change.
   - CI pin moved to `0066203` (`tre` M87), relayed and verified.
8. CI pin refined to the exact commit `d6c30ef` (relayed from the
   `tre` session, user-directed there).
9. Docs: `api/spec.md` rewritten (`spec=` handoff, new `include:`
   section, `expand_components_to_spec`, file-named errors);
   `guide/component-fragments.md` loading section updated.

## Status

**Phases 1–4 (and 3b) of 5 done.** `pytest tests/` 221 passed (up
from 157: +15 Phase 1, +16 Phase 2, +8 Phase 3, +7 Phase 3b, +18
Phase 4; 0 regressions);
all 3 examples ran clean; `mkdocs build --strict` clean (new
`guide/hot-reload.md`, `guide/themes-and-fonts.md`). CI green after
the pin and after each push since (214 passed on `07d0c53`). Phase 3b
committed locally, not pushed.

Only Phase 5 (final docs pass) remains.
