# LOG — `tre`'s Building-Block Program (M34–M43)

*(Replaces M33's log — M33 is complete, committed and pushed.)*

- User: "push it, and scope tre's building-block program". Pushed
  `78884c3`.

## Scoping

1. Read `tre`'s program on `origin/main` (`68c3883`): its tracker's
   M93–M103 and D1–D11, and `docs/design/target-api.md` (purpose, R1–R12,
   node kinds, "Rebuilding the MD3 widgets", "Tesserae's needs",
   migration table). M97 is the gate; Phase 2 Step 2 stubs out removed
   names and runs Tesserae's suite.
2. Inventoried `src/tesserae`: imports from `tre`, every `add_*`/`set_*`/
   `reconcile`/`instantiate`/`from_view`/`show_view`/`open_*` call, and
   node kinds in fragments and examples (`Rect` 44, `Text` 43,
   `Container` 42, `Icon` 23, 12 MD3 kinds).
3. Found that `engine-md3`'s color science wraps the Rust
   `material_colors` crate. The node graph is "framework" in the
   migration table.
4. Spike on 0.3.4 (2,000 box+text pairs): `create`/`set`/`add_child`
   build 9.5 ms, re-color 0.8 ms; `View(spec=)` 10.9 ms,
   `set_theme` 2.3 ms.
5. Program M34–M43 written into the tracker, with decisions P1–P8.
   Not approved yet.

## M34 Phase 1 — design, decisions

User: "push it and go with your recommendations for M34". Pushed
`32abc04`.

1. Read `tre`'s reactivity (`python/tre/__init__.py` at v0.3.4): pure
   Python, ~400 lines; native only for the recording stack. `Computed`
   recomputes eagerly on a dependency change, so P3's "lazy" was wrong
   and is corrected.
2. Sized the Rust pieces Tesserae takes over (non-test lines): binding
   ~530, cascade ~230, reconciler ~420, spec ~530, build ~1,080, theme
   ~140, MD3 color/typography/shape ~600, icons ~120.
3. `docs/design/building-blocks.md` plus a "Design" nav section;
   `mkdocs build --strict` clean.
4. Step 3 (ask `tre` for its migration guide) and the color-science
   spike's package download wait on the user's OK.

## M34 — message to `tre`, colour spike

User: "push it, send the message to tre, and download it". Pushed
`761191f`.

1. Message sent to the `tre` session: the same socket address as every
   earlier exchange, checked in this session's transcript. The one
   ListAgents peer is titled "Milestone 5". It asks for the migration
   guide, proposes the gate-check shim, asks about the node graph, and
   notes tre#12.
2. `pip install materialyoucolor` into a scratch `venv-mcu`: 3.0.4,
   MIT, pure Python, needs Pillow.
3. Parity against `tre`'s `Window.theme.role` for 49 roles, 8 seeds,
   light and dark (784 values): spec 2025 differs in 695; spec 2021
   differs in 32, all light `on_*_container`. `tre` uses tone 10 and
   materialyoucolor tone 30; tone 10 from the scheme's palettes matches
   all 32. 784/784.

## `tre`'s reply

`tre` agreed to everything and started its M97 Phase 2 (local commits,
not pushed):
- `TRE_FORBID_REMOVED=1` switches on a `tre/_removed.py` shim covering
  all of 0.3.5;
- `tools/dump_widget.py` dumps widgets as diffable JSON, with a reference
  page for all 57 legacy factories;
- behaviour write-ups, and an audit of `binding.rs`/`cascade.rs`;
- icons are 12 SVG `d=` strings (view box `0 -960 960 960`);
- the node graph goes on primitives, with edges on `canvas`.
Recorded in M34 Phase 1 Step 3, M41, M42 and M43.

## M44 — logging with loguru (outside the program)

User: "Id like to use loguru for logs and console outputs for tesserae.
Can we set that up while we wait for tre". Asked three questions; the
user took the recommendations: on by default, failed background reloads
logged (not raised through `tre`), examples on `logger`. `loguru` 0.7.3
installed. `tesserae/log.py` with `configure_logging`; logging in
`watch.py` and `app.py`; the `logs` fixture; four tests rewritten, seven
added; docs. 426 passed. Recorded as M44.

## M34 Phase 2 — spikes; M34 complete

User: "push it and run the two spikes". Pushed `d5e7dfc`. The app quit
mid-run; resumed.

1. `cascade_cost.py`: Tesserae 20.7 / 2.8 / 0.7 ms against `tre`
   11.0 / 3.1 / 0.5 ms (build / theme switch / bound update), with
   matching results. The profile puts half the build in the rule scan.
2. `checkbox_on_primitives.py`: 6/12 at first. A simulated press and
   release already counts as a click, so the extra click toggled back;
   Tab needed a second focusable node. Then 12/12.
3. Spikes kept in `tools/spikes/` with a README.
