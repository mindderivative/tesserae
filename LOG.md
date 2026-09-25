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
