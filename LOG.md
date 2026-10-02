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

Follow-up: the gate blocked `docs/guide/overlays.md`, and the commit went
ahead because that command chained with `;`, so `13434a3` pointed its nav
at a missing page. `mkdocs build --strict`, now run without `-q`,
reported it (exit 1). The page is added in the next commit; commits now
chain on `&&`.

## M41 Phase 6: the gate; M41 complete

User: "Push it and start Phase 6". Pushed `e3682f3`.

- `test_no_tre_controls.py` now forbids M41's names too; clean.
- Under tre's shim: the examples and the 152 widget tests are clean.
  The whole suite is 599/497 (was 327/583); the rest is planned
  (`tre.View`/`tre.Signal` tests for M43, `Window.set_theme` for M42,
  M42's widgets).
- Found: the shim removes `add_image_from_bytes`, which D6 kept, so
  `image()` joins M42.
- The widget catalog's pro-delegation paragraph was out of date after
  Phase 2; rewritten.

1227 passed.

## M42 scoped

User: "Push it and scope M42". Pushed `6e48798`.

- Read tre's removal list and `target-api.md` (0.3.5).
- Eight `tesserae.widgets` functions are still tre's. `App` and six test
  helpers theme windows (219 shim failures).
- Found: docking's framework API (`dock_target`/`dock_drop`,
  `set_active_panel`) is 0.3.5-only, so docking can't be built on 0.3.4.
  Tesserae never exposed it, so M99 doesn't wait on it.
- tre's node graph has no drag or edges.

Q1–Q4 are in the tracker, with recommendations.

## M42 decisions

User: "Q1 - Build them all in M42 / Q2 - Recommended / Q3 - Recommended /
Q4 - Recommended".

- M42 grows to 8 phases: the new widgets (segmented button, pagination,
  popover, time input field, carousel, splitter) join it.
- Docking and the app shell become M45, after M43, on 0.3.5's docking
  events.
- Nothing pushed; no push was asked for.

## M42 Phase 1: search

User: "Push it and start Phase 1". Pushed `0df3db2`.

- Audit: tre's search bar (and the fragment) put the placeholder in the
  field as text; it's hint text now. `text_input` takes no
  `line_height`.
- SearchView is an overlay under the bar, driven by the field's focus,
  typing and keys, with rows built once and attached as needed.
- Mutants: 10 of 10 caught after redoing a break that hadn't applied
  and adding a test for shrinking results.

1233 passed.

## M42 Phase 2: date and time

User: "Push it and start Phase 2". Pushed `9b1cb55`.

- Measured tre's period selector (52x72, 36 px halves) and time field
  (96x72, 45 px), then used MD3's numbers where they differ.
- `text_input` takes no `text_align`, so the time field is centred by
  sizing the input to two digits, re-applied after a re-colour (which
  resets a TextField's layout).
- A test first expected a change event for typing "1" over a 1.
- Mutants: 10 of 10 caught after pinning the width in a circular
  centring check.

1242 passed.

## M42 Phase 3: media

User: "Push it and start Phase 3". Pushed `40d1bfb`.

- `push_frame` is on tre's removal list too; its replacement is setting
  `rgba`/`pixel_width`/`pixel_height`.
- A re-colour re-applies a view's frames, so `video.frame()` records the
  latest there.
- Found: the video's spec id was `image`, so its frames were keyed
  wrongly; a re-colour test caught it.
- Mutants: 6 of 6 caught.

1244 passed.

## M42 Phase 4: the node graph

User: "Push it and start Phase 4". Pushed `24f3add`.

- Probed transforms: a 0x0 box scales about its origin, and hit testing
  follows the transform, so panning and zooming are a translate and a
  scale on one content box.
- Edges are cubic paths re-routed on moves.
- Mutants: 8 of 9 caught; the 9th exposed dead re-colour code, removed.
- With this phase, no `tesserae.widgets` function delegates to tre.

1251 passed.

## Review of M42 Phases 2–4 (after the move to Nobara)

User: "Yes, review them then continue with M42". The three commits
(`40d1bfb`, `24f3add`, `f50dfd0`) were made on the other machine and
pushed there; `origin/main` matched.

Found and fixed:
- `node_graph.set_theme` didn't re-theme its nodes; the test had
  re-themed each node itself.
- A graph node took keyboard focus with no ring, and clipped its
  children, so a ring couldn't show. It now has MD3 feedback, including
  the dragged state layer, and its title bar rounds its own corners.
- The period selector's tabs were in a `group`, not a `tablist`.

Each fix is covered: undoing it fails a test. 1252 passed.

## M42 Phase 5: segmented button, pagination, popover

Per Q1, three widgets tre had and Tesserae never wrapped, checked
against tre's dumps in `legacy-widgets.md` (0.3.5).

- `segmented_button`: one 1 px outlined pill, padded 1 px so a selected
  fill doesn't cover the outline; per-corner ends on the segment and its
  feedback clip. Single-select is a radio group (one Tab stop, arrows
  select); `multi=True` is checkboxes (arrows move focus).
- `pagination`: previous, pages, next; the ends disabled at the bounds.
  Previous is `chevron_right` turned 180°, since there's no
  `chevron_left` among the 12 icons.
- `Popover`: MD3's rich tooltip, persistent until dismissed; the text's
  height is measured wrapped, since the compiler measures one line.
- Mutants: 15 of 16 caught; the 16th showed re-turning the arrow after a
  re-colour was dead code, so it was removed.
- Docs: widget catalog (a stale "thin delegates" sentence removed),
  overlays guide, API index, `ARCHITECTURE.md`.

1273 passed.

## M42 Phase 6: carousel and splitter

User: "Push it and start Phase 6". Pushed `7842c23`.

- Read tre's `legacy-behavior.md` (0.3.5) for both, and 0.3.4's docs:
  no frame callback, and `width` doesn't animate, but `get` reads a
  property mid-animation.
- `carousel`: the position is an eased animation on a private node;
  `_Ticker` re-lays the items out each frame from it. The layout is a
  pure function (`carousel_layout`) blending the snapped layouts either
  side of the position.
- `splitter`: two panes and a 16 px handle; a drag puts the handle's
  middle under the pointer.
- Found by a test: an unsized node's `width` reads `"auto"`.
- Mutants: 16 of 17 caught (two after tightening tests); 1 equivalent.

1287 passed.

## M42 Phase 7: off the window's theme

User: "Push it and start Phase 7". Pushed `fea5f5e`.

- `App` no longer calls `Window.set_theme` (`_set_window_theme`,
  `_window_theme`, `_OVERRIDDEN_SEED` removed), nor re-asserts the
  window's theme after an OS switch.
- Tests that read the window's theme now read `app.theme`, and a new
  test pins that the window stays unthemed. The fragment tests' window
  helpers stop theming windows, which nothing read. The tre-reference
  tests keep `Window.set_theme` until M43.
- Mutation: re-theming the window fails 5 tests.

1287 passed.

## M42 Phase 8: tests, docs, the gate -- M42 complete

User: "Push it and start Phase 8". Pushed `93ce390`.

- `tests/test_no_tre_controls.py` forbids M42's names from `tre`'s
  `_removed.py` (0.3.5, `279e640`), and `set_theme`/`theme` on a window.
- Ran the suite and examples under `tre`'s switch (its `_removed.py`
  installed over the 0.3.4 wheel from the scratchpad): examples clean;
  739 passed / 419 failed, all deliberate `tre`-reference tests (`View`
  250, `Window.set_theme` 154, `Signal` 14, and tree parity's corpus).
- Fixed in tests: reading `window.theme` (removed outright in 0.3.5),
  `helpers.elevation`'s fallback to `elevation`, and `border_width`.
- Docs: the stale "thin delegate" wording in the widget docstrings,
  diagrams and docs home; the design page records the gate result.

1288 passed. M42 complete.

## M43 scoped

User: "Push it and scope M43". Pushed `9f52fc1`.

- `tre`'s `0.3.5` branch (`279e640`): M97 waits on Tesserae's
  confirmation (Step 6); M98 is complete; M99–M103 not started; no
  0.3.5 release.
- Under the switch, Tesserae's code and examples are clean; 419 tests
  fail, all comparing with `tre` on purpose (`View` 250,
  `Window.set_theme`/`theme` 154, `Signal` 14).
- Phases: the dry run (done), decisions, reference tests off `tre`, the
  switch in CI, confirm to `tre`. Q1 recorded reference data, Q2 a
  vendored `_removed.py`, Q3 the move to 0.3.5 as a new M46.

## M43 decisions

User: "Push it and go with your recommendations for M43". Pushed
`96e0129`.

- Q1: record `tre`'s answers once on 0.3.4 (`tools/record_tre_reference.py`
  -> `tests/reference/`); retire the tests of `tre`'s own behaviour.
- Q2: vendor `_removed.py` as `tests/tre_removed.py`; CI runs plain and
  with the switch.
- Q3: M43 ends at the confirmation; new M46 moves to 0.3.5 after `tre`'s
  release; M45 follows M46.

## M43 Phase 3: reference tests off tre's removed API

User: "Push it and start Phase 3". Pushed `1a525da`.

- `tests/reference.py`: `reference.tre(fn)` replays a recorded answer
  (or re-raises a recorded exception); `TESSERAE_RECORD_TRE=1` records.
  Tagged JSON keeps tuples, non-string keys and exceptions exact.
- `tools/record_tre_reference.py` records the seven parity modules on
  0.3.4 (refuses without `View`/`Signal`/`Window.set_theme`); saved only
  when every test passes. ~370 KB under `tests/reference/`.
- Converted binding parity, tree parity (spec + frames + `tre_dump` per
  case), spec build, tokens, the theme object, view and clickable error
  parity. Retired `test_reactive`'s `tre` half; `register()` now rejects
  any non-Tesserae object; the GC guard frees a `Window` and a node.
- With the switch on (no live `tre`), breaking the evaluator, colours,
  cascade or compiler fails the replayed tests, as do a tampered or a
  missing answer.
- Under `TRE_FORBID_REMOVED`: the whole suite passes; examples clean.

1288 passed.

## M43 Phase 4: the switch in CI

User: "Push it and start Phase 4". Pushed `0f90c46`.

- `tests/tre_removed.py`: `tre`'s `_removed.py` at `279e640`, unchanged
  below a source header.
- `tests/conftest.py` installs it with `TRE_FORBID_REMOVED=1`;
  `tools/forbid_removed.py` runs a script with it; a switched-only test
  checks the names are gone. A script using `Window.set_theme` exits 1
  under the runner.
- `ci.yml`: the suite and examples again with the switch on.
- Locally: plain 1288 (+1 skipped), switched 1289; examples clean.

## M43 Phase 5: confirm to tre -- M43 complete

User: "Push it and start Phase 5". Pushed `31fcc1b`.

- CI run 36293860118: every step green; plain 1286 passed / 3 skipped,
  switched 1287 passed / 2 skipped; examples clean both ways.
- At the user's go-ahead, sent the confirmation to `tre`'s session
  ("Milestone 5 (fork)"): commit, run, counts, changes since the dry
  run, next steps (M46, M45), and a request to hear if M100's renames
  go beyond `_removed.py` at `279e640`. Queued; no reply yet.

M43 complete.

## tre's reply to the M43 confirmation

`tre`'s session verified the confirmation against this repo (`31fcc1b`
on `main`, run 36293860118 green, `tests/tre_removed.py` identical to
its `_removed.py` at `279e640` below the header) and closed its M97
(`c348333`). M99 is unblocked on its side; the user decides when it
starts. The request about renames is its M100 Step 3: an updated
`_removed.py` or a note before the 0.3.5 release, so the gate can be
rerun.

## Gate rerun with tre's updated `_removed.py` (0.3.5 at 07be406)

At `tre`'s request (its M100 done). The new file adds only
`Event.source` and `Event.position` (diffed against the vendored copy,
read through the GitHub API). `tests/tre_removed.py` updated; both names
raise under the switch. Zero `RemovedError`s: 1289 passed switched, 1288
plain, examples clean. `tre`'s list of behaviour changes a name switch
can't catch went into M46's step. Reported back.

## M47 scoped: bindable accessibility

User: "Scope the a11y bindable gap as M47".

- Read `spec/build.py` (`_a11y_fields`, `_a11y_props`) and `view.py`
  (`_wire_binding`, `_apply`): `a11y:` is set once per build or patch;
  bindings know nothing accessible.
- The macro layer substitutes only a bare `{{ name }}`, so binding
  expressions pass through fragments. `tre` 0.3.4 can't report speech,
  so tests read `label`/`a11y_hidden`/`level`.
- Phases: decisions, bound `a11y:` in views, `tesserae.a11y.bind` for
  Python, tests/docs. Q1 inside `a11y:`, Q2 `label`/`hidden`/`level`
  (not `role`/`live`), Q3 the Python helper.

## M47 decisions

User: "Push it and go with your recommendations for M47". Pushed `132416c`.

- Q1: bindings written inside `a11y:`. Q2: `label`, `hidden`, `level`
  bindable; `role`/`live` fixed. Q3: `tesserae.a11y.bind` for Python.

## M47 Phase 2: bound `a11y:` in views

User: "Push it and start Phase 2". Pushed `a1c28ed`.

- Compiler: bound fields left to the view, not reset on patch; a bound
  `role`/`live` is an error. View: `_wire_a11y`, dependency-tracked,
  checked with `tesserae.a11y`, on the accessible node.
- Found: bindings are whole values (no interpolation; use a `Computed`);
  a Link's text binding overrode its `a11y:` label; a control's `a11y:`
  was dropped since M40. Both bugs fixed.
- 18 tests; mutants 10 of 11 caught, 1 equivalent.

1308 passed.

## M47 Phase 3: tesserae.a11y.bind

User: "Push it and start Phase 3". Pushed `2d918c5`.

- `a11y.bind(node, label=, hidden=, level=)`: a `Signal`/`Computed`, a
  function or a value per field, one `Effect` each, checked as
  `describe` checks, returning a stopper; `role`/`live` refused; a failed
  bind disposes what it set up.
- 9 tests; 7 mutants, all caught.

1317 passed.

## M47 Phase 4: example, docs -- M47 complete

User: "Push it and start Phase 4". Pushed `d968339`.

- `examples/counter`: a polite live count, and the button's name bound
  to "Increment, count is N"; `app.py` and the keyboard test check it.
- Docs home line; the known gap moved to "Fixed gaps".

1317 passed. M47 complete.

## M48 scoped: hot reload for register()ed screens

User: "Scope hot reload for register()ed screens as M48". Also recorded
(memory): once `tre` reports the 0.3.5 release, start M46 and push it,
then start M45.

- `_start_watchers` watches only screens with `_Registered.path`, which
  only `load()` sets. A `View` built from a file keeps `view.path`, and
  `move_to` keeps it, so no `path=` is needed.
- Phases: decisions (Q1 the file from the view; Q2 log a screen with no
  file), watch every file-built screen with tests, docs/example.
- Named, to check in Phase 2: whether components added by
  `tesserae.instantiate` are watched.

## M48 decisions

User: "Push it and go with your recommendations for M48". Pushed `81742fe`.

- Q1: a registered screen's file comes from `view.path`; no `path=`.
- Q2: a screen with no file is logged once when hot reload starts.

## M48 Phase 2: watch every file-built screen

User: "Push it and start Phase 2". Pushed `512b546`.

- `_start_watchers` reads `view.path`; `_Registered.path` removed; a
  spec-built screen is logged once.
- `tests/test_register_reload.py` (3); the live test runs for `load` and
  `register`. Mutants: the old rule fails 5 tests; no log line fails 1.
- Probe: a `tesserae.instantiate` component's file isn't watched -- new
  known gap.

1321 passed.

## M48 Phase 3: docs, example -- M48 complete

User: "Push it and start Phase 3". Pushed `786a1ba`.

- `guide/apps-and-screens.md`, `api/app.md` and `register()`'s docstring
  say a file-built registered screen is hot-reloaded; the multi-screen
  example's notes too. The gap moved to "Fixed gaps".

M48 complete.

## M46: move to tre 0.3.5

`tre`'s session reported v0.3.5 released; the user's standing go-ahead:
"Once you receive the message from tre about the release, start M46 and
push it, then start on M45."

- Checked the release on GitHub first: published, 24 assets, tag on
  `2e4ed35`.
- `.venv`: the release's cp314 wheel. 9 failures, one cause:
  `helpers.elevation` caught only `AttributeError`; 0.3.5's `get` raises
  `ValueError`. Fixed.
- Retired the vendored switch, its runner, conftest's switch and CI's
  second run; CI builds `tre` at `v0.3.5`.
- Reviewed `tre`'s behaviour changes. Click bubbling: pointer clicks
  already bubbled on 0.3.4 (M39's test); innermost-only was tried and
  reverted as a design change -- now a known gap to decide.

1322 passed.

## M45 scoped: docking and the app shell

Started after M46 by the user's standing go-ahead (which covered pushing
M46 only). Reported M46 to `tre` (queued).

- Read 0.3.5's docking stubs and `docs/guide/docking.md` at `v0.3.5`,
  and 0.3.4's `build_shell`; probed the wheel: a zone shows one panel by
  keeping only it as a child; `dock_target`/`dock_drop` report a
  headless drag; `window.on` keeps one listener per event.
- Phases: decisions, `Dock`, `AppShell`, example/docs. Q1 a Python API
  first; Q2 secondary tabs, tab as handle, highlight, keyboard "Move
  to"; Q3 splitters; Q4 `layout()`/`restore()`.

## M45 decisions

User: "Push it and go with your recommendations for M45". Pushed `0f49f65`.

- Q1 a Python `Dock`/`AppShell` first, `App.use_shell`; Q2 secondary
  tabs, tab as handle, highlight, keyboard "Move to"; Q3 splitters; Q4
  `layout()`/`restore()`.

## M45 Phase 2: tesserae.docking.Dock

User: "Push it and start Phase 2". Pushed `c3fd91e`.

- Probed 0.3.5: a drop over no zone keeps the panel; a drag can start
  on `pointer_move`; zones keep non-panel children; drags update both
  lists; `dock_panel` on a docked panel leaves it listed twice (worked
  around in `move()` with a drag; worth raising with `tre`).
- `Dock`: zones as tab strips over `tre`'s zone bodies, MD3 secondary
  tabs, click/Enter/arrows, drag past 4 px with a highlight, "Move to"
  menu (right click, Menu key, Shift+F10), theming, a11y.
- 15 tests; 14 mutants, all caught after two tests were tightened.

1337 passed.

## tre issue #14

User: "create a tre issue about the bug with set_active_panel." Filed
https://github.com/mindderivative/tre/issues/14 with a repro on the 0.3.5
wheel: `dock_panel` on a docked panel leaves it in the old zone's list;
`set_active_panel` there then makes it a child of both zones. Listed as a
known gap; `Dock.move()` keeps its drag workaround.

## tre 0.3.5.1: issue #14 fixed

`tre`'s session reported v0.3.5.1. Checked on GitHub (published, 24
assets, issue #14 closed); the repro now behaves. `.venv` and CI pin
`v0.3.5.1`; `Dock.move()` calls `dock_panel` and updates the model
itself (no `dock_drop` fires); a test pins that `move` sends no pointer
event. The known gap moved to "Fixed gaps".

## M45 Phase 3: the app shell

User: "Push it and start Phase 3". Pushed `00e2f2a`.

- `AppShell`: bars, navigation, the dock's zones around `content`, at
  100% of the window. Resize handles (splitter-styled) instead of M42's
  proportional splitter, since zones keep pixel sizes as the window
  resizes -- Q3's intent kept.
- `App.window`, `App.use_shell`; `layout()`/`restore()` on the shell.
- 11 tests; 16 mutants, all caught.

1349 passed.

## M45 Phase 4: center tabs, example, guide -- M45 complete

User: "Push it and start Phase 4 with center=True". Pushed `c04c51f`.

- `AppShell(center=True)`: the middle is the dock's center zone;
  `App.show` goes through `shell.show_screen` and screens are its tabs.
  3 tests, mutation-checked.
- `examples/app_shell/` (self-checking, in CI) and the "App Shell &
  Docking" guide page.

1356 passed. M45 complete.

## M49–M52 scoped

User: "Scope M49", then "Scope all as separate Milestones, 2 will be M49
as previously discussed". Each of the four named candidates is its own
milestone, researched from the source:

- M49, innermost clicks: seven activation-listener sites; `tre`'s
  `Event.stop()`; M46's reverted patch.
- M50, widgets follow the app's theme: every factory's result has
  `set_theme`, but nothing links a widget to an app, and `set_dark`
  skips the shell.
- M51, runtime components: `instantiate` drops the path; the watchers
  start once; `reconcile` re-adds a rebuilt root at the end.
- M52, declarative shell: the view pipeline has no pluggable kinds, and
  reconcile would fight the dock, so a separate `*_Shell.yaml` is
  recommended.

Also: the tracker generator was updated from the build-tracker skill, at
`tre`'s request (links, and a lone `~` in struck text).

## M49 Phases 1-2: the innermost clickable takes the click

User: "M49 start with recommendations" (Q1-Q4 as recommended).

- `listeners.handled(fn)`, from M46's saved patch, now wraps all 10
  activation sites, including the context menu attach and `Dock` tabs,
  for `click` and `secondary_click`. It stops the event even if `fn`
  raises, and even for a disabled control.
- M39's test now expects one click. 9 new tests; 12/12 mutants caught.
  A first mutation run faked a catch through a stale `.pyc`, so the
  script now runs with bytecode caching off.

1364 passed, all four examples clean.

## M49 Phase 3: docs -- M49 complete

User: "Start phase 3 with recommendations". The controls guide and the
widget catalog now say that a control or button inside a clickable
takes its own click. The known gap moved to "Fixed gaps". 1364 passed;
all four examples clean.

## M50 Phases 1-2: widgets and controls follow the app's theme

User: "Start 50 with recommendations" (Q1-Q3 as recommended).

- `tesserae.follow`: an app is found by its window. A widget or control
  with no `theme=` takes `app.theme` and follows it; `theme=` pins it.
- Followers are held strongly, not weakly as scoped, so a widget no one
  kept still follows. They're pruned on `destroy`, or when their node is
  found gone. `set_dark`, the OS switch and `set_theme_specs` re-theme
  views and followers with one rollback.
- The docs no longer pass `theme=app.theme` in snippets, since that
  would now pin the widget.
- 10 tests. 14/15 mutants caught; the survivor was a dead guard, now
  removed.

1374 passed; all four examples clean.

## M50 Phase 3: views, the shell and dock, overlays

User: "Start phase 3".

- A `View` on an app's window with no theme argument follows the app.
  `dark` now defaults to `None`, so `dark=False` pins it.
- `Dock` and `AppShell` follow. `_follow_theme` lets a following shell
  re-colour only itself and the dock it made, so a pinned bar stays
  pinned. Overlays follow through their widgets.
- `examples/app_shell/` has no `theme=` left, and checks `set_dark`.
- 7 tests; 12/12 mutants caught.

1381 passed; all four examples clean.

## M50 Phase 4: docs -- M50 complete

User: "Start phase 4". Added the widget catalog's opening note and the
themes guide's light and dark line. Removed the controls guide's stale
note that Python controls don't follow. The known gap moved to "Fixed
gaps". 1381 passed; all four examples clean.

## M51 Phases 1-2: components keep their file

User: "Start M51 with recommendations" (Q1-Q3 as recommended).

- `View.instantiate` records `component.path`.
- `reconcile` re-inserts a rebuilt root at its old index.
- Components whose nodes a host reload destroyed are forgotten and
  unwired.
- `tre`'s `off` on a destroyed node doesn't raise (checked), so the
  guard I first wrote was dead code and was removed.
- 4 tests; 7/7 mutants caught.

1385 passed; all four examples clean.

## M51 Phase 3: watching component files

User: "Start phase 4". Phase 3 hadn't been done, so I asked, and the
answer was "Phase 3, then 4".

- `ComponentWatcher`: one per component file. It rebuilds the spec once
  and reconciles each live instance from its own copy; a bad edit fails
  once. `App.watch_component` is called by `instantiate`, so mid-run
  components are watched too.
- `_stop_watchers` stops them all at the end of `run()`.
- 12 tests, plus a live case; 14/14 mutants caught after 5 survivors got
  tests.

1398 passed; all four examples clean.

## M51 Phase 4: docs and example -- M51 complete

- The components guide and README now cover component hot reload.
- `examples/todo_list/` says how to try it and checks that each row
  knows its file.
- The known gap moved to "Fixed gaps". A narrower one replaces it:
  components in a view the app doesn't know about aren't found.

1398 passed; all four examples clean.

## M52 Phases 1-2: the shell file

User: "Start M52 use recommendations" (Q1-Q4 as recommended).

- `tesserae.shell_file` checks the whole `*_Shell.yaml` schema and
  names each mistake by file and key.
- `build_shell` builds the existing `AppShell`; its bars stretch with
  the window and it follows the app's theme. `app.load_shell(path)`
  builds and uses it.
- `panels:` and `on_navigate` are checked but not acted on until
  Phase 3.
- 31 tests; 23/23 mutants caught.

1429 passed; all four examples clean.

## M52 Phase 3: panels and navigation

User: "continue to the next phase".

- A panel is a registered screen, or `<Name>_View.yaml` (plus its
  ViewModel) next to the shell file, registered under its name.
- Rail items call `app.show`, or `on_navigate`; `app.show` moves the
  rail's selection. References are checked before anything is built.
- `show_screen` brings a docked root's tab forward and tracks its
  content screen, so panels are never pulled out of their zones.
- 14 tests; 18/18 mutants caught.

1445 passed; all four examples clean.

## M52 Phase 4: hot reload of the shell file

User: "push and start phase 4". Pushed `a28acb4..8eea926` first; CI run
36386574658 passed (1444 passed, 4 skipped; the four examples clean).

- The shell file is watched. An edit patches the bars, the status text,
  zone sizes, the rail, and panels added or moved, keeping the user's
  drags and sizes. Structural edits are logged as needing a restart.
- `tre` can't undock a panel (probed), so removing a panel is a restart
  and a new known gap.
- 11 tests, plus a live case; 21/21 mutants caught.

1458 passed; all four examples clean.

## tre issue #16

User: "File a tre issue asking for an undock call". Filed
https://github.com/mindderivative/tre/issues/16. It proposes
`Window.undock_panel(panel)`, with the Phase 4 probe as the repro:
a detached docked panel stays in its zone's list, and
`set_active_panel` attaches it again. The known gap and the hot-reload
guide link to it.

## M52 Phase 5: the file-built example -- M52 complete

User: "Start phase 5".

- `examples/app_shell_file/` declares the studio in `Studio_Shell.yaml`,
  with no widgets made in Python. It's self-checking and runs with hot
  reload on; CI runs it next to `examples/app_shell/`.
- `App.screen(name)` gives a panel's view and the ViewModel the app
  built from a file, replacing the example's `app._registered` access.
- The README now lists all five examples; it had missed `app_shell/`
  since M45.

1473 passed; all five examples clean. M49-M52 are all done.

## Known gaps: scoped and filed as issues

User: "scope out all known gaps that are for Tesserae to fix, and any
that are for tre, then submit an issue on each of them".

Each gap was re-checked against the source and `tre` 0.3.5.1 first.

- **Stale:** the `on_change` on reload gap. `tre` #12 is closed (0.3.5
  removed the cause), and Tesserae has fired `on_change` only for user
  edits since M37. It moved to "Fixed gaps", with no issue.
- **Found:** both `tre` and `tesserae` are names already taken on PyPI.
- **Tesserae:** #1-#17 (mindderivative/tesserae; the repo's first
  issues). Scrim resize (a bug), pagination ellipsis, shell panel
  removal (after tre#16), components in unknown views, a SpinBox kind,
  declarative video, declarative graph_node, extended_fab without an
  icon, per-item styling for `repeat:`, the cascade and `components:`, a
  text wrapper (low priority), routing, a state store, `tesserae new`,
  PyPI (after tre#19), wide-gamut colours, and `dark="system"` at start
  (after tre#18).
- **`tre`:** #18 (`window.get("dark")`) and #19 (PyPI, and a
  distribution name), next to #16 (undock).
- The Known gaps list now links each gap to its issue: 13 bullets, with
  the three widget-fragment gaps folded into their summary line.

## PyPI name: tesserae-ui

User: "pypi for tesserae should be named tesserae-ui".

- `tesserae-ui` was free on PyPI. It's now `pyproject.toml`'s
  `[project] name`, and a wheel builds as `tesserae_ui-0.1.0`. The import
  name stays `tesserae`, since hatchling's package path was already
  explicit (`packages = ["src/tesserae"]`).
- `.venv`'s editable install is now `tesserae-ui`; the old `tesserae`
  one was removed. 1473 passed.
- Issue #15 was updated and commented. The README, the installation page
  and the known gap name it.

## tre's PyPI name: tesserae-engine

User: "tre will be tesserae-engine which tre is working on right now".

- The name was free on PyPI. Recorded on Tesserae's side: issue #15
  (body and a comment), the README, the installation page and the known
  gap. tre #19 is left to tre's session.
- `pyproject.toml` keeps `"tre"`, with a comment, until `tesserae-engine`
  is published; switching now would break `pip install -e .` in CI.

## The release workflow

User: "already setup the github pypi env for you and the pending
publisher is up" (`tesserae-ui`, `mindderivative/tesserae`,
`release.yml`, `pypi`).

- `.github/workflows/release.yml`, run on a published GitHub Release:
  - checks the tag matches the version;
  - refuses while a dependency is the bare `tre` (PyPI's `tre` is an
    unrelated regex library);
  - builds, runs `twine check --strict`, and runs the suite and the five
    examples against the installed wheel;
  - publishes through trusted publishing in the `pypi` environment.
- Checked locally: the YAML parses, the guard blocks today's
  `pyproject.toml`, and `tesserae_ui-0.1.0` builds and passes
  `twine check --strict`.
- Issue #15 has a progress comment. What's left is the
  `tesserae-engine` dependency, then a release.

## tre 0.3.5.2: tesserae-engine on PyPI

tre's session reported v0.3.5.2, which fixes tre #16 (undock), #18
(read the OS appearance) and #19 (PyPI, as `tesserae-engine`).

- **Verified first:** the release (24 assets); `tesserae-engine` 0.3.5.2
  on PyPI (22 wheels, no sdist yet); #16, #18 and #19 closed.
- **`.venv`:** `pip uninstall tre` first, as tre warned, then
  `tesserae-engine==0.3.5.2`. `undock_panel` exists, and
  `window.get("dark")` is `True` before `run()` here.
- **`pyproject.toml`:** now depends on `tesserae-engine>=0.3.5.2`, so
  `release.yml`'s guard passes.
- **CI:** installs it from PyPI: no tre checkout build, no Rust, no
  maturin. A font-only tre checkout at v0.3.5.2 with `TRE_SOURCE_DIR`
  keeps the real-font test running, in `release.yml` too.
- **Docs:** the README and installation page install from PyPI (with the
  uninstall-`tre`-first warning), and the "starts dark" notes point at
  #17.
- **Tracker and issues:** the three known gaps waiting on tre are
  unblocked. Comments on #3, #15 and #17.

1473 passed, 1 skipped; all five examples clean.

Pushed `8eea926..bec0cba` (user: "push"). CI run 36435128346 passed,
the first to install `tesserae-engine` from PyPI: 1469 passed and 5
skipped (the five live `App.run` tests, with no display on the runner),
with the real-font test running from the font-only checkout. All five
examples ran clean.

## Tesserae 0.1.0 on PyPI

User: "push and publish". Pushed `bec0cba..76ca67f`, then published
the v0.1.0 GitHub release (pre-release; `--target main`, since GitHub
rejected a short SHA).

- `release.yml` (run 36501339807) built `tesserae_ui-0.1.0` (the wheel
  and the sdist), passed the checks and `twine check`, and ran the suite
  (1469 passed, 5 skipped) and five examples against the installed
  wheel. It uploaded after the user approved the `pypi` environment.
- **Checked:** in a fresh venv, `pip install tesserae-ui` pulls
  `tesserae-engine` 0.3.5.2, and the counter example runs.
- #15 closed. The README and installation page lead with
  `pip install tesserae-ui`. The known gap moved to "Fixed gaps".

## M53 Phases 1-2: undocking on shell reload (#3)

User: "Start the next milestone". Nothing was scoped, so I scoped M53
from the issues `tre` 0.3.5.2 unblocked (#3 and #17), with Q1-Q3 as
recommended:
- a removed panel is undocked, and its screen kept;
- macOS and Windows adopt the OS appearance on the first frame;
- a test seam keeps the start-up appearance deterministic.

Phase 2:
- `Dock.remove_panel` (via `tre`'s `undock_panel`), which also ends a
  drag of the removed panel.
- `reload_shell` undocks the panels a file edit drops; "panels removed"
  is no longer a restart.
- 5 tests; 8/8 mutants caught.

1478 passed; all five examples clean.

## M53 Phase 3: the OS's appearance at start (#17)

User: "start phase 3".

- `App(dark="system")` starts with `window.get("dark")`: at once on
  Linux, and on the first frame on macOS and Windows (queued by `run()`).
  It falls back to dark when the OS can't say.
- `_os_dark` is the test seam, and `conftest.os_appearance` makes it
  answer `None` by default, so the suite doesn't depend on the desktop.
- 10 tests, including a live `run()` in a subprocess; 7/7 mutants
  caught.

1488 passed; all five examples clean.

## M53 Phase 4: pushed and closed -- M53 complete

User: "start phase 4". Pushed `76ca67f..9ba1881`. CI run 36503537261
passed: 1483 passed and 6 skipped (the live tests, with no display),
and five examples clean. Closed #3 and #17 with summaries, and their
known gaps moved to "Fixed gaps" (12 -> 10).

## M54 Phases 1-2: an open overlay follows a window resize (#1)

User: "Start addressing all of the backlog. Begin with bugs and then
gaps that would resolve or help other gaps."

- **The backlog order:** #1 (the bug); then enablers (#8's `when:`, #9,
  #10, #5, #6, #7); then independent fixes (#4, #2, #16, #11); then the
  app-level features (#13, #12, #14).
- **The fix:** `listen_window` gives a window one shared dispatcher for
  its events. Overlays `_fit` on open and on every `resize` while open.
- 6 tests; 8/8 mutants caught (two dead branches removed after probing).

1494 passed; all five examples clean.

## M55: fragment conditionals and the text-only extended FAB (#8)

- Fragment params can have defaults. `when:` drops a child, and
  `{if:, then:, else:}` picks a value, both at expansion time and per
  item in `repeat:`.
- The `ExtendedFab*` fragments take an optional `icon`, and
  `extended_fab(icon=None)` uses the fragment's text-only shape.
- 23 tests; 13/13 mutants caught.

1517 passed; all five examples clean.

## The backlog, scoped up front as M56-M67

User: "Make sure you are updating the build tracker with the milestones
before they are started as that is the whole point of the build tracker.
If possible update the build tracker with all known milestones and
adjust the scopes as you start them."

- Every remaining backlog item is now a scoped (⬜) milestone in order,
  M56-M67. Each has its issue, the gap, a draft approach, provisional
  decisions and draft phases, and gets refined when it starts.
- The known gaps name their milestone.
- Saved as a feedback memory: milestones go in before they start.

## M56: per-item styling for repeat: (#9)

User: "push and start the milestones in order". Pushed `a4ac4c1..9092b53`
(CI run 36506034375 passed), and closed #1 and #8.

M56, refined when it started:
- Only tabs, the rail and the drawer have a selected item. `button_group`
  and `Menu` needed only a list of items.
- A fragment can forward `items` to `repeat:` with no expander change.
- Style has no absolute positioning, so the tab indicator is laid out at
  the bottom of a column the label's width.

Built: `Tabs`, `NavigationRail`, `NavigationDrawer` (and their `*Item`s
with `selected`), `Menu` and `ButtonGroup`. `MenuItem` gains optional
`height` and `padding`. 15 parity tests; 12/12 mutants caught.

1552 passed; all five examples clean.

## M57: a theme's components: for fragments (#10)

Refined at the start:
- Widgets didn't use `components:` either, beyond three special tokens.
- The shipped default theme's entries had never been applied.
- A FAB's variant is its size.

Built:
- Fragment roots are tagged with `component_of`, and the cascade applies
  the entry's corner radius and elevation (variant, then component), in
  views and widgets alike.
- The FAB fragments name `fab.{{ fab_size }}`.
- 25 tests; 12/12 mutants caught.

1579 passed; all five examples clean.

## M58: a SpinBox YAML control kind (#5)

- `SpinBox` is the ninth control kind: `value`, `min`, `max` and `step`;
  a bound value is clamped; two-way; `a11y:` goes on the input; new
  bounds rebuild it. The fragment is now this kind.
- **Found:** `SpinBox` had no `dispose()`, so a view rebuilding one
  raised. Added.
- 6 tests plus the reworked fragment test; 9/9 mutants caught.

1587 passed; all five examples clean.

## M59: a declarative video (#6)

User: "Start M59".

- An `Image` takes a `frame` binding, `(rgba, width, height)`. Each
  frame is shown and the latest kept, so it survives a re-theme or
  reconcile.
- The `video` widget shares the path. The `Video` fragment adds the
  binding only when given one.
- 5 tests; 8/8 mutants caught.

1594 passed; all five examples clean.

## M60: a declarative node graph (#7)

User: "push and start M60". Pushed `9092b53..392d8d8` (CI run
36510904115 passed), and closed #9, #10, #5 and #6.

- `NodeGraph` and `GraphNode` are YAML kinds built with the widgets,
  with `edges:` and content in a node's body.
- A reload matches nodes by id and keeps user drags unless the file
  moves the node.
- **Found:** `_props_equal` missed the keys M57, M58 and M60 added.
  Fixed.
- 12 tests; 18/18 mutants caught.

1608 passed; all five examples clean. Every MD3 widget can now be
declared.

## M61: hot reload for components in any view (#4)

User: "Push and start M61". Pushed `392d8d8..d78b5bc` (CI run 36522987253
passed), and closed #7.

- `tesserae.instantiate` registers each component with its app, in a
  `WeakSet`. The watcher finds instances in any view on the app's window.
- 4 tests; 5/5 mutants caught.

1614 passed; all five examples clean.

## M62: pagination with an ellipsis (#2)

User: "Push and start M62". Pushed M61 as `d78b5bc..234a67b` (CI run
36523682265 passed), and closed #4.

- `pagination(max_visible=7)`: over that many pages, as many slots show
  the first and last pages, the current page amid its neighbours, and an
  inert `…` for each run left out. They're redrawn as the page moves, and
  focus follows the current page. `.shown` lists each slot's page.
- 20 tests; 14/14 mutants caught.

1634 passed.

## M63: CSS wide-gamut colours (#16)

User: "push and start M63". Pushed M62 as `234a67b..f49dd36` (CI run
36524137958 passed), and closed #2.

- `tre` 0.3.5 parses no colour strings, so the reference is 0.3.4's
  `color` crate (0.3.3). `tesserae._wide_gamut` ports its parser and
  conversions in `f32`: 170,000 generated strings match a Rust harness
  on the crate byte for byte, and 711 are recorded from `tre` 0.3.4 as
  parity data.
- Out-of-gamut colours clip per channel, as `to_rgba8` did.
- 42/42 mutants caught, after rebalancing the corpus into gamut and
  adding near-black inputs where a linear segment decides a byte.
- Found: `tools/record_tre_reference.py` can't re-record
  `test_tree_parity` since M56 (a known gap now).

2358 passed.

## tre 0.4.0 (2026-09-29)

`tre`'s session reported 0.4.0. Verified: the v0.4.0 GitHub release (24
assets), and `tesserae-engine` 0.4.0 on PyPI (22 wheels and an sdist;
PyPI's project index lagged, but the version's own page listed them).

- `.venv` on 0.4.0; the floor is `tesserae-engine>=0.4.0`. CI's and
  `release.yml`'s `tre` checkout (for the real-font test) moved to v0.4.0.
- Nothing broke: 2360 passed (+2 over M63 from the docs checks on the
  guide's new YAML example), and all five examples ran clean.
- Checked 0.4.0's behaviour changes against Tesserae. `App.run` passes
  on `tre`'s new `RuntimeError` for a GPU that can't be set up.
  Tesserae makes no zero-size windows. No test matched `window.get()`'s
  old error text. Partial redraw is on by default.
- Docs: the dependency floor, 0.4.0's wheels and sdist (Rust 1.90+),
  `run()`'s headless and GPU behaviour, and partial redraw. Also, the
  themes guide's new example no longer gives text a translucent colour.

## M64: a `tesserae.widgets.text` wrapper (#11)

User: "Push and start M64-67 and Add M68 as a move to tre 0.4.0". Pushed
M63 and the move onto `tre` 0.4.0 as `f49dd36..f9f1147` (CI run
36526332657 passed on 0.4.0), and closed #16. The move is recorded as M68.

- `widgets.text(window, content, typography_role="body_medium",
  color="on_surface", width=None)`, from a new `Text` fragment.
  `.content` is a `Signal` that re-measures the text.
- Found and fixed: a re-theme put a widget's original fragment content
  back, and no widget followed a theme's `typography:`. `Widget` now
  hands its theme's type overrides to its view, as M57 did components.
- 10 tests; 11/11 mutants caught.

2372 passed.

## M65: an app-level state store (#13)

- `App(state=...)`, also settable as `app.state`: any object, typically
  a class of `Signal`s. `App.of(view)` finds the app from a view,
  component or window.
- `ViewModel.app` and `ViewModel.state` resolve through the view's
  window (M50's registry). They're non-data descriptors, so a
  ViewModel's own attribute wins. Bindings read `{{ state.x.get() }}`
  in any view.
- `examples/multi_screen/` now `load()`s both screens and shares state
  between them.
- 9 tests; 10/10 mutants caught.

2383 passed.

## M66: routing, a back stack and deep links (#12)

- `navigate(name, /, **params)`, `back()` and `forward()`, with
  `on_navigated(params)` on the screen's ViewModel before it shows.
  `can_go_back`/`can_go_forward` are Signals, set together. `show` stays
  a jump that replaces the current entry.
- Routes: `route("notes/{id:int}", "Note")`, `navigate_to("notes/42")`
  and `location`.
- The shell's rail navigates. Alt+Left/Right go back and forward, except
  in text inputs. The mouse's side buttons wait on tre#21, filed.
- Found by tests: set one at a time, the two history signals showed a
  follower a state that never existed; and a param called `name`
  collided with `navigate`'s argument (now positional-only).
- `examples/multi_screen/` navigates, goes back, and takes a deep link.
- 27 tests; 23/23 and 15/15 mutants caught.

2410 passed.

## M67: a `tesserae new` scaffolding CLI (#14)

- A `tesserae` console script (and `python -m tesserae`).
  - `tesserae new <name> [--shell] [--dir]` makes a runnable app:
    `app.py` with shared state and routes, and a Home pair. `--shell`
    adds a shell file and a Settings screen.
  - `tesserae add screen <Name>` adds a pair, and loads and routes it in
    `app.py` at two marker comments (it prints the lines without them).
    Nothing is overwritten.
- The templates ship in `tesserae/templates/` (checked in a built wheel).
- Found: a `component:` call can't take `handlers:`, so a YAML button is
  a `Rect` with a `Text` child (a known gap).
- 12 tests, each running a generated app headlessly; 21/21 mutants caught.

That finishes the backlog M54 ordered. 2422 passed.

## The `tre` 0.3.4 recorder re-records every module again (2026-09-29)

`tools/record_tre_reference.py` failed collecting `test_tree_parity`:
fragments added after M46 had no sample values (`items`, `item_width`),
and a defaulted param (M55) would have crashed the lookup.

- Required params come from `VALUES`, and `items:` per fragment.
- `tre` gets specs without the `component_of` tag (M57), and new cases
  are recorded without it.
- While recording, each corpus keeps every question it asked before
  (`reference.previous`) and adds only new ones. Keys are positions (a
  doc's nth block), so rebuilding them from edited files would have
  given old keys new questions.
- Binding expressions rooted at M65's `app`/`state` aren't asked of `tre`.

Recorded on `tre` 0.3.4 (1357 passed). Every existing answer is
identical, key by key in all eight files: +27 tree cases (8 example
views, 9 fragments, 10 inline views) and +33 binding expressions.
`Tabs` stays out: its `width: "100%"` divider is beyond 0.3.4's `View`.
The main suite on 0.4.0 has 2482 passed.

## M72: tre 0.4.1 and the mouse's side buttons (#20)

`tre`'s session reported 0.4.1, which closes tre#21. Verified: the
release (24 assets), PyPI's 0.4.1 (22 wheels and an sdist), and tre#21
closed.

- `.venv` on 0.4.1; the floor is `tesserae-engine>=0.4.1`; CI's `tre`
  checkout moved to v0.4.1. Nothing broke (2502 passed, examples clean).
- `App._history_button`: the mouse's back and forward side buttons call
  `back()`/`forward()` from a `pointer_down` listener on the window's
  root. 5/5 mutants caught.

Taken between M71's Phases 2 and 3 (M71 Phase 2 was committed first).
2503 passed.

## M71: layout vocabulary -- the rest of flexbox, and a ScrollView (#21)

User: "Scope M71 and file the tre grid issue" (tre#23), then "push and
start M71" (pushed `d1e87a1..ba04848`, CI green).

- A view's style (and a stylesheet) takes `flex_wrap`, `align_self`,
  min/max width and height, `aspect_ratio`, `position` with `x`/`y`,
  `z_index` and `clip_children`. A style sets one only when it gives it,
  and a patch resets only those it dropped (`Built.layout_keys`), so
  Python's placement of spec-built nodes survives a re-theme. `tre`'s
  layout errors name the widget.
- `kind: ScrollView`: `tre`'s `scroll_view` with one content box. A
  `Scroller` adds the keys, focus reveal, `scroll_into_view` and
  `two_way: scroll_offset`, which `tre` lacks (tre#24, filed).
- Found on the way:
  - `tre` clamps an offset only at its next layout;
  - `layout_y` is in window space and includes scrolling;
  - `scroll_view` never shrinks its one child and ignores its own padding.
- A new Layout guide page.
- 20 + 23 tests; 16/16 and 27/27 mutants caught.

M72 (tre 0.4.1, the side buttons) was taken between Phases 2 and 3.
2536 passed.

## M69: handlers on a component call (#18)

User: "push and start M69" (pushed `ba04848..80ef0e9`, CI green; #21
and #20 closed).

- A `component:` call also takes `handlers:`, `bindings:`, `two_way:`,
  `a11y:`, `interaction:` and `classes:`, put on the fragment's root.
  Mappings merge key by key (the call's win), `two_way:` replaces, and
  `classes:` adds. Their `{{ }}` stay the view's bindings. `style:` is
  still refused.
- The `tesserae new` templates use `component: ButtonFilled` and
  `ButtonFilledTonal`, each with an `a11y:` label (a fragment button has
  the role but no name of its own).
- 13 tests; 11/11 mutants caught.
- A slip, fixed: the first Phase 2 commit went in with one test failing
  (an older test pinned the refusal's wording). The chained command's
  `tail` hid pytest's exit code, so commits now check it. The fix is
  the next commit.

## M70: `disabled` on any node (#19)

User: "push and start M70" (pushed `80ef0e9..d9057c3`, CI green; #18
closed).

- `disabled:` as a node key or a binding on any node. Disabled, a node
  is announced disabled, isn't focusable, shows no state layer, ripple
  or ring, runs no handlers (the click is still taken), and fades to 38%
  of its style's opacity. A control's `disabled` is its own.
- The View applies it after every build and patch (`_sync_disabled`,
  beside the state layers and Scrollers). A planned dict of bound values
  turned out to be unobservable, since bindings are applied again after
  every patch, so it went.
- Found: `_props_equal` didn't compare `disabled`, so removing a
  control's key wouldn't have reached it.
- Docs: the interaction guide's "Disabled" section. The routing guide's
  back button is now a binding.
- 11 tests; 17/17 mutants caught.

2564 passed (+2 docs checks on the guide's new example).

## M73: tre 0.4.2 -- its scroll views, and a smaller Scroller

`tre`'s session reported 0.4.2, which closes tre#23 (CSS Grid) and tre#24
(scroll views). Verified: the release (24 assets), PyPI's 0.4.2 (22
wheels and an sdist), and both issues closed.

- `.venv` on 0.4.2; the floor is `tesserae-engine>=0.4.2`; CI's `tre`
  checkout moved to v0.4.2. The examples ran clean. One test failed,
  from 0.4.2's focus reveal: `tre` scrolled before the `Scroller` heard
  the focus, so the Scroller saw no change and the two-way binding
  wasn't told.
- Probing 0.4.2 found a real conflict: a `key_down` listener on the
  scroll view, which the `Scroller` had, keeps every key from `tre`, so
  a focused child's keys wouldn't scroll.
- The `Scroller` now only follows `tre`'s `scroll` event for
  `two_way: scroll_offset`. Its keys, reveals and clamping went.
- 24 ScrollView tests, one of them new (a focused child's keys scroll);
  7/7 mutants caught.
- M74 (grids in YAML) is scoped and waits for the user.

2565 passed.

## M74: grids in YAML (on tre 0.4.2, tre#23)

User: "push and start M74" (pushed `91ed3b2..9f05cae`, CI green).

- All 13 grid properties are in a view's style and stylesheets:
  `display`, the templates, auto tracks and flow, `grid_column`/`grid_row`,
  `row_gap`/`column_gap`, `justify_items`/`justify_self`, `align_content`.
  - They follow M71's rule: set only when given, reset when dropped. A
    dropped row or column gap goes back to the style's `gap`, since 0
    would undo it.
  - Placement goes on a Link's box and a control; a ScrollView's content
    can be a grid.
- Found by a guide example: `tre` refuses a bare number as a track list.
  The compiler passes it as a string; filed tre#27.
- A "Grids" section in the Layout guide.
- 21 tests; 14/14 mutants caught, and M71's 16/16 again.
- No known gaps remain.

2590 passed.

## M75: a node's style from a file (#22)

User: "push and start M75" (pushed `9f05cae..d315db7`, CI green).

- `style: counter_Style.yaml` reads a node's style from the file. It's
  read as an `include:` is: relative to the file that names it, kept
  inside that folder, cycle-checked, and watched for hot reload.
- A stylesheet or theme rule's `style:` can name one too.
- Naming conventions: `*_Style.yaml` is one node's style,
  `*_Stylesheet.yaml` a stylesheet, `*_Theme.yaml` a theme. Each loader
  refuses the others' suffixes; names with none still load.
- M29's generic `include:` already did most of this
  (`style: {include: ...}` worked before M75).
- The docs lint assumed a mapping `style:`; it skips a style file now.
- 16 tests; 14/14 mutants caught.

2610 passed.

## M76: one `pip install`, on every platform

User: "Scope all three and start the first", after describing the intent:
one `pip install` for a developer, and a single executable or installer for
their users (M77, M78).

- Linux already worked from a fresh venv. materialyoucolor has no Python
  3.9 wheels, and the user set the floor at **3.12**. Supported platforms
  are where every dependency has a wheel: Linux x86-64, macOS arm64 and
  Windows x64.
- A CI `clean-install` job: the wheel alone, `--only-binary=:all:`, then a
  `tesserae new` app run headlessly. It passes on 3 platforms x 3.12 and
  3.14.
- The suite on macOS and Windows found:
  - on macOS, watchers reloading files that hadn't changed (FSEvents
    reports writes from before the watch), so both watchers now compare
    stamps;
  - on Windows, a source read without an encoding, now UTF-8 with a lint
    to keep it so, and a test's backslash labels.

  Now 2613 passed on each, 0 skipped on macOS and Windows.
- 0.2.0 prepared: the version, a changelog, and the README's install
  section. Publishing is the user's step.
- Released: GitHub pre-release v0.2.0 (user: "push and release"). The
  user approved the `pypi` deployment, and Tesserae 0.2.0 is on PyPI.
  Checked from PyPI itself: a fresh venv, `pip install tesserae-ui` alone
  (wheels only) installed all six dependencies, and a `tesserae new` app
  ran. M76 complete.

## M77: `tesserae build`, an app as one executable

User: "push and start M77". Phase 1 settled the decisions (see the tracker).

- Phase 2: `tesserae build [app.py] [--name] [--icon] [--console]
  [--include] [--exclude] [--check]`, in `tesserae/build.py`. It scans the
  app's folder (skipping `.git`, venvs, `build`, `dist`, caches and hidden
  files), bundles every file at its relative place, analyses the app's
  `.py` files for imports, and calls PyInstaller `--onefile`. `App.run`
  now takes `TESSERAE_MAX_FRAMES` and turns hot reload off in a frozen
  app. A `tesserae new --shell` app builds into one 41 MB Linux
  executable in 13 s, and `--check` runs it for 30 frames from an empty
  folder. The mutation check caught 14/15; the survivor was a redundant
  glob form, now removed. 2622 passed.
- Phase 3 (user: "push and start phase 3"): a `build-executable` CI job
  builds a `tesserae new --shell` app from the wheel on Linux, macOS and
  Windows and runs `--check`. With no display `App.run` returns at once,
  so `--check` now needs frames drawn: `TESSERAE_FRAMES_REPORT` makes a
  run write how many. Linux runs under Xvfb and needed
  `libxkbcommon-x11`, which winit loads for an X11 window. All three
  drew 30 frames and exited cleanly.
- Phase 4 (user: "push and start phase 4"): the "Releasing Your App"
  guide. Its numbers were measured, not assumed: start-up 0.55 s built
  against 0.23 s from source (Linux), and sizes of 41/25/30 MB (Linux,
  macOS, Windows, from CI). That the unpacked folder is where `__file__`
  points came from the CI log. The macOS listing showed PyInstaller also
  makes a `.app` beside the executable, so the guide says so. The README
  had "Install" twice; they're now merged, with a "Release an app"
  section. The changelog gains an "Unreleased" section (M77, M79). M77
  complete.

## M79: `tre` 0.4.3

`tre`'s session reported v0.4.3 during M77. I checked the release (24
assets), PyPI (22 wheels and an sdist) and that `tre` #27 is closed before
acting on it.

- Moved `.venv`, the floor (`>=0.4.3`) and CI's and `release.yml`'s `tre`
  checkout. The suite passed unchanged (2624), and all five examples ran.
- Dropped M74's bare-number track conversion, since `tre` now does it
  itself.
- New tests for 0.4.3's scroll changes: a far offset is held at the end,
  and `two_way` writes back the end; shortcut keys don't scroll, but Shift
  does; a nested vertical `ScrollView` keeps the wheel even when its
  content fits. The last one is what `tre` documents (a wheel passes only
  views that don't scroll in its direction), unlike a browser's scroll
  chaining, so it's reported to `tre`'s session as a possible feature,
  not a bug. 2630 passed.

## M78: installers for each platform

User: "push and start M78". The user then chose Inno Setup for Windows and
documented signing, and asked for five Linux formats: "Can we do a
flatpak, appimage, .deb, .rpm, and an arch pacman type?" So the draft's
three phases became six.

- Phase 1, research (2026-09-29, primary sources):
  - GitHub runner images
    (github.com/actions/runner-images: Windows2025, macos-26-arm64 and
    Ubuntu2404 readmes): Inno Setup 6.7.1 and WiX 3.14 on Windows, no
    NSIS; `dpkg` and `rpm` on Ubuntu, no `appimagetool` or FUSE.
  - Inno Setup licence: jrsoftware.org/files/is/license.txt. Free for any
    use; its authors ask for-profits to buy a licence, voluntarily.
  - WiX 6+ maintenance fee (github.com/wixtoolset/wix OSMFEULA.txt):
    organisations with $10k+ a year in revenue.
  - AppImage: docs.appimage.org and AppImage/appimagetool.
  - `.deb` format: deb(5).
  - PyInstaller: the 6.13 changelog says onefile with a `.app` will be
    blocked in 7.0 (a new known gap for M77's macOS default); its docs
    say it ad-hoc signs its output.
  - Apple's notarization docs, and Sequoia removing Control-click, Open
    (developer.apple.com/news/?id=saqachfa). The M77 guide said
    Control-click, so I fixed it.
- The one-folder probe: 0.27 s to start against 0.55 s for one file and
  0.23 s from source; 107 MB uncompressed.
- Decisions Q1-Q5 are in the tracker.
- Phase 2: `tesserae build --installer`, from a one-folder build.
  - App details come from options. A PNG icon is converted to `.ico` or
    `.icns` with Pillow, which writes both, on Linux too.
  - macOS: the `.app`'s `Info.plist` is stamped, re-signed ad hoc and put
    in a `.dmg` with `hdiutil`. On a real Mac in CI the signature
    verified, and the installed app drew 30 frames.
  - The single file on macOS no longer adds `--windowed`. That closes the
    known gap, and it broke one test that assumed `--windowed`
    everywhere; that test is now pinned to Linux.
  - 16/16 mutants caught.
- Phase 3, Windows: Inno Setup, found (`TESSERAE_ISCC`, the PATH, the
  usual installs, or Tesserae's cache) or fetched.
  - The fetch is 7.1.0's x64 setup from jrsoftware/issrc. It's checked
    against the digest GitHub publishes for the release asset,
    `sha256:0362a383…`, and unpacked with `/PORTABLE=1`, which Inno
    Setup's own `setup.iss` documents and which installs nothing.
  - The script is a per-user install (`PrivilegesRequired=lowest`) with a
    Start-menu entry, an optional desktop entry and an uninstaller. Its
    AppId comes from the identifier. It's written as UTF-8 with a BOM.
  - 20/20 mutants caught after one more test: the first run missed that
    nothing checked Windows was registered for `--installer`.
- Phase 3 verified in CI (run 36685061823): the installer built with the
  runner's Inno Setup 6.7 installed silently, got its Start-menu entry,
  ran (30 frames) and uninstalled cleanly. A second build used the Inno
  Setup 7.1.0 that Tesserae fetched. Three CI-side fixes on the way:
  PowerShell couldn't run Git Bash's `/d/a/...` venv path; it took the
  fetch notice as part of the ISCC path; and a test expected `/` in
  Windows paths. Phase 3 done.

## M80: `tre` 0.4.4

`tre`'s session reported v0.4.4 during M78 Phase 4. It adds scroll
chaining, for the wheel and keys, as Tesserae suggested after 0.4.3.
Verified first: the release has 24 assets, and PyPI has 22 wheels and an
sdist. CI had already installed it through the `>=0.4.3` floor, and M79's
pinned test failed there, as the pin was meant to.

- Moved `.venv`, the floor (`>=0.4.4`) and CI's and `release.yml`'s `tre`
  checkout. Exactly the one expected failure. That test is flipped (the
  page now takes the wheel the inner view can't use), and a key test is
  added (Page Down chains too, and `two_way` hears it). The docs say so.
  All five examples ran; 2659 passed.
- Phase 4, Linux: an AppImage, a `.deb` and a pacman package.
  - Tesserae writes the `.deb` and the pacman package itself. The
    AppImage uses the pinned `appimagetool` and runtime.
  - Three CI runs to green. First, the single file `dist/demo` clashed
    with the app folder, which is now `dist/<name>-<version>`. Second, on
    Arch the installed app found "no display": winit couldn't load
    `libXcursor` or `libXi`. I reproduced it in a local podman container,
    declared every X11 library `tre` loads (from the names in its
    engine), and pacman then pulled them in. Third, a Windows test run
    showed the program's executable bit must be set by the packager.
  - Final run 36749555627: all three installed and ran for 30 frames.
- Reviewed `tre` 0.5.0's custom-windowing design (`tre` #28) for `tre`'s
  session, against Tesserae's code:
  - Q1's "interactive" rule must stop at the drag region, above which
    Tesserae's root listener for the mouse's back/forward buttons sits,
    and ignore hover and tooltip listeners.
  - The Windows menu needs an opt-out, and macOS needs an event when its
    inset changes.
  - Also asked for: a pointer cancel after a native drag, fullscreen, a
    window icon, and a minimum size.

## The build tracker is archived; the GitHub project takes over

User: "Finish out this build tracker and then archive it, start using the
GitHub project instead."

- The tracker's final state:
  - a dated archive note at the top;
  - "Just closed" and "Up next" pointing to the GitHub project;
  - M78 (Phase 4 of 6 done), M81 and M82 each naming the issue they
    continue in (#26, #24, #29).
- It's archived as `BUILD_TRACKER_ARCHIVE_0.2.md`, the complete record of
  M1-M82. References to it are updated; the docs' "project status"
  sections point to the project.
- Tracking continues in the GitHub project Tesserae UI Framework
  (users/mindderivative/projects/2): releases are milestones with umbrella
  issues (#23 for 0.2.1, #24 for 0.3.0). This LOG continues as the repo's
  running narrative.

## M78 Phases 5-6, #39, and M78 complete

Tracked in the GitHub project (#35, #36, #39, #26).

- Phase 5 (`beb73a7`): an `.rpm` (with `rpmbuild`) and a Flatpak (with
  `flatpak-builder`, on Freedesktop 26.08), each made when its tool is
  installed and reported when it isn't.
  - The `.rpm` passed locally in a Fedora 44 container.
  - Both passed in CI. The Flatpak runs a build from Ubuntu 24.04
    (glibc 2.39).
- Phase 6 (`2ae7cd0`): the guide's install/uninstall table for all seven
  installers, and signing with the developer's own certificates.
- #39, a macOS hot-reload race CI found (the test job failed on reload
  tests that hadn't changed):
  - A save can arrive as one event while the file is empty. The watchers
    now let a change settle (`ab4b2da`).
  - A save can also land while the file is read. They now read it again
    (`d2537b6`).
  - Seven tests fake the events on any platform.
- CI run 36767330299 is green on all three platforms. M78 is complete; the
  0.2.1 release (#29) is next. 2676 passed.

## Tesserae 0.2.1 released

User: "push and release", then "approved, check PyPI".

- `a7d7c1a`: version 0.2.1 and the changelog section headed. CI (run
  36772575520) was green on it before tagging.
- GitHub pre-release `v0.2.1` on that commit. `release.yml` run
  36773310140: build passed (the tag matches the version). The user
  approved the `pypi` deployment, and publish succeeded.
- Checked from PyPI in a fresh Python 3.14 venv, wheels only:
  `pip install "tesserae-ui[build]==0.2.1"` brought `tesserae-engine`
  0.4.4 and PyInstaller 6.22.3. A `tesserae new --shell` app built into
  one executable (30 frames), and `--installer` made the AppImage, `.deb`,
  pacman package and `.rpm` (30 frames), with the Flatpak skipped and its
  install hint shown (no `flatpak-builder` here).
- On GitHub: #37, #29 and the 0.2.1 umbrella #23 are closed, and so is the
  repository's `0.2.1` milestone (14 issues). Next is 0.3.0 (#24), which
  starts when the user says so.

## 0.3.0: custom windowing (#24)

User: "commit CLAUDE.md, push and start 0.3.0", then "approved" for each
milestone. Built on the `0.3.0` branch, on `tre` 0.5.0, tracked in the
GitHub project.

- M1 (#30), the design (`docs/design/custom-windowing.md`): nine
  questions, decided as recommended; Q9, a window border, is the user's
  addition ("yes, add the border to M4").
- M2 (#40), the window on `App`: the options, the actions, `maximized`
  and `active`, `pointer_cancel` clearing every pressed state.
- M3 (#41), title bars in YAML: `window_region`, the `window.*` handlers,
  `kind: TitleBar`, its theme (the user asked whether it follows light and
  dark, and whether its height can change: it does, and it can), macOS's
  inset.
- M4 (#42), the shell and scaffolding: the shell's top bar as the title
  bar, the window border, `tesserae new --custom-title-bar`,
  `examples/custom_title_bar`, hot reload (it needed no code).
- M5 (#43), docs and checks: the Custom Title Bars guide; CI builds a
  custom-title-bar app on every platform; a hand check on Linux, X11 (the
  user has no other machine).
  - It found the example's hand-built bar overlapping the text above it
    (#62; a Text wider than its box wraps when drawn but lays out one line
    tall), and a panic on any real click in a text field (#63): `tre`
    0.4.4 and 0.5.0 held a `Ref` through a `borrow_mut`. `tre` fixed it in
    0.5.0.1 (`tre` #51), the user re-checked, and the floor is
    `tesserae-engine>=0.5.0.1,<0.6`.
  - Not checked by hand: Wayland, Windows, macOS. The changelog says so.
- M6 (#44), the release: the version and docs (#64), `0.3.0` fast-forwarded
  into `main` (#65), and the GitHub pre-release `v0.3.0` (#66).
  - CI on `main` failed twice on Windows in a live hot-reload test: four
    tests rewrote their files every 20 ms, so the #39 settle logic never
    settled. They save once and retry after half a second now (`045d2a5`);
    CI is green on `main` and `0.3.0`.
  - `release.yml` run 36821967058: the build passed, the user approved the
    `pypi` deployment, and the upload to `tesserae-ui` succeeded.
  - Checked from PyPI in a fresh Python 3.14 venv, wheels only:
    `pip install "tesserae-ui[build]==0.3.0"` brought `tesserae-engine`
    0.5.0.1 (its requirement is `>=0.5.0.1,<0.6`) and PyInstaller 6.22.3.
    A `tesserae new notes --shell --custom-title-bar` app ran (30 frames)
    and built into one executable (`--check`: 30 frames, exited cleanly);
    `--custom-title-bar` without `--shell` is a one-line error. pip's
    index took a few minutes to list 0.3.0 after PyPI's own page did.
  - 0.3.0 was hand-checked on Linux, under X11, only.

## Tesserae 0.3.1 released (#72)

User: a Getting Started walk-through for a fresh Linux install, declarative
and imperative; then "release 0.3.1", and "approved, check PyPI".

- The walk-through (#68-#71): `examples/getting_started/` (eight step
  programs the page includes as they are) and `tests/test_getting_started.py`.
  Running it for real found what writing it hadn't: a YAML `Text` needs a
  `font_family`, `text_align` wasn't a YAML key, and `App.run()` refused an
  empty window, which is the first step of an app built in Python.
- 0.3.1 (#73-#77): `App.run()` needs no screen, `text_align` in a YAML
  `text:` block, a closest-match hint on a misspelt name, and
  `run(keepalive=)`.
- The user's own trial found the last two. A typo in `foreground` got no
  hint. Then an edit to a view didn't reload even after dragging, resizing
  and clicking the window: `tre`'s idle window starved other Python
  threads (reproduced in pure `tre`; its run loop wasn't detached from the
  GIL), so the watcher couldn't hand the reload over. `keepalive`, on by
  default with `hot_reload`, ticks the window (0.5% of a core). A first
  version also ticked runs bounded by `max_frames` and slowed five live
  tests from 1 s to 41 s each; found from the suite's run time.
- `tre` fixed it (its #92), the user sent the report, and `tre` 0.5.1
  shipped it. Checked here on both Wayland and X11, and Tesserae passed
  against 0.5.1 (no `padding` or paint use of the kinds that changed).
- Release: CI on `0.3.1` first failed on macOS (my test assumed a border
  there) and once on Fedora's registry (503), both fixed or re-run; `main`
  fast-forwarded to `c862078`; pre-release `v0.3.1`; the user approved the
  `pypi` deployment (run 36946332567).
- Checked from PyPI in a fresh venv: `pip install "tesserae-ui[build]==0.3.1"`
  brought `tesserae-engine` **0.5.1** (the requirement is `>=0.5.0.1,<0.6`).
  The eight walk-through programs ran (10 frames each), the hint and
  `text_align` work, `tesserae new --shell --custom-title-bar` built and
  drew 30 frames with `--check`, and the idle-window script runs with no
  keepalive on the released engine. PyPI's unversioned JSON lagged the
  simple index by several minutes.
- Next: with `tre` 0.5.1 out, the keepalive default can go off and the
  floor rise to 0.5.1 (a 0.3.2, the user's call).

## Tesserae 0.3.3 released (#80, #81, #82)

User: the three findings in Documents/Issues.md, then "approved, do #80 and
#82 as 0.3.3, but all shell elements should have `style:`", "approved, push
and release it, promote 0.3.2" and "approved, check PyPI".

- #80: a shell's top bar and status bar shrank in a short window (`tre`'s
  default `flex_shrink` is 1). They are `flex_shrink=0` at the widget, so
  code, shell files and reload swaps are all covered. The navigation rail
  never shrank (I had said it did, from one item; the user corrected me).
- #81: `style:` on every part of a shell (the shell, `top_bar`, `navigation`,
  `status_bar`, `content`, each zone as `{size, style}`), in a file and in
  code. Hot reload applies a changed style and restores the shell's own
  values when one is removed. A top bar's icon buttons fit a `height` under
  48. The shell schema knows them.
- #82: theme roles (and `kind: TitleBar`) work with no `theme_seed`, from the
  baseline palette, with a did-you-mean hint on a misspelt role.
- Released: 2971 tests passed, strict docs clean, CI green on `0.3.3` and
  `main`. `v0.3.3` is a pre-release on GitHub; `v0.3.2` was promoted to
  Latest. PyPI had `tesserae-ui` 0.3.3 after a retry (the index lags), and
  a fresh venv installs it with `tesserae-engine` 0.5.1.

## Tesserae 0.3.2 released (#78, #79)

User: "approved, do all of #78 and push it with 0.3.1 release", then "sorry
0.3.2 release" (0.3.1 was already on PyPI, and PyPI never lets a version be
replaced, so it is 0.3.2), then #79 added to it, and "approved, check PyPI".

- #78: `tre` 0.5.1 is the floor (`tesserae-engine>=0.5.1,<0.6`; CI and the
  release workflow check out `tre` v0.5.1) and `run(keepalive=)` is off by
  default, now that `tre` lets other Python threads run in an idle window.
  `main`'s CI had gone red on macOS and Windows the day `tre` published
  0.5.1: the two tests that held an idle window with no keepalive were
  written to fail once `tre` was fixed, and CI installs the newest allowed
  engine. They are gone; `test_keepalive_idle.py` checks that a thread and
  a hot-reload edit reach an idle window by default, and fails on 0.5.0.1.
- #79, the user's issue: YAML schemas for Red Hat's YAML language server.
  Four draft-07 files (a view, a shell, a component fragment, a theme or
  stylesheet), written by `tools/generate_yaml_schema.py` from Tesserae's own
  code and from `tre`'s error messages (which list the valid layout values).
  They ship in the wheel, are served at
  `https://mindderivative.github.io/tesserae/schema/`, and `tesserae schema
  [--settings]` finds them and prints the setting. Checked with a generic
  validator (every YAML file in the repository, and 15 mistakes rejected)
  and with Red Hat's real `yaml-language-server` 1.24.0, driven over the
  Language Server Protocol (`tools/check_schema_in_language_server.py`): all
  97 files open clean, completions and diagnostics as intended. Both ways
  of checking found things the other couldn't: the fragment format's
  `params` defaults, `repeat` parameters and `{if, then, else}` values (22
  of 77 fragments failed at first), and `kind:` completing only `TitleBar`.
  Not run inside VS Code itself, only the server it uses.
- The first release run failed and published nothing: the release
  workflow's "Test the built wheel" installs the wheel and `pytest`, not the
  dev extras, so the new tests couldn't import `jsonschema`. It installs
  `jsonschema` now, and the pre-release and its tag were recreated on the
  fixed commit (run 36956069222).
- `tre` asked, through its own session, for a check of its 0.5.1 build and
  then of its fix for the idle-window problem (`tre` #92). Both were built
  into a scratch folder (never into `tre`'s tree) and reported: nothing in
  Tesserae relied on `padding` or paint properties being ignored.
- Checked from PyPI in a fresh Python 3.14 venv: `tesserae-ui[build]==0.3.2`
  brought `tesserae-engine` 0.5.1 (requirement `>=0.5.1,<0.6`); the four
  schemas are in the install and byte-identical to the docs site's; a
  scaffolded app's YAML validates against the installed schemas; `run()`'s
  `keepalive` defaults to `False`; the user's hot-reload scenario (a root's
  `width` from `auto` to `100%` and back, on an idle window, no keepalive)
  applied both edits; the eight Getting Started programs ran; and
  `tesserae new --shell --custom-title-bar` built and `--check` drew 30
  frames. The simple index lagged by a few minutes.

