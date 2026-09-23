# Build Tracker

Updated after every milestone/phase/stage/step completion, kept in sync with `ARCHITECTURE.md`. Status legend: ✅ done · 🚧 in progress · ⬜ not started.

**Milestones 1-6 are seeded, written after the fact (2026-09-23):** this file didn't exist when Tesserae's first 6 commits landed (2026-09-19 through 2026-09-21) -- their real history is reconstructed honestly from those commits' own messages and the code as it exists today, not presented as if this tracker had been running from day one.

---

## Top Metrics

| Milestone | Progress | Status |
|---|---|---|
| M1 — Initial App + Counter Vertical Slice | `██████████` 100% | ✅ Complete (2026-09-19) |
| M2 — `App.load()` Naming Enforcement + Multi-Screen Example | `██████████` 100% | ✅ Complete (2026-09-20) |
| M3 — Real Component Embedding: `instantiate()` + Todo List Example | `██████████` 100% | ✅ Complete (2026-09-20) |
| M4 — `Repeater`: Automatic Keyed List Diffing | `██████████` 100% | ✅ Complete (2026-09-21) |
| M5 — Reactivity Re-exports: `Computed`/`Effect`/`batch`/`untrack` | `██████████` 100% | ✅ Complete (2026-09-21) |
| M6 — Sync with `tre` v0.3.0's `flex_direction` Rename | `██████████` 100% | ✅ Complete (2026-09-23) |
| M7 — Bootstrap Documentation Infrastructure (this file, MkDocs, `PLAN.md`/`LOG.md`) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M8 — Widget Catalog, Buttons & Actions (thin delegates) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M9 — Widget Catalog, Selection & Input (thin delegates) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M10 — Widget Catalog, Cards/Lists/Chips/Structural Rows (thin delegates) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M11 — Widget Catalog, Navigation & Shell (thin delegates + 1 naming translation) | `██████████` 100% | ✅ Complete (2026-09-23) |

**Just closed:** M11 — `tesserae.widgets` Navigation & Shell Composition category (`tabs`/`navigation_rail`/`navigation_drawer`/`toolbar`/`top_app_bar`/`status_bar`), plus the first real application of M8's naming-translation decision: `add_toolbar`'s own `color=` kwarg isn't an RGBA color at all — it's a named container-tone selector (`"standard"`/`"vibrant"`, confirmed at `window_factory.rs:6727-6734`). Tesserae's `toolbar(tone=...)` translates to it internally, since calling a two-value named selector `color` is its own kind of confusing (a caller would reasonably expect an RGBA tuple, matching every other `color`/`background` kwarg in the catalog).

**Up next:** the remaining 2 widget categories in the original Part 2 scope (Overlays, Search) plus Date & Time and Media & Graphics. The Text/Icon primitives (`add_text`/`add_icon`) remain where M8's `background`-as-glyph-color translation actually applies, if/when they get their own `tesserae.widgets` wrapper — not yet decided which milestone that is. Then Part 3 — the YAML component macro-expansion layer — the real "ease of use to a GUI designer" deliverable.

**Known gaps:**
- The remaining 4 widget categories are still real, deferred work — being scoped now (see "Up next").
- Part 3 (YAML component macro-expansion) not started.
- No routing beyond a plain named `App.show(name)` (no history/back-stack, no URL-style deep links); no app-level state store shared across screens; no `tesserae new` CLI scaffolding tool. All real, named, un-scoped future candidates — see `README.md`'s own "Explicitly deferred" section.
- Not published to PyPI (`tre` itself isn't fully published either yet — both depend on a local editable checkout for now).

**Fixed gaps:**
- M7's own tracker entry wasn't flipped to ✅ before its commit (`686214a`) landed — Phase 2/3 checkboxes and the Top Metrics row both still read `⬜`/`🚧` despite the real MkDocs site, `docs.yml`, and `PLAN.md`/`LOG.md` all existing on disk. Caught and corrected while starting M8; all three deliverables verified present before flipping the status.

---

## Milestone 1 — Initial App + Counter Vertical Slice

**Status: ✅ Complete (2026-09-19).** The real starting point: `App`, the single entry point owning a named `(View, ViewModel)` registry and one live `tre.Window`, per the user's own explicit design requirement ("app.py should be the entry point for the app... this allows for switching of current views without needing to bootstrap each view/viewModel"). `App.show(name)` opens the real `Window` via `tre.Window.from_view` the first time, then switches it via `tre.Window.show_view` on every call after — neither a `View` nor its `ViewModel` is ever re-parsed or re-bootstrapped by a later `show()`. `Signal`/`View`/`ViewModel` are thin, unmodified re-exports of `tre`'s own real MVVM primitives, not duplicated.

### Phase 1 — `App` + Real Vertical Slice ✅
- Step 1: `App.__init__`/`register`/`show`/`run`, backed directly by `tre.Window.from_view`/`show_view` (`src/tesserae/app.py`) — ✅
- Step 2: `examples/counter/` — a real `Counter_View.yaml` + `Counter_ViewModel.py` pair, a real dispatched click incrementing a `Signal`-bound label, through a genuine render loop — ✅
- Step 3: 5 real pytest tests for `App` itself — ✅

### Phase 2 — CI Hardening ✅
- Step 1: real CI wired up (`.github/workflows/ci.yml`), checking out both `tesserae` and the sibling `tre` repo, installing `tre` editable, running `pytest`/the counter example — ✅
- Step 2: dropped the unmaintained `actions-rs/toolchain@v1` (GitHub-flagged deprecated, forced onto an old Node.js runtime) once the first real CI run surfaced the warning — `ubuntu-latest` already ships a working stable Rust toolchain, the same real finding `tre`'s own `ci.yml` already relies on — ✅

---

## Milestone 2 — `App.load()` Naming Enforcement + Multi-Screen Example

**Status: ✅ Complete (2026-09-20).** `App.load(view_path, viewmodel_cls, name=None)` — the real, runtime-enforced counterpart to the `*_View.yaml`/`*_ViewModel.py` naming convention this repo documented from its first commit but never actually checked, mirroring pyCopper's own validated design. Raises immediately on a missing suffix or a mismatched prefix, rather than failing later with an unrelated error once a handler name doesn't resolve.

### Phase 1 — Naming Enforcement ✅
- Step 1: `check_naming_convention` (`src/tesserae/naming.py`), checked via `inspect.getfile` against the `ViewModel` class's own defining file — `tre.View` has no `path` getter of its own (confirmed by reading `view.rs` before designing this), so `load()` takes the path directly — ✅
- Step 2: `App.load` wired to call it, returning the constructed `(view, viewmodel)` pair — ✅

### Phase 2 — Multi-Screen Example ✅
- Step 1: `examples/multi_screen/` — two independent screens (`Home`/`Settings`), each its own `*_View.yaml`/`*_ViewModel.py` pair, switched via `App.show()` from inside each screen's own real dispatched `on_click` handler — proving a switch works even when triggered *reentrantly*, from the handler `App.show` itself is dispatching into (the same real scenario `tre`'s own M42 Phase 2 had to fix a real borrow-panic bug for) — ✅
- Step 2: `examples/counter/` updated to use `App.load()`, dogfooding the new check — ✅
- Step 3: 5 new pytest tests for `load()`; CI runs both examples — ✅

---

## Milestone 3 — Real Component Embedding: `instantiate()` + Todo List Example

**Status: ✅ Complete (2026-09-20).** `tesserae.instantiate(parent, path, viewmodel_cls, into, *args, **kwargs)` — the enforced-naming counterpart to `tre`'s own real `View.instantiate`/`Component.instantiate` (`tre`'s M43): embeds another view's own YAML as a real, independent `Component` with its own `ViewModel`, forwarding extra constructor args for the real common case (an item's own data, or a callback letting it notify its parent on removal).

### Phase 1 — `instantiate()` ✅
- Step 1: `src/tesserae/component.py` — checks the naming convention, then calls `parent.instantiate(path, into)` (real `tre` M43 capability) and constructs `viewmodel_cls(component, *args, **kwargs)` — ✅
- Step 2: naming-convention checking factored out of `App.load` into the shared `tesserae.naming.check_naming_convention` — two real call sites justified sharing it — ✅

### Phase 2 — Todo List Example ✅
- Step 1: `examples/todo_list/` — a real dynamic list, each item its own `Component` + `ViewModel`, added via a real dispatched "Add" click and removed via its own "Remove" click, plus a real two-way-bound checkbox toggle — proves the full multi-instance lifecycle end to end through a genuine render loop — ✅
- Step 2: 4 new pytest tests for `instantiate()`; CI runs all three examples — ✅

---

## Milestone 4 — `Repeater`: Automatic Keyed List Diffing

**Status: ✅ Complete (2026-09-21).** `Repeater(parent, items_signal, path, viewmodel_cls, into, key=identity, args=lambda item: (item,))` — the declarative-*feeling* layer on top of M3's `instantiate`/`Component.remove()`: watches one list `Signal` as the single source of truth and keeps exactly one `Component` + `ViewModel` alive per item currently present, diffing by key. Built entirely in Python on top of M3's already-shipped capability — zero new `engine-spec`/`engine-core` work needed.

### Phase 1 — `Repeater` ✅
- Step 1: `src/tesserae/repeater.py` — subscribes to `items_signal`, diffs the new list's own keys against the previously-rendered set on every change: new keys call `instantiate`, keys no longer present call `component.remove()` — ✅
- Step 2: real, stated scope boundary, not silently glossed over — no reordering an already-present key (`engine_core::Tree` has no child-reorder primitive at all, confirmed by reading its source; `tre`'s own `Reconciler` carries the identical real limitation), and no re-application of a changed item's own *data* to an already-alive instance (that's the item's own `ViewModel`'s job) — ✅
- Step 3: a YAML-level `for_each:` keyword was considered and set aside — it would need a genuinely new per-item binding-resolution scoping layer in `engine-spec` (today every binding resolves against exactly one `ViewModel`-shaped object), a much bigger, riskier feature than reusing what M3 already tested — ✅ (real, deliberate, documented decision)

### Phase 2 — Todo List Rewrite + Tests ✅
- Step 1: `examples/todo_list/` rewritten onto `Repeater` — `TodoViewModel.items` is now the single source of truth (a plain list of stable ids); `TodoItemViewModel.remove_self` mutates the shared `items` `Signal` directly instead of calling `Component.remove()` via a private callback — the real single-source-of-truth pattern a repeater is for — ✅
- Step 2: 8 new pytest tests — ✅

---

## Milestone 5 — Reactivity Re-exports: `Computed`/`Effect`/`batch`/`untrack`

**Status: ✅ Complete (2026-09-21).** `tre`'s richer reactivity layer (`tre`'s own M45) is real — re-exported unmodified from `tesserae`, the same shape `Signal`/`View`/`ViewModel`/`Component` already use.

### Phase 1 — Re-export ✅
- Step 1: `Computed`/`Effect`/`batch`/`untrack` added to `src/tesserae/__init__.py`'s real, public surface — ✅
- Step 2: `README.md`/`ARCHITECTURE.md`'s own "Explicitly deferred" lists updated — had also gone stale on the live-bindable-properties item, closed separately by `tre`'s own M44 with no `tesserae`-side change needed — ✅

---

## Milestone 6 — Sync with `tre` v0.3.0's `flex_direction` Rename

**Status: ✅ Complete (2026-09-23).** `tre` v0.3.0 renamed the declarative `style.flex_direction` values from `Row`/`Column` to `Horizontal`/`Vertical` — a deliberate, hard rename (the old values no longer parse), since "row"/"column" collide with the different, established meaning those words carry in spreadsheet/datasheet tools. Tesserae's own `.venv` was still on `tre` 0.2.0, and every example/test YAML in this repo used the old values — a real, concrete demonstration of exactly the "pull a new tre release and have to retest everything" problem the user's own new `tre`-side `0.3.1` release-branch workflow (accumulate multiple changes per release) exists to reduce going forward.

### Phase 1 — Update and Fix ✅
- Step 1: `tre` reinstalled editable into `tesserae/.venv` at its current `main` (v0.3.0) — ✅
- Step 2: all 7 affected files updated (`examples/counter/Counter_View.yaml`, `examples/multi_screen/Home_View.yaml`, `examples/multi_screen/Settings_View.yaml`, `examples/todo_list/Todo_View.yaml`, `examples/todo_list/TodoItem_View.yaml`, `tests/test_component.py`, `tests/test_repeater.py`) — ✅
- Step 2: verification — ✅ (22/22 pytest passing, up from 12 real failures against the stale install; all 3 real examples — `counter`/`multi_screen`/`todo_list` — run clean end to end.)

---

## Milestone 7 — Bootstrap Documentation Infrastructure

**Status: ✅ Complete (2026-09-23).** User-directed, as part of shifting real development focus to Tesserae: "Tesserae as a new project and git/github repo should have its own documentation to include build tracker and MkDocs, along with everything else. If it is Tesserae scoped it goes in the Tesserae project." Mirrors `tre`'s own real, established documentation shape rather than a lighter-weight substitute — this file, a real MkDocs site, and `PLAN.md`/`LOG.md`, so the real widget-catalog/macro-expansion work (Milestones 8+) has a real place to be tracked from the beginning.

### Phase 1 — `BUILD_TRACKER.md` ✅
- Step 1: this file, seeded with Milestones 1-6 as real, honest, after-the-fact history reconstructed from the 6 real commits already shipped — ✅
- Step 2: `tools/generate_tracker_artifact.py` copied verbatim from `tre` (the script's own header states it's project-agnostic, meant to be copied into any repo with a `BUILD_TRACKER.md` at its root) — ✅

### Phase 2 — MkDocs Site ✅
- Step 1: `docs/`/`mkdocs.yml`, the same real structure `tre/docs/` established (Overview/Installation/Getting Started/Guide/API Reference/Architecture), scoped to what Tesserae itself provides — ✅
- Step 2: a `docs.yml` GitHub Actions workflow mirroring `tre/.github/workflows/docs.yml` — ✅

### Phase 3 — `PLAN.md`/`LOG.md` ✅
- Step 1: adopted in this repo too, overwritten per phase, matching `tre`'s own already-corrected convention (no per-step archiving; `BUILD_TRACKER.md` is the durable record) — ✅

---

## Milestone 8 — Widget Catalog, Part 2a: Buttons & Actions

**Status: ✅ Complete (2026-09-23).** Real, direct user correction mid-milestone reshaped this and every widget category still to come: the original plan called for from-scratch Python reimplementations of all 38 composition-only widgets' MD3 color/shape/elevation resolution. Before writing the first one, a real, load-bearing realization: `window.add_button()` and its 37 siblings already work perfectly from Python *today* — a from-scratch port would duplicate real, working Rust logic for zero fidelity gain, and for `add_button_group`/`add_split_button` specifically, could *never* reach parity at all (their hover/press shape-tightening and reflow animations live entirely in `PaintProperties` fields with no public Python setter). Presented to the user via `AskUserQuestion`; user's own reply reframed the goal directly: "It's not about accessing the widgets it's about ease of use to a GUI designer" — meaning the real deliverable is Part 3 (declarative `kind: Button` usable in a `*_View.yaml`, impossible today), and `tesserae.widgets` should be thin, faithful delegates to `tre`'s own native factories, not parallel reimplementations.

Same message also surfaced a second, real, cross-cutting finding: if the imperative and declarative surfaces expose confusing or inconsistent naming, "ease of use to a GUI designer" isn't served just by delegating — the *names* matter too. Confirmed concretely: `engine-spec`'s declarative `style.background` doubles as a `Text` node's own glyph color (`build.rs:547-564` — not an actual background fill), and `add_icon`/`add_badge` separately call the same underlying concept `color=`. Decision: Tesserae's own API translates to clear, consistent names at each point a widget exposes a color kwarg — `background` only ever means a real background fill, `foreground` names glyph/text color — rather than inheriting `tre`'s organically-evolved internal vocabulary wholesale. Applied starting with the next widget category (Text/Icon-family), since none of this milestone's 6 button-family widgets expose a raw background/color kwarg to begin with.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/buttons.py` — `button`/`icon_button`/`fab`/`extended_fab`/`split_button`/`button_group`, each `window` as first positional arg (matching `tesserae.component.instantiate`'s own convention), same parameter names/order/defaults as `tre`'s own `add_*` factories (verified directly against `crates/engine-py/src/window_factory.rs`'s real `#[pyo3(signature = ...)]` declarations, not assumed), delegating with zero added logic — ✅
- Step 2: `src/tesserae/widgets/__init__.py` — re-exports all 6 as `tesserae.widgets.*` — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_buttons.py` — 9 real pytest tests, each constructing the same widget two ways (via `tesserae.widgets` and via the native `window.add_*` call with identical args) and asserting `Node.get("corner_radius")`/`.get("elevation")`/`.get("border_width")` match exactly (`Node.get()` has no `"background"` property at all — confirmed directly from `node.rs`, colors are deliberately excluded), plus real kwarg-forwarding checks (`variant=`, `size=`) proving the delegate doesn't silently drop an argument — ✅

---

## Milestone 9 — Widget Catalog, Part 2b: Selection & Input

**Status: ✅ Complete (2026-09-23).** `checkbox`/`slider`/`radio_button`/`switch`/`spin_box`. Real finding before writing these: `checkbox`/`slider`/`radio_button`/`switch` are actual `NodeKind` primitives in `tre` (not compositions) — confirmed against the approved plan's own list of the 21 real primitive kinds — already fully usable from Python with zero blockers. Wrapped anyway, matching M8's "accessed as if created by tesserae" goal: a GUI designer using `tesserae.widgets` shouldn't need to know or care which underlying widgets are primitives vs. compositions in `tre`. `spin_box` is a real composition (a text field flanked by minus/plus icon buttons).

None of these 5 expose an ambiguous color kwarg — `background` already means "this widget's own fill" everywhere it appears (`checkbox`/`slider` take it directly; `radio_button`/`switch` are auto-themed with no color override at all) — so no naming translation was needed. Auditing composition-only Card/Chip/Badge/ListItem factories while investigating where the translation *should* land turned up a correction to M8's own note (see Top Metrics "Up next" above): none of those four expose a raw color kwarg either, only `add_text`/`add_icon`'s own primitive signatures do.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/selection.py` — `checkbox`/`slider`/`radio_button`/`switch`/`spin_box`, same parameter names/order/defaults as `tre`'s own factories (verified directly against `window_factory.rs`) — ✅
- Step 2: `src/tesserae/widgets/__init__.py` extended to re-export all 5 — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_selection.py` — 6 real pytest tests, parity asserted on each widget's own real gettable state (`get_checked()`/`.get("thumb_position")`/`.get("select_progress")`/`.get("toggle_progress")`/`.get("corner_radius")`) — ✅
- Step 2: full suite — 37 passed (31 prior + 6 new), 0 regressions — ✅

---

## Milestone 10 — Widget Catalog, Part 2c: Cards, Lists, Chips & Structural Rows

**Status: ✅ Complete (2026-09-23).** `card`/`list_`/`list_item`/`chip`/`badge`/`divider`/`link`/`accordion_header`/`tree_node` — the 9 real factories in `tre`'s own "Cards, Lists, Chips & Structural Rows" category. Confirms M9's own correction directly: checked every one of these 9 signatures against `window_factory.rs` before writing the wrappers, and none expose a raw color kwarg beyond the already-clear `border_color` (`add_list`/`add_link` take no color at all) — the `background`-as-glyph-color naming issue really is confined to the primitive `add_text`/`add_icon` factories, not this category.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/structural.py` — all 9, same parameter names/order/defaults as `tre`'s own factories (verified directly against `window_factory.rs`, including the two-element return tuples `add_accordion_header`/`add_tree_node` produce) — ✅
- Step 2: `src/tesserae/widgets/__init__.py` extended to re-export all 9 (`list_`/`badge` etc. named to avoid shadowing Python builtins) — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_structural.py` — 12 real pytest tests: parity on `elevation`/`corner_radius`/`border_width`, a real kwarg-forwarding check (`card`'s `elevated` vs. `outlined` variant resolves to different elevation *and* border width), `add_list`'s real `ValueError` on an empty item list reproduced through the delegate, and `add_tree_node`'s `leaf=True` correctly producing `chevron=None` — ✅
- Step 2: full suite — 49 passed (37 prior + 12 new), 0 regressions — ✅

---

## Milestone 11 — Widget Catalog, Part 2d: Navigation & Shell Composition

**Status: ✅ Complete (2026-09-23).** `tabs`/`navigation_rail`/`navigation_drawer`/`toolbar`/`top_app_bar`/`status_bar` — the 6 real factories in `tre`'s own "Navigation & Shell Composition" category.

Real, concrete first application of M8's naming-translation decision: `add_toolbar`'s own `color: Option<&str>` param isn't an RGBA color at all — verified directly at `window_factory.rs:6727-6734`, it accepts exactly two named strings (`"standard"`/`"vibrant"`), a container-tone selector, not a literal paint value. Calling it `color` is its own real source of confusion (every other `color`/`background` kwarg across the whole catalog takes an RGBA tuple) — Tesserae's own `toolbar(...)` renames it `tone=`, translating internally when it delegates to `window.add_toolbar(color=tone, ...)`.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/navigation.py` — all 6, verified directly against `window_factory.rs` (including `add_tabs`/`add_navigation_rail`'s list-of-`Node` returns and `add_navigation_drawer`/`add_top_app_bar`'s tuple returns) — ✅
- Step 2: `src/tesserae/widgets/__init__.py` extended to re-export all 6 — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_navigation.py` — 7 real pytest tests: parity on `corner_radius`, a dedicated check that `toolbar(tone="vibrant")` reaches the identical resolution as the native `add_toolbar(color="vibrant")` call (proving the translation is real, not just cosmetic), and a real kwarg-forwarding check (`variant="docked"` vs. `"floating"` resolves to different corner radius *and* elevation) — ✅
- Step 2: full suite — 56 passed (49 prior + 7 new), 0 regressions — ✅
