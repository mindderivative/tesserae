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
| M12 — Widget Catalog, Overlays (thin delegates) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M13 — Widget Catalog, Search & Progress/Status (thin delegates + 1 naming translation) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M14 — Widget Catalog, Media/Graphics & Date/Time (thin delegates + `icon`'s naming translation) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M15 — Part 3 Phase 1: Component Macro-Expansion Engine | `██████████` 100% | ✅ Complete (2026-09-23) |
| M16 — Part 3 Phase 2: Wire `App.load()`/`instantiate()` to Macro-Expansion | `██████████` 100% | ✅ Complete (2026-09-23) |

**Just closed:** M16 — `App.load()` and `tesserae.instantiate()` both now apply `component:` macro-expansion by default (built on `tre`'s own new M73, `instantiate(..., source=...)`, which closed the one real blocker M15 had named). A real, honest limitation surfaced by this milestone's own tests, not fixed here: `App` has no theme API at all, so an MD3-token-using `component:` fragment can't actually render through `App.load()` without one yet.

**Previously:** M15 — the real start of Part 3: `component: Name` / `with: {...}` in a `*_View.yaml` now expands to a real `*_Component.yaml` fragment's own `WidgetSpec` subtree before `tre` ever parses the file, modeled on pyCopper's real `source:`/`with:`/`params:` precedent (`pyCopper/src/pycopper/spec/include.py`, read directly). Real findings that reshaped the design: `tre` already has a working, unparameterized `include:` splice (`engine-spec/src/include.rs`) that this pass deliberately leaves untouched; `tre`'s declarative layer resolves MD3 color roles/shape tokens for real (verified with a live `theme_seed` call) so fragments need no Python-side color math; the declarative cascade never consults a theme's per-component `components:` override (only the imperative catalog does) — a real, named gap, not silently promised as covered. A real, load-bearing bug found while testing (not assumed): PyYAML's `safe_dump` quotes numeric-looking strings, which would have broken every numeric param — fixed by preserving a param's real type on a whole-value placeholder match. One real fragment shipped (`Button_Component.yaml`, "filled" variant, faithful to `resolve_button_colors`), proven identical to `tesserae.widgets.button(...)`'s own `corner_radius` via a real cross-check test.

**Up next:** the other 37 component fragments (a separate, mostly-mechanical milestone). Real, additive follow-up decision to make: give `App`/`App.load()` its own theme API (`theme_seed`/`custom_theme`/`dark`) — currently `App` has none at all, a real, pre-existing gap that surfaced directly while testing this milestone's own `component: Button` wiring (an MD3-token-using fragment can't actually render through `App.load()` today without one).

**Known gaps:**
- 37 of 38 widget categories have no declarative `*_Component.yaml` fragment yet (only `Button`) — real, deferred, mechanical follow-up work.
- `App`/`App.load()` has no theme-related API at all (`theme_seed`/`custom_theme`/`dark`/`stylesheet`) — a real, pre-existing gap, not introduced by this milestone, but newly relevant now that `component:` fragments can reference MD3 color roles/shape tokens through `App.load()`.
- The declarative cascade doesn't consult a theme's per-component `components:` override (imperative-only) — an app wanting that level of per-component customization uses `tesserae.widgets` instead of a declarative fragment.
- No dedicated `tesserae.widgets.text` wrapper for the raw `add_text` primitive — every widget needing text uses its own clear param instead; revisit only if a real caller needs the bare primitive.
- No routing beyond a plain named `App.show(name)` (no history/back-stack, no URL-style deep links); no app-level state store shared across screens; no `tesserae new` CLI scaffolding tool. All real, named, un-scoped future candidates — see `README.md`'s own "Explicitly deferred" section.
- Not published to PyPI (`tre` itself isn't fully published either yet — both depend on a local editable checkout for now).

**Fixed gaps:**
- ~~`App.load()`/`tesserae.instantiate()` don't use `load_view`/macro-expansion yet — a real app must call `tesserae.spec.load_view(...)` directly today.~~ **Fixed (M16).** `App.load()` now constructs via `load_view` directly; `tesserae.instantiate()` now expands `path` and hands off via `source=`.
- ~~`tesserae.instantiate()` (embedded components) can't use `component:` at all — blocked on a `tre`-side `Component.instantiate(source=...)` addition.~~ **Fixed.** `tre`'s own M73 (`instantiate(..., source=...)`) closed the blocker; M16 wired `tesserae.instantiate()` to use it.
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

---

## Milestone 12 — Widget Catalog, Part 2e: Overlays

**Status: ✅ Complete (2026-09-23).** `dialog`/`snackbar`/`side_sheet`/`menu`/`menu_item`/`tooltip` — `tre`'s own "Overlays" category (dialogs, menus, snackbars, side sheet). Real scope decision: deliberately does **not** wrap `Window.open_*`/`close_*` (e.g. `open_dialog`/`close_dialog`) — those are already plain, minimal `Window` methods with no naming ambiguity or construction-time logic to delegate around, so a `tesserae.widgets` wrapper would only add indirection, not clarity. `menu` delegates to `tre`'s own `build_menu` factory name (there is no `add_menu`). None of these 6 expose an ambiguous color kwarg, so M8's naming translation wasn't needed here.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/overlays.py` — all 6, verified directly against `window_factory.rs` (including `add_snackbar`'s `(container, action|None, close|None)` return shape) — ✅
- Step 2: `src/tesserae/widgets/__init__.py` extended to re-export all 6 — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_overlays.py` — 7 real pytest tests: parity on `corner_radius`, `add_snackbar`'s real `None`-shape for an omitted `action_label`/`closable` reproduced through the delegate, and `build_menu`'s real `ValueError` on an empty item list reproduced through `menu(...)` — ✅
- Step 2: full suite — 63 passed (56 prior + 7 new), 0 regressions — ✅

---

## Milestone 13 — Widget Catalog, Part 2f: Search & Progress/Status

**Status: ✅ Complete (2026-09-23).** `search_bar`/`search_view` (Search) and `circular_progress`/`linear_progress`/`loading_indicator` (Progress & Status) — the last 2 categories from the original Part 2 scope's category list in `tre`'s own docs (`circular_progress`/`linear_progress`/`loading_indicator` are real `NodeKind` primitives, wrapped for the same uniform-surface reason M9 wrapped `checkbox`/`slider`/etc.).

Second real, concrete naming translation: `add_loading_indicator`'s `color: Option<(u8,u8,u8,u8)>` is a genuine RGBA tint for the spinner's own glyph (no background of its own; falls back to the theme's primary when omitted) — verified directly against `window_factory.rs`, the same "glyph/tint, not a fill" concept M8 named `foreground`. Tesserae's own `loading_indicator(foreground=...)` translates internally to `add_loading_indicator(color=...)`.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/search.py` — `search_bar`/`search_view`, verified directly against `window_factory.rs` (including `add_search_bar`'s real 4-tuple return) — ✅
- Step 2: `src/tesserae/widgets/progress.py` — `circular_progress`/`linear_progress`/`loading_indicator`, with the `foreground=`→`color=` translation on the third — ✅
- Step 3: `src/tesserae/widgets/__init__.py` extended to re-export all 5 — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_search.py` — 3 real pytest tests, including proving the returned `TextField` node from `search_bar(...)` is genuinely wireable via `set_on_change` — ✅
- Step 2: `tests/test_widgets_progress.py` — 4 real pytest tests: parity on `.get("value")` for both progress bars, and a real check that the translated `loading_indicator(foreground=...)` call reaches `tre` without raising, matching the native `color=` call (no gettable color property exists to assert stronger parity — the same real limitation every other color kwarg in this catalog has) — ✅
- Step 3: full suite — 70 passed (63 prior + 7 new), 0 regressions — ✅

---

## Milestone 14 — Widget Catalog, Part 2g: Media/Graphics & Date/Time — Part 2 Complete

**Status: ✅ Complete (2026-09-23).** `image`/`video`/`icon`/`graph_node`/`node_graph` (Media & Graphics) and `date_picker_day`/`time_picker_dial`/`period_selector` (Date & Time Pickers) — the last 2 categories, completing the full widget catalog (14 real widget-catalog milestones, every category in `tre`'s own `docs/guide/components.md` now covered).

The real, final application of M8's naming-consistency finding: `add_icon`'s own `color: (u8,u8,u8,u8)` is the glyph's own paint — an icon has no background at all (confirmed directly in `window_factory.rs`, matching the docs' own "No `background` param, same reasoning as `Image`" note). `icon(foreground=...)` translates internally to `add_icon(name, color, size, ...)`. `image`/`video` take no color param at all — their content *is* their own pixels. `graph_node`/`node_graph`/the 3 Date & Time widgets only take the already-clear `border_color`.

Real, deliberate scope note: no dedicated `tesserae.widgets.text` wrapper for the bare `add_text` primitive was built — every widget in the catalog that displays text does so through its own already-clear, purpose-named param (`label`, `headline`, `content`, `text`), never a raw passthrough to `add_text`'s own ambiguous `background=` (glyph color). If a real caller needs the bare primitive later, that's the one remaining place the `background`→`foreground` translation would land.

### Phase 1 — Thin Delegating Wrappers ✅
- Step 1: `src/tesserae/widgets/media.py` — all 5, `icon`'s naming translation applied — ✅
- Step 2: `src/tesserae/widgets/date_time.py` — all 3 (named to avoid shadowing the stdlib `datetime` module) — ✅
- Step 3: `src/tesserae/widgets/__init__.py` extended to re-export all 8 — ✅
- Step 4: `tests/fixtures/pixel.png` — a real, minimal valid 1×1 PNG (hand-built via `zlib`, no external dependency) checked in for `image(...)`'s own real file-loading test coverage — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_widgets_media.py` — 6 real pytest tests: real file-loading parity via the checked-in PNG fixture, `add_image`'s real `OSError` on a missing path reproduced through the delegate, the `foreground=`→`color=` translation, and `add_icon`'s real `ValueError` on an unknown icon name reproduced through the delegate — ✅
- Step 2: `tests/test_widgets_date_time.py` — 5 real pytest tests, including `add_period_selector`'s real `ValueError` on an invalid `selected` value reproduced through the delegate — ✅
- Step 3: full suite — 81 passed (70 prior + 11 new), 0 regressions — ✅

**Part 2 of the approved plan is now complete.** All widget-catalog categories are real, tested, faithful delegates to `tre`'s own native factories, with 3 real, concrete naming translations applied where `tre`'s own vocabulary was genuinely ambiguous (`add_toolbar`'s `color`→`tone`, `add_loading_indicator`'s `color`→`foreground`, `add_icon`'s `color`→`foreground`).

---

## Milestone 15 — Part 3, Phase 1: Component Macro-Expansion Engine

**Status: ✅ Complete (2026-09-23).** The real start of Part 3 — letting a `*_View.yaml` author write `component: Button` / `with: {label: ..., ...}` directly, with no knowledge that `Button` is a Rect+Text composition underneath. Modeled on pyCopper's own real, proven `source:`/`with:`/`params:` design (`pyCopper/src/pycopper/spec/include.py`, read in full before designing anything), adapted to `tre`'s real `WidgetSpec` schema.

Real investigation that reshaped the design before any code was written:
1. `tre` already has a real, working `include:` splice mechanism (`crates/engine-spec/src/include.rs`) — path-confined, cycle-detected, depth-limited, operating on the raw YAML tree before validation. It has **no parameterization at all**. This milestone's engine deliberately leaves a literal `include:` key completely untouched — `tre`'s own mechanism resolves it later — and only adds the missing capability, parameterized reuse.
2. `tre`'s declarative layer genuinely resolves MD3 color roles (`background: primary`) and shape/elevation tokens (`corner_radius: small`), confirmed with a live `tre.View(path=, source=, theme_seed=(0x67,0x50,0xA4,0xFF))` call — no Python-side color computation needed in a fragment.
3. Real, honest gap, confirmed by grepping `build.rs`/`cascade.rs` for `components`: the declarative cascade never consults a theme's per-component `components:` override — only the imperative catalog's `window.theme.shape("button", variant)` does. Named directly, not silently dropped.
4. `WidgetSpec`'s real schema (`id`/`kind`/`classes`/`style`/`text`/`checked`/`value`/`image`/`bindings`/`handlers`/`two_way`/`children`, `#[serde(deny_unknown_fields)]`) has no `anchor:`-style cross-reference field — only `id:` needs namespacing when a fragment is used twice, simpler than pyCopper's own `name:`+`anchor:` pair.
5. `Component.instantiate` (the embedded-component path `tesserae.instantiate()` uses) has no `source=` override at all — confirmed directly, it calls `std::fs::read_to_string(path)` with no way to inject pre-expanded text (`crates/engine-py/src/component.rs:119`). `component:` expansion can reach a top-level screen (`App.load()` constructs a `View` directly) but not an embedded component yet — a real, named, deferred gap requiring a small `tre`-side widening.

### Phase 1 — The Engine ✅
- Step 1: `src/tesserae/spec/expand.py` — `expand_components`/`ComponentError`. A real, load-bearing bug found while testing, not assumed: PyYAML's `safe_dump` quotes a numeric-looking Python `str`, which would turn `width: "{{ width }}"` into `width: '120'` after substitution — a quoted string `tre`'s own `serde_yaml_ng` parser rejects for an `f32` field. Fixed by preserving the supplied value's real Python type when a string is *exactly* one placeholder (`_WHOLE_PARAM_RE`), falling back to plain string interpolation only for an embedded placeholder — the same rule that lets `with: {label: "{{ some_signal.get() }}"}` forward a live `tre` binding expression through untouched, verified directly — ✅
- Step 2: `src/tesserae/spec/load.py` — `load_view(path, *, component_dirs=None, **view_kwargs) -> tre.View`, the real integration point (a plain function, not a `tre.View` subclass — `View` is a native `pyo3` class, and a function returning the genuine object works just as well) — ✅
- Step 3: `src/tesserae/spec/components/Button_Component.yaml` — one real, faithful "filled"-variant fragment (container=`primary`, label=`on_primary`, matching `resolve_button_colors` exactly), with its own real, stated limitation: `corner_radius` is a required param, not derived from `height`, since `{{ }}` substitution has no arithmetic and `engine_md3::shape::named` has no "full/pill" token to reach for instead — ✅
- Step 4: `pyproject.toml` — added a real `pyyaml>=6.0` dependency (previously only present transitively via `mkdocs`, never declared) — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_spec_expand.py` — 13 real pytest tests: every guard named above (missing/unknown param, missing call-site `id:`, unknown component, a real cycle via a `tmp_path` fixture directory, id-namespacing across two uses of one component, a `{{ }}` binding surviving untouched, numeric-type round-tripping), plus the real cross-check that matters most — constructing the same button both ways (`component: Button` through `load_view`/`View(source=...)`, and `tesserae.widgets.button(...)` directly) and asserting identical `corner_radius` — ✅
- Step 2: `tests/test_spec_load.py` — 3 real pytest tests against an actual file on disk (not just an in-memory YAML string), including a true no-op-passthrough proof for a view with zero `component:` usage — ✅
- Step 3: full suite — 97 passed (81 prior + 16 new), 0 regressions — ✅

**Deliberately not in this milestone (named, not silently dropped):** the other 37 component fragments; wiring `App.load()`/`tesserae.instantiate()` to use `load_view` by default; a `poll_reload`-integrated re-expansion helper; embedded-component `component:` support (blocked on the `tre`-side `Component.instantiate(source=...)` gap named above); the declarative-vs-imperative `components:` theme-override gap.

---

## Milestone 16 — Part 3, Phase 2: Wire `App.load()`/`tesserae.instantiate()` to Macro-Expansion

**Status: ✅ Complete (2026-09-23).** User-directed: "Start 3, then move to 2 and then 1" — item 3 (the `tre`-side `instantiate(..., source=...)` widening, `tre`'s own M73) landed first on `tre`'s `0.3.1` branch, closing the one real blocker M15 had named. This milestone is item 2: wiring Tesserae's own two real construction paths — `App.load()` (top-level screens) and `tesserae.instantiate()` (embedded components) — to apply `component:` macro-expansion by default, so an app author never needs to call `tesserae.spec.load_view`/`expand_components` directly.

Real, honest limitation surfaced while testing, not fixed here: `App`/`App.load()` has no theme-related API at all (`theme_seed`/`custom_theme`/`dark`/`stylesheet` never existed on `App`, a real, pre-existing gap unrelated to this change). This means a `component:` fragment referencing an MD3 color role (like `Button_Component.yaml`'s own `background: primary`) can't actually *render* through `App.load()` yet without a theme -- proven directly in this milestone's own tests (see below), not glossed over.

### Phase 1 — `tre`-side: `instantiate(..., source=...)` ✅
- Step 1: done on `tre`'s own `0.3.1` branch, commit `b963331` (`tre`'s own M73) -- `instantiate_component` (`crates/engine-py/src/component.rs`) widened with `source: Option<String>`, mirroring `View::new`'s own M71 pattern; both `View.instantiate` and `Component.instantiate` (the nested-component call site) widened to forward it — ✅
- Step 2: reinstalled into `tesserae/.venv` via `maturin develop --release`, confirmed live with a direct interactive check before proceeding — ✅

### Phase 2 — Tesserae-side: Wire `App.load()`/`instantiate()` ✅
- Step 1: `src/tesserae/app.py` — `App.load()` now constructs via `tesserae.spec.load_view(view_path)` instead of `tre.View(str(view_path))` directly; real, deliberate scope limit stated in its own docstring: no `theme_seed`/`custom_theme`/`stylesheet`/`dark` forwarding yet (`App.load()` never accepted any of those before this change either, so this is additive, not a narrowing) — ✅
- Step 2: `src/tesserae/component.py` — `instantiate()` now reads `path`'s real content, calls `expand_components()`, and hands off via `parent.instantiate(str(path), into, source=expanded)` -- reachable for real, nested components too, since `Component.instantiate` (not just `View.instantiate`) got the identical `source=` widening — ✅

### Phase 3 — Verification ✅
- Step 1: `tests/test_app.py` (`tesserae`) -- 2 new pytest tests: a real no-op regression proof, and a real *distinguishing* proof that macro-expansion genuinely runs -- before this wiring, a `component:`-using view fails with `tre`'s own schema error (`component` is not a real `WidgetSpec` field, `deny_unknown_fields`); after, it fails later, at MD3 color resolution (no theme given), proving `component:`/`with:` were genuinely replaced before `tre` ever parsed the file — ✅
- Step 2: `tests/test_component.py` (`tesserae`) -- 2 new pytest tests, the identical real distinguishing-proof pattern applied to `tesserae.instantiate()` (an embedded component, not a top-level view) — ✅
- Step 3: full suite -- 101 passed (97 prior + 4 new: 2 in `test_app.py`, 2 in `test_component.py`), 0 regressions — ✅
- Step 4: all 3 real examples (`counter`/`multi_screen`/`todo_list`) re-run end to end -- genuinely warranted this time (unlike the additive widget-catalog milestones), since this change touches the core construction path every example goes through, not an independent new module; all exited cleanly with correct real output (`Count: 3` after 3 clicks, final screen `Settings`, final todo items list) — ✅

**Real, honest limitation, named directly (not fixed here):** `App`/`App.load()` still has no theme API of its own -- a `component:` fragment using an MD3 color role can't render through `App.load()` without one. A real, additive follow-up candidate once a real app needs it.
