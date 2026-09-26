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

## M35 — reactivity in Tesserae

User: "push it and start M35". Pushed `7e508a7`.

1. Read `tre`'s reactivity at v0.3.4 (Computed, Effect, ViewModel, the
   `_core` recording imports). `tre` is MIT, same author.
2. `src/tesserae/reactive.py`: the same code with a Python recording
   stack, plus the bridge: with no Tesserae frame open, reads go to
   `tre._core._record_read`, so `tre`'s `View._attach` bindings still
   track them.
3. `tests/test_reactive.py`: 13 tests × 2 implementations, plus a names
   test and bridge tests. The shadowing mutant wasn't caught at first;
   the real case is `untrack` inside a method a binding calls. Writing it
   found that `tre`'s grammar needs `info.described()`, not
   `described()`. 5/5 mutants caught.
4. The full suite once failed intermittently in an M44 test: a race
   between the watcher thread's ERROR and DEBUG log lines. Fixed by
   waiting for the DEBUG line. 455 passed.
5. Docs updated everywhere reactivity was called "tre's, re-exported".

## M36 Phase 1 — evaluator

User: "push it and start M36". Pushed `9d00521`.

1. Read `tre`'s grammar, evaluator and resolver at v0.3.4. Found no
   Python entry point to the evaluator, so the harness goes through a
   `View` Text binding: `tre`'s "expects a string binding, got X"
   message exposes its exact value form.
2. `src/tesserae/binding.py` (lexer, parser, evaluator, resolver,
   `value_debug`).
3. Parity: 32 failures at first, all the harness's own (the error text
   names the ViewModel's class, and the two sides used different class
   names). Then 166/166. Checked tre's side was real values, not matching
   harness errors (81 values, 82 errors, including wraps and `Float(inf)`).
   6/6 mutants caught.
4. `guide/bindings.md`.

## M36 Phase 2 — wiring staged into M37

Read `tre`'s `apply_binding_value` and handler wiring: all legacy calls
(`set_checked`/`set_selected`/`set_text`/`set_layout`/`animate` with old
names/`set_on_*`). Probed the new API on `View`-built nodes: text, fill
and width work, and programmatic `set` fires no change event. On a
legacy Checkbox or Switch, `set(checked=)`/`set(selected=)` sets only
the a11y flag, and no synthetic click toggles one. Asked the user; they
chose "Move wiring into M37". M36 closed as the evaluator; wiring steps
added to M37 Phase 2 and M40.

## M37 scoping

User: "push it and scope M37". Pushed `cbdf82c`.

1. Read `tre`'s `spec.rs` (15 kinds, the style fields) and `build.rs`
   (`build_tree`, `patch_node`, layout, paint, text, per-kind fields,
   token resolution through `engine-md3`).
2. Probes on 0.3.4:
   - `box` defaults to horizontal/`auto`;
   - no `elevation` property, only `shadows`;
   - a `text` node has no intrinsic size, and neither does a `View`
     Text (0 px tall), so no regression;
   - `window.root` has 16 px padding;
   - a legacy `add_checkbox` node moves into a created tree and still
     works, but a node from another window's tree doesn't.
3. Coupling counts: 15/39 test files use `tre.View`; 135 `.node()`
   lookups; 28 `get_text()`.
4. Six phases and decisions Q1–Q4 written into the tracker.

## M37 Phase 1 — tokens

User: "push it and go with your recommendations for M37". Pushed
`42d0b70`.

1. Read `engine-md3`'s shape and type scales, and `engine-render`'s
   key/ambient shadow geometry.
2. `materialyoucolor` 3.0.4 installed in `.venv` and added as a
   dependency.
3. `tokens.py`. Pillow's colour parser missed CSS Color 4 syntax, and a
   probe of 20 strings against `tre` showed it; added `rgb()`/`hsl()`
   parsing. A rounding slip (50% gave 127, not 128) was caught the same
   way. Wide-gamut functions raise, and are listed as a known gap.
4. 74 tests. The type scale is compared at f32. A mutant that seemed to
   survive (`spec_version`) had only changed the docstring; mutating
   the call itself gives 18 failures.

## M37 Phase 2 — compiler and cascade

User: "push it and start Phase 2". Pushed `dcc2bbd`, `fe7e6ee`.

1. Read `tre`'s per-kind build rules, `required_background`/
   `required_foreground` (the not-a-fill check reads inline `style:`
   only), the state-field checks, `resolve_style_layered`, the error
   texts, the shipped default theme and the icon table.
2. Probes: the legacy factory signatures; `text_input`'s `fill` is its
   glyph colour; the new defaults match the legacy ones; `create` won't
   take `align_items=None`.
3. `icons.py` (extracted from `tre`'s source), `default_theme.yaml`,
   `cascade.py`, `build.py`.
4. 42 tests. A test fix: `tre` reads path data back normalised.
   Mutants: 5/5 caught after adding the stylesheet-background Text case.
   741 passed.

## M37 Phase 3 — tree parity

User: "push it and start Phase 3". Pushed `6c6dde1`.

1. The corpus: the fragment calls, generated from their `params:`, and
   the suite's inline views, harvested with `ast`, plus the examples and
   docs.
2. The first exploratory run: 89/121 identical. Differences: the
   TextField `fill` (tre reads back its text colour, fixed `#1C1B1F`,
   found in `engine-core`); Checkbox/Slider corner radius (the cascade's
   paint wasn't applied to the MD3 kinds); Link text unreadable on
   tre's side; unsized root height (content-sized in `from_view`).
3. Fixed each, and made the differ skip what tre can't read.
   100/100, then 127/127 with the examples, docs and the Image fragment.
4. The acceptance check first dropped 56 fragments because it built tre
   views without a seed. SpinBox exposed Tesserae accepting a number as
   text content; it's now rejected, as in tre.
5. Mutants: 3 of 4 caught; level 5 is pinned by `test_tokens.py`.

## M37 Phase 4 — View, reconciler, wiring

User: "push it and start Phase 4". Pushed `29743ac`.

1. Read `tre`'s `reconcile.rs`: match by id; patch when props differ;
   rebuild on a kind change; remove missing children; append only.
2. Split `build.py` into props functions plus `create`/`patch`;
   170 compiler and parity tests unchanged.
3. `view.py`. Smoke-testing found:
   - `Node.off(event)` takes no handler;
   - `on` keeps one listener per event, so each node and event gets a
     dispatcher;
   - the legacy Checkbox's change slot fired during binding application
     (now suppressed);
   - a re-style reset the legacy checkbox state, and two-way wrote False
     back (restyles now leave state alone).
4. `ViewWatcher` handles a Tesserae `View`.
5. 23 tests. Mutants: the ordering one survived because `parent() is not
   outer` was always true; fixed with `!=`, then caught. 900 passed.

## M37 Phase 5 — components and screens

User: "push it and start Phase 5". Pushed `055737c`.

1. `Component`, `View.instantiate`, `View.move_to`, path sources and
   `View.click`; `tesserae.instantiate` builds into a Tesserae parent.
2. `App` owns its window from the start, builds screens into it, and
   switches them with attach and detach.
3. The switch-over broke 17 tests:
   - tests registering `tre` views, fixed by exporting Tesserae's
     `View`, which takes a path;
   - `get("elevation")` readbacks, now `helpers.elevation` from
     `shadows`;
   - an unvalidated malformed stylesheet (the cascade now validates);
   - colour wording (now `tre`'s);
   - two `tre`-only behaviours (updated);
   - out-of-range elevation markers.
   913 passed; the examples run.
4. Mutants: the re-theme propagation survived until the test checked
   each host change separately.

## M37 Phase 6 — tests, docs; M37 complete

User: "push it and start Phase 6". Pushed `3d468a1`.

1. Production: `load_view` builds a Tesserae `View`; the `tre` fallbacks
   in `instantiate`/`ViewWatcher` and `push_frames` removed; the M35
   bridge removed.
2. Failures, and what they found:
   - `test_images` (rewritten to check pixels);
   - `test_themes`: a theme's unknown top-level key went unchecked, and
     Tesserae now validates it, naming the file;
   - `test_watch_thread`: a failed root rebuild destroyed the old tree,
     so reconcile is now all or nothing.
3. Fragment tests moved to `helpers.view_from`/`elevation`. The SpinBox
   test reads the TextField's box via `parent()`, and the DatePickerDay
   test uses a seed and Tesserae's wording.
4. `get_text` became `get("text")` on Tesserae nodes; examples use
   `simulate`.
5. Docs and docstrings swept. 909 passed; examples clean.

## M38 scoping

User: "push it and scope M38". Pushed `cf39d3d`.

Read `tre`'s motion curves (Emphasized is two cubic segments), its
`ThemeChanged` handling (it flips only the window theme and fires
`color_scheme`), the window properties (the OS appearance isn't
readable), `ThemeSpec` (`components:`/`typography:`), and the
typography/shape lookups (overrides reach factories only, not views).
Four phases and decisions Q1–Q4 written into the tracker.

## M38 Phase 1 — Theme

User: "push it and start Phase 1". Pushed `7720fe9`, `9659fdc`, `4c03c33`.
Read `tre`'s component lookup (variant, then bare key) and
`resolve_components`. `theme.py`, `app.theme`/`view.theme`. 110 tests,
109 of them against `tre`'s `Window.theme`; 3/3 mutants caught. 1019
passed.

## M38 Phase 2 — typography in views

User: "push it and start Phase 2". Pushed `17df8a0`. Typography
overrides ride on the prepared layers (`Layers`), so no call site
changed; `_text_style` applies them for Text/Link only. 8 tests, 3/3
mutants caught, 1029 passed.

## M38 Phase 3 — light and dark

User: "Push and start phase 3". Pushed `8437295`. `App` gained
`dark="system"`, `set_dark`, the `color_scheme` listener, and
`dark`/`dark_mode`. No existing test assumed light. 10 tests; 3/3
mutants caught. 1042 passed.

## M38 Phase 4 — docs; M38 complete

User: "Yes". Pushed `349d0bb`, `1dceb2b`. M38 added to `ARCHITECTURE.md`
and the design page; a known gap for `"system"` starting dark;
`Window.set_theme` removal moved to M41.

## M39 scoping

User: "Yes". Pushed `315cfb7`. `tre`'s `0.3.5` branch has `dump_widget.py`,
`legacy-behavior.md` and the MD3 handover (local commits `da2f475`,
`9f926d6`, `1686796`). Read the state layer and ripple section. Probe:
an `on_click` Rect is focusable, a Tab stop and Enter-activated in
`tre`'s `View`, but none of those in Tesserae's -- a regression, now in
known gaps. Roles: `tre`'s `View` nodes report none via `get()`.
