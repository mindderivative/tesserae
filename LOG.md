# LOG — M33: Migrate to `tre` 0.3.4

*(Replaces M31's log — M31 is complete, committed and pushed.)*

- User: "scope the tre 0.3.4 migration".

## Scoping

1. The GitHub release notes are empty, so it was scoped from
   `git log v0.3.3..v0.3.4` (21 commits) and the source at the tag.
2. Built v0.3.4 without touching `tre`'s checkout: `git archive v0.3.4`
   into the scratchpad, `maturin build --release` offline with M32's
   Cargo build dir. Installed into a scratch venv, `venv-034`, which
   reaches `.venv`'s packages through a `site.addsitedir` `.pth` line
   (a plain path line doesn't process the nested editable-install
   `.pth`). Checked it's 0.3.4: it has `Window.create` and `Node.destroy`.
3. Tesserae unmodified on 0.3.4: 1 failed / 254 passed; no unraisable
   warnings; counter, multi_screen and todo_list run clean.
4. The failure: `SideSheetModal`'s scrim opacity is 0.32 against `tre`'s
   1.0. `tre` moved its scrims' 32% into the color (`scrim_fill`), since
   group opacity would fade the panel. The spec's `resolve_color` has no
   role-plus-alpha form.
5. A scan for translucent colors and `opacity` found exactly the known
   six `#FFFFFF00` labels and the two scrims.
6. `Component.remove()` still frees (`Tree::remove` unchanged); only
   `Node.remove()` became a detach, and Tesserae doesn't call it.
7. tre#10: `gc_repro2.py` panics on 0.3.3 and is clean on 0.3.4.
8. There's no Python pixel read-back in 0.3.4, so tests will check
   declared values.

## Phases 1–2 — decisions, migrate

User: "go with your recommendations for M33".

1. `.venv` pinned to the v0.3.4 wheel. Baseline 1 failed.
2. `get("fill")` works on 0.3.4: `tre`'s dialog and side-sheet scrims
   read `(0, 0, 0, 82)` with opacity 1.0, and a spec's `"#00000052"`
   reads `(0, 0, 0, 82)`. So the fragments match exactly, and the tests
   compare fills.
3. Two fragments and six labels fixed; `_assert_scrim_matches` in the
   overlay tests; `tests/test_paint_0_3_4.py` (163 cases). With the fix
   stashed: 2 overlay failures and 8 scan failures (6 labels, 2 scrims).
4. 418 passed; examples clean; `mkdocs build --strict` clean.

Hook: a GateGuard pre-Bash check asked for the request and the
command's purpose before the pin; stated, then run.

## Phase 3 — verify, docs, tracker

User: "start Phase 3".

1. `tests/test_thread_gc.py`. The old `venv-033` pointed into the
   removed worktree, so a fresh `venv-033w` was built from the saved
   v0.3.3 wheel: there the test fails with the `PanicException`; on
   0.3.4 it passes.
2. `ci.yml` ref `v0.3.3` → `v0.3.4`. Not pushed, so no CI run yet.
3. `installation.md`, `README.md` → v0.3.4 (release assets checked:
   CPython 3.9–3.15 wheels). Transparency section in the themes guide.
4. 419 passed; `mkdocs build --strict` clean. Gaps moved to fixed.

## CI

User: "push it and check the CI run". Pushed `e8b23c3..73b31da`. CI run
36178911095 green: `tre` at `29800f3`, built `tre-0.3.4`, 417 passed and
2 skipped (the two live tests; no display), no unraisable warnings. Docs
deploy green. M33 complete.
