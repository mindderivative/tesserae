# LOG — M29: Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

- A `tre` session relayed a user-directed handoff: Tesserae owns all
  file handling, `tre` gets specs and bytes. Recorded as M29 in
  `BUILD_TRACKER.md` after verifying every line reference and every
  `tre` API name against both codebases (`65e9d5a`).
- User: "pin CI to 0.3.2 and start Phase 1".

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
4. Docs: `api/spec.md` rewritten (`spec=` handoff, new `include:`
   section, `expand_components_to_spec`, file-named errors);
   `guide/component-fragments.md` loading section updated.

## Status

**Phase 1 of 5 done.** `pytest tests/` 172 passed (up from 157, +15,
0 regressions); all 3 examples ran clean; `mkdocs build --strict`
clean. Committed locally; not pushed.

Phase 2 waits on the user's Pillow decision; Phase 3 on a file-watching
choice; Phase 4 on `tre` M86.
