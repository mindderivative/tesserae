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

## `tre`'s handover; the gate dry run; M39 Phase 1

`tre` sent its M97 Phase 2 handover and asked for Step 6.

1. Dry run of `_removed.py` (0.3.5, `c49b85f`) from a scratchpad pytest
   plugin: 583 failed / 327 passed, nearly all at `Window.set_theme`.
2. A static scan showed `src/tesserae` uses none of M98's names; the
   rest is M99's (the legacy kinds, `tesserae.widgets`, `set_theme`).
3. Examples: counter and multi_screen run clean; todo_list stops at
   `add_checkbox`.
4. Fixed an unused `from tre import View` (`dae9ff3`).

User: "Yes do as recommended". Sent the report to `tre`; pushed
`cd1632e`, `dae9ff3`, `3631991`. (`3631991` carried a tracker line the
generator rejected, because a pipe hid its failure; fixed in the next
commit.)

M39 Phase 1: on_click nodes are focusable buttons. `role=None` isn't
settable, so removal uses `role="none"`. The reconciler patches on
handler changes. 5 tests; 3/3 mutants caught; 1048 passed.

## M39 Phase 2: state layer and ripple

User: "Push and start 39 phase 2". Pushed `96a7ae3`.

Probes on 0.3.4:
- Hovering a child box gives the parent no `pointer_leave`.
- `pointer_down` bubbles, with `target`; `x`/`y` are local to `current`.
- A keyboard click has `x=None`.
- `focus_visible` is True from Tab and False from a press.
- `layout_width`/`layout_height` give the laid-out size.
- A single `advance(1000)` is one tick, so a fade chained from a timer's
  `on_complete` needs one more frame. The tests step in 16 ms frames.

Design choices:
- The layer and ripples paint after the content (Material Web, Compose),
  which also keeps the reconciler's child indices valid.
- Focus shows the 10% layer only for `focus_visible`, or every clicked
  button would stay tinted.
- Material Web's ripple timing, including the 225 ms minimum press; a
  `stroke_width` animation serves as the timer.
- Rect and Container only; Text, Link, Image and Icon can't hold children.

16 tests; 8/8 mutants caught (one needed a stronger assertion on layer
order with content). 1064 passed.

## M39 Phase 3: focus ring and accessibility

User: "Yes". Pushed `7082b6c`.

Probes on 0.3.4:
- The `set()` error lists every property; the accessibility ones are
  `role`, `label`, `value*`, `checked`, `selected`, `expanded`,
  `disabled`, `level`, `live` and `a11y_hidden`.
- `a11y_action` takes `increment`, `decrement`, `expand`, `collapse`,
  `scroll_into_view` and `set_value`. `click` and `focus` aren't among
  them.
- `disabled=True` still takes Tab focus and clicks: it's only announced.
- `live` is off/polite/assertive or None; `level` is a positive int or None.
- A box's stroke is drawn inside it (tre's paint docs), so the ring is a
  box 5 px out with a 3 px stroke.

Design: the node's own `clip_children` (Phase 2) would clip a ring
outside it, so a clip box now holds the layer and ripples, and the node
stays unclipped. That also lifts Phase 2's limit.

Correction: Phase 2's commit says 1048 -> 1064, but it holds 1068 tests.
`test_paint_0_3_4.py` checks every YAML block in the docs, and the new
guide's blocks were written after the test run.

24 new tests; 11/11 mutants caught (one needed a new test). 1094 passed.

## M39 Phase 4: closing pass; M39 complete

User: "Yes". Pushed `66d5b8a`.

- Example buttons had no labels, so a screen reader would say only
  "button". Each now has `a11y: {label: ...}`. The purple and red filled
  buttons also have a white tint, since the default `on_surface` would
  hardly show on them.
- Adding those fields broke 5 tree-parity cases: `tre`'s builder rejects
  unknown fields. `treediff.for_tre` strips `a11y`/`interaction` from
  `tre`'s copy.
- A keyboard-only test of the counter example, through `App`.
- All three examples run cleanly. 1095 passed.

## M40 scoped

User: "Push and scope M40". Pushed `90bc4dc`.

Read `tre`'s `legacy-behavior.md` (0.3.5) for the controls. Read
`tre`'s tracker: M98 is complete on 0.3.5, and M99 waits on Tesserae's
M40–M42.

Probes:
- In Tesserae, clicking a YAML Checkbox or Switch leaves it unchanged,
  and Tab skips both; the Slider is focusable.
- The same in `tre`'s `View` and `add_checkbox`: none toggle, focus or
  have a role.

Carousel and Splitter were never in `tesserae.widgets`; Link is
Tesserae's since M37.

Q1–Q4 are in the tracker, with recommendations.

## M40 Phase 1: the control foundation

User: "Push it and go with your recommendations for M40". Pushed
`f19573b`; Q1–Q4 as recommended.

- `Interaction` gained `surface=` (events from the target, feedback in
  a child) and `enabled`.
- `Listeners` was taken out of `View._listen`, so controls share a
  view's dispatcher.
- `tokens.BASELINE` holds MD3's published colours, from `tre`'s
  handover plus `on_surface` and `secondary`; `build._BASELINE` reuses it.

Found while building:
- `layout_x`/`layout_y` are window-wide, not parent-relative. The first
  surface ripple offset was wrong off the origin; a test places the
  control at x > 0.
- `animate(prop, v, 0)` lands on the next frame, so a non-animated
  repaint uses `set` (`Control._to`).
- The tracker generator needs each Step on one line.

19 tests; 10/10 mutants caught. 1114 passed.

## M40 Phase 2: radio buttons and switches

User: "Push it and start Phase 2". Pushed `4c48958`.

Probed: `translate_x` and `scale` animate, and `layout_x` includes the
translation; `width` can't be animated. So the switch handle is a 28 px
circle, scaled to 16, 24 or 28 px, and slides with `translate_x`.

- `RadioGroup` behaves like HTML same-name radios: one Tab stop, the
  arrow keys wrap and skip disabled buttons.
- `Control.target` allows a non-square target (the switch is 52×48).
- `Interaction(ring_around=)` puts the switch's ring around its track.

13 tests; 11/11 mutants caught. 1127 passed.

## M40 Phase 3: the slider and the spin box

User: "Push it and start Phase 3". Pushed `72ed9e0`.

Probed:
- After `capture_pointer()`, moves and the release arrive with `x`
  relative to the node, however far outside.
- A `text_input` fires `change` on every edit.

Found by a test: Python's `round()` rounds half to even, so 5 with step
2 snapped to 4. It now rounds half up, as HTML's range input does.

SpinBox is three targets, so it isn't a `Control`; same API.
15 tests; 12/12 mutants caught. 1142 passed.

## M40 Phase 4: progress, loading, the time picker dial

User: "Push it and start Phase 4". Pushed `5c86537`.

Probed:
- `path` takes arcs and curves.
- `rotation_deg` and `trim_*` animate.
- `animate("data")` morphs any two outlines, resampling them itself, so
  the handover's shapes needn't share commands.
- `get("data")` reads back normalised.
- The window root lays out in a row. A first probe placed the dial past
  the window's edge and looked like a bug.

Mutants: 11 of 12 caught, after the linear sweep test was tightened to
count wraps. The generation bump on settling is equivalent: settling's
`stop_animation` ends the loop, since a stopped animation never
completes.

15 tests; 1157 passed.

## M40 Phase 5: wiring the controls in

User: "Push it and start Phase 5". Pushed `d5abfe2`.

- The eight kinds compile to controls. The view's bindings, `two_way:`
  and `on_change` go to the controls' `Signal`s and `on_change`. The
  legacy change-slot suppression is deleted.
- New `group:` on RadioButton.
- The factories return controls (P6).

Found:
- A duplicate-keyword bug in the first `_patch_control`.
- My first fragment-comment rewrite cut the LoadingIndicator's file at a
  `params:` inside its comment; I restored it from git and redid it,
  anchored on the real line.
- A dial test expected 10 after 11 + up; 11 + up is 12 AM, which is 0.

Mutants: 10 of 11 caught; the trial's own dispatcher is equivalent.
1179 passed.

## M40 Phase 6: the gate; M40 complete

User: "Push it and start Phase 6". Pushed `ec8272a`.

- tre's `_removed.py` (0.3.5), run from the scratchpad: the counter,
  multi_screen and todo_list examples are clean. todo_list got past
  `add_checkbox`.
- Under the shim, a standalone `View` still called `Window.set_theme`;
  removed, since nothing reads the window's theme now.
- New: `tests/test_no_tre_controls.py` (an AST scan of `src/tesserae`)
  and `docs/guide/controls.md`.
- Found: `mkdocs build --strict -q` exits 0 on a missing nav page, since
  `-q` stops warnings being counted. Rerun without it, the docs are
  clean. Recorded in memory; the check now runs without `-q`.

1183 passed.

## M41 scoped

User: "Push it and scope M41". Pushed `4c06650`.

Scanned `tesserae.widgets` for `tre` calls: 36 remain, 27 of them
M41's. The fragments cover the fixed-shape widgets; the list-driven ones
have none. `tesserae.icons` already has `tre`'s 12 icons.
`show_layer`/`hide_layer` are 0.3.4's overlay primitives.

Conflict found: removing `App`'s `Window.set_theme` can't be done in M41,
since M42's widgets still read the window's theme (Q4).

Q1–Q4 are in the tracker, with recommendations.

## M41 Phase 1: the composed-widget base

User: "Push it and go with your recommendations for M41". Pushed
`411ddca`; Q1–Q4 as recommended. Q4 moves the window-theme step to M42
Step 4.

Found while auditing the button fragment:
- Its label was 0 px wide and uncentred: tre's text has no intrinsic
  size. The compiler now measures text (`measure_text`; `line_height` is
  a multiple of the font size, which a test first got wrong).
- `patch` passed `align_items`/`justify_content` twice, a TypeError on
  any re-theme of such a node since M37 Phase 4. Fixed, with a
  regression test.

Mutants: 8 of 8 caught after a test for building after a re-colour.
1198 passed.

## M41 Phase 2: buttons and actions

User: "Push it and start Phase 2". Pushed `4b476cd`.

- The five factories are built from fragments; the button group is
  assembled from button fragments.
- Audit: the fragments now centre their content; the standard and
  outlined icon buttons use `on_surface_variant`.
- Probed: an ancestor gets `pointer_enter` when the pointer lands on a
  child; `pointer_leave` fires while a press is held (a test that pressed
  without moving in first never entered the node).
- Mutants: 11 of 12 caught after redoing one break and tightening the
  split test; `release()` before a press is equivalent.

1205 passed.

## M41 Phase 3: containment and lists

User: "Push it and start Phase 3". Pushed `c18a8a4`.

- Ten factories built from fragments, with behaviour: filter chips
  toggle, input chips remove, accordion headers and tree nodes expand.
- Found: a `link()`'s click never fired, because tre 0.3.4's `text`
  gets no pointer events, so every YAML `Link` since M37 was
  keyboard-only. A Link is now a box holding its text. Then a patch's
  a11y reset cleared the box's label, fixed.
- Audit: chips are padded and centred; the list headline is
  `body_large`.
- Mutants: 12 of 12 caught.

1209 passed (14 tre-parity tests went with their file).

## M41 Phase 4: navigation

User: "Push it and start Phase 4". Pushed `e8d6ea4`.

- Tabs, rail and drawer are built in Python (no fragments) on a shared
  selection helper; toolbars, the top app bar and the status bar come
  from their fragments.
- Measured tre's widgets first (150x48 tabs, 80x52 rail items, a 356 px
  drawer), then used MD3's numbers.
- Found: `Widget` marked interactive parts before running `edit`, so the
  app bar's added icon buttons "didn't exist". Reordered.
- A toolbar test overflowed its window and flexbox shrank the toolbar.
- Mutants: 10 of 10 caught after tightening three tests.

1214 passed.

## M41 Phase 5: overlays

User: "Push it and start Phase 5". Pushed `f5c2d64`.

Probed tre's layers: anchored placement flips to fit; `dismiss` comes
on Escape and on an outside press without hiding; hiding returns focus;
modal layers trap focus; animations run on nodes in no tree, so they
work as timers.

- `tesserae.overlays` has six overlays; the factories move onto them.
- A menu of `menu_item` widgets must use each item's own dispatcher, or
  its listeners would replace the item's (tre keeps one per event).
- Mutants: 11 of 12 caught; the timer's generation check is equivalent.

1227 passed.
