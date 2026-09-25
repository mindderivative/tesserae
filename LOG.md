# LOG — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

- A `tre` session relayed a user-directed handoff: Tesserae owns all
  file handling, `tre` gets specs and bytes. Recorded as M29 in
  `BUILD_TRACKER.md` after verifying every line reference and every
  `tre` API name against both codebases (`65e9d5a`).
- User: "pin CI to 0.3.2 and start Phase 1", then "push it and use Pillow for Phase 2".

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
5. Docs: `api/spec.md` rewritten (`spec=` handoff, new `include:`
   section, `expand_components_to_spec`, file-named errors);
   `guide/component-fragments.md` loading section updated.

## Status

**Phases 1–2 of 5 done.** `pytest tests/` 188 passed (up from 157:
+15 Phase 1, +16 Phase 2; 0 regressions); all 3 examples ran clean;
`mkdocs build --strict` clean. CI green after the pin (172 passed on
`82cf4f2`). Phase 2 committed locally, not pushed.

Phase 3 waits on a file-watching choice. Phase 4 is unblocked locally
(`tre` M86 landed on `0.3.2`, not pushed) and waits on a go-ahead.
