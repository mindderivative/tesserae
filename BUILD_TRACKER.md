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
| M17 — Part 3 Phase 3: Button Component Fragments (all 5 MD3 variants) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M18 — Part 3 Phase 4: `icon_button`/`fab`/`extended_fab` Component Fragments | `██████████` 100% | ✅ Complete (2026-09-23) |
| M19 — Part 3 Phase 5: `split_button` Fragments — Buttons & Actions Complete | `██████████` 100% | ✅ Complete (2026-09-23) |
| M20 — Part 3 Phase 6: Selection & Input Component Fragments | `██████████` 100% | ✅ Complete (2026-09-23) |
| M21 — Part 3 Phase 7: Cards/Lists/Chips/Structural Rows Component Fragments | `██████████` 100% | ✅ Complete (2026-09-23) |
| M22 — Part 3 Phase 8: Navigation & Shell Component Fragments (Fixed-Shape Members) | `██████████` 100% | ✅ Complete (2026-09-23) |
| M23 — Part 3 Phase 9: Overlays Component Fragments | `██████████` 100% | ✅ Complete (2026-09-23) |
| M24 — Part 3 Phase 10: Search, Progress & Status, Media & Graphics, Date & Time Component Fragments | `██████████` 100% | ✅ Complete (2026-09-23) |
| M25 — Scoping the Next Boundary + `NodeGraph` Component Fragment | `██████████` 100% | ✅ Complete (2026-09-24) |
| M26 — Detailed Scoping: `tre`-Side Primitive Additions & Macro-Layer Loop Construct | `██████████` 100% | ✅ Complete (2026-09-24) |
| M27 — `RadioButton`/`Switch`/`CircularProgress`/`LinearProgress`/`LoadingIndicator`/`TimePickerDial`/`Link` Component Fragments | `██████████` 100% | ✅ Complete (2026-09-24) |
| M28 — Macro-Layer `repeat:` Construct, Staged Against `ListItem` First | `██████████` 100% | ✅ Complete (2026-09-24) |
| M29 — Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only | `██████████` 100% | ✅ Complete (2026-09-25) |
| M30 — Theme Arguments on `App` and `App.load()` | `██████░░░░` 67% | 🚧 In progress — Phase 2 of 3 done (2026-09-25) |
| M31 — Hot Reload for Theme and Stylesheet Files | `░░░░░░░░░░` 0% | ⬜ Not started — waiting on the tre 0.3.3 migration |

**Just closed:** M30 Phase 2 (2026-09-25) — `App(...)` now takes an app-wide theme (`theme_seed`/`dark`/`default_theme`/`custom_theme`) and a default stylesheet, `App.load(..., stylesheet=)` overrides the stylesheet per screen, and the new `App.build_view()` themes screens given to `register()`; theme files are read once, by Tesserae. Phase 1 (same day): the user chose that API, and deferred theme-file hot reload to a new M31 until `tre` issue #8 is fixed. Before that, M29 — Tesserae owns all file handling and gives `tre` no file path anywhere: views go over as one finished dict (with `include:` resolved in Tesserae), images as RGBA pixels (Pillow), themes/stylesheets as `*_spec=` dicts and fonts as bytes (`tre` M86), and `app.run(hot_reload=True)` reloads a running app from `watchfiles` events via `tre` M87's `App.thread_handle()` (requested as `tre` issue #6). Six user-approved phases, each checked against `tre`'s real source first and mutation-checked; 157 → 221 tests.

User direction, relayed from the `tre` session: "Tesserae should not be pushing files directly to tre. It should be pushing spec information and handling the files itself." Phase 6 (hot reload inside `App.run()`) was added last and is called "Phase 3b" in commits. In detail:

- **Views** go to `tre` as one finished dict (`View(spec=...)`, `instantiate("", into, spec=...)`, `reconcile(spec=...)`), with `include:` resolved in Tesserae (a port of `tre`'s rules; an included file can now use `component:`) and `tre`'s errors re-raised naming the source file.
- **Images** are decoded with Pillow and handed over as RGBA (`push_frame`, `add_image_from_bytes`).
- **Themes, stylesheets, fonts** are read by Tesserae and handed over as `*_spec=` dicts and `register_font` bytes (`tre` M86), with a `FontFallbackWarning` where `tre` would silently substitute a font.
- **Hot reload** is Tesserae's: `app.run(hot_reload=True)` watches every file a screen is built from with `watchfiles` on a background thread and applies changes through `tre` M87's `App.thread_handle()` — requested as [`tre` issue #6](https://github.com/mindderivative/tre/issues/6), now closed.
- Tesserae now gives `tre` **no file path anywhere**. 157 → 221 tests.

Real findings along the way, each recorded in its phase: dropping `path` in Phase 1 would have broken images and `poll_reload` (so it moved to Phase 3); unquoted YAML dates break `spec=` (normalized); `tre`'s single-threaded views and lack of a loop hook (→ `tre` issue #6 → M87); GitHub's runner has no display, so live `App.run()` tests skip there; and the docs pass caught Tesserae's own `multi_screen` example still handing `tre` file paths.

**Previously:** M15-M28 — the macro-expansion engine, its wiring, all 9 MD3 widget categories (67 fragments), the M25/M26 scoping of the last real fronts, M27's 7 primitive fragments, and M28's `repeat:`. See their own entries below.

**Up next:** M30 Phase 3 — the committed tests for the new `App` theme API, a final MkDocs re-check, moving the closed `App` theme gap to "Fixed gaps", and PLAN.md/LOG.md; waiting on the user's go-ahead. Then M31 (hot reload for theme and stylesheet files): [`tre` issue #8](https://github.com/mindderivative/tre/issues/8) is now fixed in `tre` M91, but only in the unreleased 0.3.3, so M31 waits on a Tesserae 0.3.3 migration milestone (not yet scoped). Other named, un-scoped candidates: hot reload for `App.register()`ed screens, and conditional per-item styling for the 5 Rust-internal-state-dependent-coloring widgets (`tabs`/`button_group`/`navigation_rail`/`navigation_drawer`/`menu`).

**2026-09-24 sync check:** `tre` v0.3.1 is now a real, tagged, released version (`github.com/mindderivative/tre/releases/tag/v0.3.1`) -- Tesserae's own `App` was on hold until this happened, per the user's own earlier call. Re-verified against it directly: 135/135 `pytest` passing, all 3 examples (`counter`/`multi_screen`/`todo_list`) run clean end to end, zero changes needed this time (unlike M6's own real 7-file fix) -- the editable install (`Editable project location: /home/phil/rustDev/projects/tre`) tracks `tre`'s own source tree live, with no reinstall step required. `tre` issues #2 and #3 (both referenced below) are now genuinely closed on GitHub, not just code-complete -- their own real fixes had shipped weeks of `tre`-side milestones ago but the issues themselves were never closed until now.

**Known gaps:**
- 67 of ~68 real MD3 widgets now have a declarative `*_Component.yaml` fragment; `video`/`node_graph`/`graph_node` are the only real remaining structural blockers (see below), plus `extended_fab`'s own deliberately deferred gap.
- `video` still has no full, faithful declarative fragment -- [`tre` issue #2](https://github.com/mindderivative/tre/issues/2) (M25's own real blocker) is now closed (`tre` v0.3.1 made `ImageSpec.src` optional, so `kind: Image` with no `src:` produces the exact synthetic blank placeholder `add_video` already builds), narrowing this to a real, smaller remaining gap: a fragment can now declare the placeholder, but real video content still needs the app to fetch the resulting `Node` and call `push_frame` imperatively afterward -- no way for a one-shot static fragment expansion to wire that up on its own.
- `graph_node` is structurally unfragmentable — needs a live node reference as its own attachment parent, which the macro layer's textual expansion cannot express (M25, reclassified from "no `NodeKindSpec`" — the real blocker is different).
- `extended_fab`'s icon-less structural shape has no fragment yet (real, deliberately deferred — see M18).
- `repeat:` (M28) is real but deliberately narrow: `tabs`/`navigation_rail`/`navigation_drawer`/`button_group`/`menu` still can't be expressed with full fidelity, since their own imperative construction computes real state-dependent active/inactive coloring in Rust that a static `{{ }}`-substitution template can't branch on -- a second, separate, un-scoped capability (conditional per-item styling) is the real remaining gap for these 5, not the repeat mechanism itself (`list_`/`ListItem` has no such gap and is fully covered). `repeat:` is also deliberately not reactive -- its own items are fixed at macro-expansion time; an app wanting runtime-changing content still uses the existing imperative `tesserae.Repeater`.
- `App`/`App.load()` has no theme-related API at all (`theme_seed`/`custom_theme`/`dark`/`stylesheet`) — a real, pre-existing gap, newly relevant now that `component:` fragments can reference MD3 color roles/shape tokens through `App.load()`. `load_view` itself takes them all since M29 Phase 4, reading theme/stylesheet files in Tesserae; a themed screen can use `load_view(...)` + `App.register(...)` meanwhile. **Being fixed in M30** (API decided 2026-09-25: app-wide theme on `App(...)`, per-screen stylesheet on `load()` with an app-wide default).
- **Upcoming `tre` 0.3.3 breaks Tesserae's YAML.** `tre`'s M90 (commit `a5bed0a` on its unreleased `0.3.3` branch, seen 2026-09-25) renames the declarative schema: enum values become lowercase snake_case (`flex_direction`, `fit`, `align_items`, `justify_content`), a new `style.foreground` sets Text/Link/Icon/LoadingIndicator glyph color (inline `style.background` on those becomes an error), `Switch`/`RadioButton` take `selected:` instead of `checked:`, and `text.role` becomes `text.typography_role`. 37 of the 67 fragments use `role:` alone; the other renames reach most fragments, examples and test views. Nothing breaks while CI pins `v0.3.2`; moving to 0.3.3 needs a migration milestone. **For that milestone** (per the `tre` session, 2026-09-25; M90 now complete on `tre`'s `0.3.3` branch — `a5bed0a`, `49c55b3`, `fa2a02a` — not yet pushed or released): the full old → new table is in `tre`'s `docs/migrating-0.3.3.md`. YAML is mostly automatic: `tools/migrate_views_0_3_3.py` rewrites views and stylesheets in place, keeping comments and including YAML in `.py` strings, with `--check` to preview. Python calls are manual, and `tesserae.widgets` mirrors `tre`'s `add_*` parameters, so it needs them: glyph color becomes `foreground=` on `add_text`/`add_icon`/`add_loading_indicator` (Tesserae's `icon`/`loading_indicator` translate `foreground=` to `color=` today), `add_toolbar(vibrant=bool)` (Tesserae's `toolbar(tone=)` translates to `color=` today), `add_switch(selected=)` with `Node.set_selected`/`get_selected`, `orientation=` on `add_divider`/`add_scroll_view`, `add_link(content=)`, `supporting_text=` on `add_dialog`/`add_popover`, and the `"thumb_position"` → `"value"` and `animate("background")` → `"foreground"` property names tests use. **Watch for a silent layout change:** stylesheet and theme rules setting `margin`, `flex_grow`, `flex_shrink`, `flex_basis`, `align_items` or `justify_content` now apply (the pre-M90 cascade dropped them), so a screen relying on them can lay out differently with no error. Old names fail loudly otherwise: a `TypeError` for a removed keyword, a `ValueError` naming the new field or listing the lowercase enum values.
- Hot reload (M29) can revert live data on screen: when an edit touches a node that has a `{{ }}` binding, `tre`'s `reconcile(spec=...)` re-applies that node's static values but not its binding, so it shows the YAML's placeholder text until the bound `Signal` next changes (reproduced 2026-09-25 against `tre` v0.3.2: editing a bound label's `style.width` turns `'bound'` into `'static'`). `View.set_theme` does the same to every bound node at once. Fixed upstream in `tre` M91 (0.3.3, unreleased; verified locally 2026-09-25) — closes when Tesserae moves to 0.3.3. Note that after the fix, a declared `on_change` handler fires once per reload.
- `App.run(hot_reload=True)` only watches screens registered through `App.load()` (M29 Phase 6): a screen given to `App.register()` directly -- e.g. `examples/multi_screen/`, whose `ViewModel`s need an `app` reference -- has no known file, so it isn't watched. A `path=` on `register()` would close this.
- Hot reload (`ViewWatcher`) doesn't watch theme or stylesheet files (M29 Phase 4); a theme edit needs an explicit `set_theme` call with a freshly loaded theme. Theme files: moved to **M31**, deferred by the user until `tre` issue #8 is fixed — now fixed in `tre` 0.3.3 (M91), so M31 waits on Tesserae's 0.3.3 migration. Stylesheet files: blocked — `tre` has no way to change a `View`'s stylesheet after construction (no `set_stylesheet`); requested as [`tre` issue #8](https://github.com/mindderivative/tre/issues/8) part 2 — added in `tre` M91 (`View.set_stylesheet`, 0.3.3, unreleased).
- The declarative cascade doesn't consult a theme's per-component `components:` override (imperative-only) — an app wanting that level of per-component customization uses `tesserae.widgets` instead of a declarative fragment.
- No dedicated `tesserae.widgets.text` wrapper for the raw `add_text` primitive — every widget needing text uses its own clear param instead; revisit only if a real caller needs the bare primitive.
- No routing beyond a plain named `App.show(name)` (no history/back-stack, no URL-style deep links); no app-level state store shared across screens; no `tesserae new` CLI scaffolding tool. All real, named, un-scoped future candidates — see `README.md`'s own "Explicitly deferred" section.
- Not published to PyPI. `tre` v0.3.2 is a published GitHub Release with 24 attached assets (`github.com/mindderivative/tre/releases/tag/v0.3.2`, 2026-09-25), and Tesserae's CI pins that tag, but neither `tre` nor Tesserae is on PyPI yet -- both still depend on a local editable checkout for actual development.

**Fixed gaps:**
- ~~Hot reload (`ViewWatcher`, M29 Phase 3) can't run inside `App.run()` — `tre`'s `View` is single-threaded and its loop had no way to run Python from another thread.~~ **Fixed (M29 Phase 6).** `tre` M87 added `App.thread_handle()`/`LoopHandle.call_soon` ([`tre` issue #6](https://github.com/mindderivative/tre/issues/6)); `App.run(hot_reload=True)` now watches every `load()`ed screen with a `watchfiles`-driven background `ViewWatcher`.
- ~~`App.load()`/`tesserae.instantiate()` don't use `load_view`/macro-expansion yet — a real app must call `tesserae.spec.load_view(...)` directly today.~~ **Fixed (M16).** `App.load()` now constructs via `load_view` directly; `tesserae.instantiate()` now expands `path` and hands off via `source=`.
- ~~`tesserae.instantiate()` (embedded components) can't use `component:` at all — blocked on a `tre`-side `Component.instantiate(source=...)` addition.~~ **Fixed.** `tre`'s own M73 (`instantiate(..., source=...)`) closed the blocker; M16 wired `tesserae.instantiate()` to use it.
- M7's own tracker entry wasn't flipped to ✅ before its commit (`686214a`) landed — Phase 2/3 checkboxes and the Top Metrics row both still read `⬜`/`🚧` despite the real MkDocs site, `docs.yml`, and `PLAN.md`/`LOG.md` all existing on disk. Caught and corrected while starting M8; all three deliverables verified present before flipping the status.
- ~~Progress & Status (`circular_progress`/`linear_progress`/`loading_indicator`) has zero fragments — no declarative `NodeKindSpec` equivalent exists for any of the 3.~~ **Fixed (M27).** `tre`'s own M84 added declarative support for all 3; fragments authored here.
- ~~`time_picker_dial`/`radio_button`/`switch`/`link` are the same "no declarative `NodeKindSpec`" story.~~ **Fixed (M27).** Same `tre` M84, same fragment-authoring pass.

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

---

## Milestone 17 — Part 3, Phase 3: Button Component Fragments (All 5 MD3 Variants)

**Status: ✅ Complete (2026-09-23).** User-directed ordering complete ("Start 3, then move to 2 and then 1" — items 3 and 2 both landed; this is item 1). Real scoping question resolved via `AskUserQuestion` before writing anything: since `{{ }}` substitution has no conditional branching, a widget with multiple real MD3 variants (button has 5: elevated/filled/filled_tonal/outlined/text) needs one fragment per variant, not one fragment with a `variant` param — user confirmed full fidelity, one fragment per variant, for all widgets going forward.

**Real, major blocking finding surfaced immediately after that decision, before continuing:** `engine-spec`'s `NodeKindSpec` supports only 7 of `engine-core`'s real 21 primitive kinds — no `kind: Icon` existed at all, confirmed directly (`unknown variant "Icon"`). This blocked roughly two-thirds of the remaining widget catalog (anything with an icon glyph: `icon_button`/`fab`/`chip`/`list_item`/`menu_item`/etc.) from being expressible as a fragment. Resolved via a second `AskUserQuestion`: added declarative `kind: Icon` to `tre` itself first (`tre`'s own new M74, committed on its `0.3.1` branch) rather than scoping fragment work down — see `tre`'s own `BUILD_TRACKER.md` for that work. Reinstalled into `tesserae/.venv` before resuming here.

This milestone itself ships the one widget that needed neither: all 5 real `button` variants, faithful to `resolve_button_colors` (`window_factory.rs`) exactly.

### Phase 1 — Rename for the Per-Variant Convention ✅
- Step 1: `Button_Component.yaml` renamed to `ButtonFilled_Component.yaml` — the new naming convention is `<Widget><Variant>_Component.yaml`, referenced as `component: <Widget><Variant>` — ✅
- Step 2: real, necessary fix caught before it went unnoticed: every existing consumer of the old `component: Button` name (`tests/test_spec_expand.py`, `tests/test_spec_load.py`, `tests/test_app.py`, `tests/test_component.py`) updated to `component: ButtonFilled` — caught immediately by re-running the full suite after the `tre` reinstall, not silently left stale — ✅

### Phase 2 — The Other 4 Variants ✅
- Step 1: `ButtonElevated_Component.yaml` — container=`surface_container_low`, label=`primary`, `elevation: level_1` (MD3's real named token, confirmed to equal the identical `1.0` `add_button`'s own unthemed fallback uses — `engine_md3::shape::ELEVATION_LEVEL_1`) — ✅
- Step 2: `ButtonFilledTonal_Component.yaml` — container=`secondary_container`, label=`on_secondary_container` — ✅
- Step 3: `ButtonOutlined_Component.yaml` — container=`transparent` (confirmed as a real, valid CSS color keyword `peniko::color::parse_color` accepts, verified with a live test before relying on it), label=`primary`, `border_color: outline`, `border_width: 1.0` — ✅
- Step 4: `ButtonText_Component.yaml` — container=`transparent`, label=`primary`, no border/elevation — ✅

### Phase 3 — Verification ✅
- Step 1: all 5 variants cross-checked in one pass against `tesserae.widgets.button(...)`'s own real output, comparing `corner_radius`/`elevation`/`border_width` for every variant — all 5 MATCH exactly — ✅
- Step 2: full suite re-run after the rename fix — 101 passed, 0 regressions — ✅

**Real naming convention now established for the rest of item 1:** `<Widget><Variant>_Component.yaml` / `component: <Widget><Variant>` for every widget with more than one real MD3 variant; a single `<Widget>_Component.yaml` / `component: <Widget>` for widgets with exactly one real shape.

---

## Milestone 18 — Part 3, Phase 4: `icon_button`/`fab`/`extended_fab` Component Fragments

**Status: ✅ Complete (2026-09-23).** Continues item 1, now unblocked by `kind: Icon` (`tre`'s own M74) -- the first 3 widget families that actually need an icon glyph.

`icon_button` (4 variants: filled/filled_tonal/outlined/standard) reuses `resolve_button_colors` directly, confirmed by direct read of `add_icon_button` -- `"standard"` maps to `"text"`'s own colors, the same real translation the imperative factory itself performs. `fab` (4 variants: surface/primary/secondary/tertiary) uses its own `resolve_fab_colors`; a real, useful finding: `elevation: level_3` is expressible as a genuine fixed MD3 token here (confirmed `ELEVATION_LEVEL_3 == 3.0`, the identical value `FAB_REST_ELEVATION_LEVEL` already uses, looked up with no variant at all -- the same across all 4 colors), so no elevation param is needed, unlike `corner_radius` (still a required param -- FAB's 3 real sizes each pair a fixed container size with their own real shape token, a caller picks the matching pair). `extended_fab` (4 variants, same `resolve_fab_colors`) has a real, fixed `corner_radius: large` token too (confirmed `SHAPE_LARGE == 16.0 == EXTENDED_FAB_CORNER_RADIUS` exactly, unlike plain FAB -- Extended FAB has no size variants in real MD3 at all).

**Real, deliberate scope boundary, named directly:** `extended_fab`'s own `icon` param is optional imperatively (changes both the leading padding *and* whether an `Icon` child exists at all) -- a genuine structural difference `{{ }}` substitution can't conditionally express. Only the leading-icon shape shipped this milestone (the more common real case); the icon-less shape is a real, separate, deferred fragment, not silently dropped.

### Phase 1 — Fragments ✅
- Step 1: `IconButtonFilled`/`IconButtonFilledTonal`/`IconButtonOutlined`/`IconButtonStandard` — a square `Rect` + centered `Icon`, `size`/`corner_radius` required params — ✅
- Step 2: `FabSurface`/`FabPrimary`/`FabSecondary`/`FabTertiary` — same real shape, `elevation: level_3` baked in as a real fixed token — ✅
- Step 3: `ExtendedFabSurface`/`ExtendedFabPrimary`/`ExtendedFabSecondary`/`ExtendedFabTertiary` — a `Container` (`flex_direction: Horizontal`) with a leading `Icon` + `Text` label, `corner_radius: large`/`elevation: level_3` both baked in as real fixed tokens (Extended FAB has no size variants), only `label`/`icon`/`width` as params — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_buttons.py` (new file) — 3 real pytest tests, each looping over its own family's 4 variants and cross-checking `corner_radius`/`elevation`/`border_width` against `tesserae.widgets`'s own imperative output (12 real variant checks total) — all MATCH — ✅
- Step 2: full suite — 104 passed (101 prior + 3 new), 0 regressions — ✅

**12 new fragments this milestone; 17 total so far (Buttons & Actions: `button` ×5, `icon_button` ×4, `fab` ×4, `extended_fab` ×4).**

---

## Milestone 19 — Part 3, Phase 5: `split_button` Component Fragments — Buttons & Actions Complete

**Status: ✅ Complete (2026-09-23).** The last widget in the Buttons & Actions category with a fixed (non-dynamic-list) shape: `split_button`, all 5 real MD3 variants (matches `button`'s own vocabulary — confirmed directly, `add_split_button` calls `resolve_button_colors` with the identical variant string). `button_group` (the category's only other remaining widget) stays out of scope — a genuinely dynamic list of N buttons, the same real structural limit already named for `tabs`/`navigation_rail`/etc.

Real, deliberate scope boundary, restated from `tesserae.widgets.split_button`'s own docstring and named directly in each fragment's own header comment: the real hover/press inner-corner "tightening" shape-morph animation (`PaintProperties.interactive_shape`/`corner_radii_override`) has no public Python API at all — this fragment is rest-state only.

Real, useful finding confirmed live before relying on it: a declarative `Container` with no explicit `width`/`height` genuinely shrinks to fit its real children (standard flexbox auto-sizing) — this is what lets the outer `Container` wrapping `leading`+`trailing` avoid needing `{{ }}` arithmetic to compute a total width.

### Phase 1 — Fragments ✅
- Step 1: `SplitButtonElevated`/`SplitButtonFilled`/`SplitButtonFilledTonal`/`SplitButtonOutlined`/`SplitButtonText` — an auto-sized `Container` (`flex_direction: Horizontal`, `gap: 2` — the real `SPLIT_BUTTON_GAP`) wrapping a `ButtonFilled`-shaped leading Rect+Text and a square trailing Rect+chevron Icon, both sharing the identical real `resolve_button_colors` output per variant — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_split_button.py` (new file) — 2 real pytest tests: all 5 variants cross-checked against `tesserae.widgets.split_button(...)`'s own real output, and a real id-namespacing structure check. Real bug caught in the test itself, not the engine, while writing it: id-namespacing is flat (every id inside a fragment gets prefixed once by the call-site's own id, regardless of nesting depth — `send_split.label`, not `send_split.leading.label`), matching pyCopper's own real `_namespace_names` precedent exactly — confirmed by direct inspection of the expanded YAML before fixing the test's own wrong assumption — ✅
- Step 2: full suite — 106 passed (104 prior + 2 new), 0 regressions — ✅

**Buttons & Actions category complete: 22 fragments** (`button` ×5, `icon_button` ×4, `fab` ×4, `extended_fab` ×4, `split_button` ×5) — every fixed-shape widget in the category now has a real, tested declarative fragment. Only `button_group` (dynamic list) remains out of scope, a real, structural limitation.

---

## Milestone 20 — Part 3, Phase 6: Selection & Input Component Fragments

**Status: ✅ Complete (2026-09-23).** `Checkbox`/`Slider`/`SpinBox` — the real, fixed-shape widgets in this category. `radio_button`/`switch` stay real, deliberately deferred: `engine-spec` has no declarative `NodeKindSpec` variant for either (the same real scope boundary `tre`'s own M74 named directly — `RadioButton`/`Switch` are real, valid `engine_core::NodeKind` values with zero declarative equivalent).

`Checkbox`/`Slider` map `checked`/`value` directly onto `WidgetSpec`'s own top-level fields (not a sibling block — confirmed directly against `build.rs`), and neither takes a `corner_radius` param — `add_checkbox`/`add_slider` both hardcode `0.0` imperatively, with no theming or param at all. Real, honest gap named directly in `Checkbox_Component.yaml`'s own header, not fixed here: `add_checkbox`'s own imperative construction additionally sets `mark_tint = theme.on_surface()` when a theme is set — a separate internal `CheckboxState` field the declarative build path never touches at all, so a declarative checkbox's checkmark always paints with its un-themed default tint.

`SpinBox`: a real, deliberate structural translation, not a compromise. `add_spin_box` itself builds 3 independent sibling nodes positioned via absolute x/y arithmetic (`field_x = base_x + SPIN_BOX_BUTTON_SIZE + SPIN_BOX_GAP`) — `{{ }}` has no arithmetic, so the fragment composes the identical visual result via a `Container` + `flex_direction: Horizontal`, the same real flexbox idiom every other fragment already uses. `add_spin_box` itself takes only `value` (no size/color params exist imperatively at all), so every other value is a literal/token — including a second real token match found: `corner_radius: small` for the field (confirmed `CHIP_CORNER_RADIUS=8.0` == `engine_md3::shape::SHAPE_SMALL` exactly, the same real key `add_spin_box` itself uses). Same real `text_tint` gap as `Checkbox` named directly: `TextFieldState.text_tint` has no declarative equivalent either.

### Phase 1 — Fragments ✅
- Step 1: `Checkbox_Component.yaml` — `params: [background, width, height, checked]`, real `mark_tint` gap named — ✅
- Step 2: `Slider_Component.yaml` — `params: [background, width, height, value]` — ✅
- Step 3: `SpinBox_Component.yaml` — `params: [value]` only, real `text_tint` gap named — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_selection.py` (new file) — 4 real pytest tests: `Checkbox`/`Slider` construct and read back correctly (`get_checked()`/`.get("thumb_position")`), `checked` confirmed as a real required param (not silently defaulted), `SpinBox` cross-checked against `tesserae.widgets.spin_box(...)`'s own real output — ✅
- Step 2: full suite — 110 passed (106 prior + 4 new), 0 regressions — ✅

**3 new fragments this milestone; 25 total so far.**

---

## Milestone 21 — Part 3, Phase 7: Cards, Lists, Chips & Structural Rows Component Fragments

**Status: ✅ Complete (2026-09-23).** `Card` (3 variants), `Chip` (5 real named variants), `ListItem`, `Badge` (2 structural shapes), `Divider`, `AccordionHeader`, `TreeNode` (2 structural shapes) — 15 new fragments. `link` stays out of scope: `NodeKind::Link` has no declarative `NodeKindSpec` equivalent at all, confirmed directly (`unknown variant "Link"`) — the same real gap already named for `radio_button`/`switch` at `tre`'s own M74.

Real token finds: `corner_radius: medium` for `Card` (`CARD_CORNER_RADIUS=12.0 == SHAPE_MEDIUM`, not variant-dependent in real MD3 card anatomy) and `corner_radius: small` for `Chip`/`BadgeLabeled` (`8.0 == SHAPE_SMALL`), both confirmed before relying on them.

`Chip`'s real variant space is genuinely 5 named states, not 4: `assist`/`filter`(unselected)/`filter`(selected)/`input`/`suggestion` — `input`/`suggestion` resolve to identical colors as unselected `filter`, but are real, distinct MD3 names kept as their own fragments on purpose. `ChipFilterSelected` is a real, distinct *structural* shape (an automatic checkmark Icon, not a param-driven color swap) confirmed directly in `window_factory.rs`'s own `show_checkmark` logic.

Real, deliberate scope boundaries, all named directly rather than silently dropped: `Chip`/`ListItem`/`ExtendedFab`-style optional leading/trailing icons and supporting text ship only the common no-icon case (multiple independent optional pieces changing real structure, `{{ }}` has no conditionals); `AccordionHeader`/`TreeNodeBranch` ship the collapsed rest state only (the real `expanded=true` chevron flip is a runtime `paint.transform` animation, not a structural difference). `TreeNode`'s real `depth * TREE_NODE_INDENT_WIDTH` indent arithmetic (`{{ }}` has none) is handled by requiring the already-computed `left_padding` as a param instead of `depth` — the same real "require the final computed value" precedent `ButtonFilled`'s own `corner_radius` param already established.

### Phase 1 — Fragments ✅
- Step 1: `CardElevated`/`CardFilled`/`CardOutlined` — content-free Rects, `corner_radius: medium` — ✅
- Step 2: `ChipAssist`/`ChipFilter`/`ChipFilterSelected`/`ChipInput`/`ChipSuggestion` — `corner_radius: small`; `ChipFilterSelected` includes a real fixed checkmark Icon — ✅
- Step 3: `ListItem` — single-line, no-icon case — ✅
- Step 4: `BadgeDot`/`BadgeLabeled` — the two real structural shapes, fixed `error`/`on_error` colors (no theming choice in real MD3 badge anatomy) — ✅
- Step 5: `Divider` — takes `width`/`height` directly rather than `length`/`vertical` (avoids 2 fragments for what isn't a real MD3 variant, matching `tesserae.widgets.divider`'s own imperative design) — ✅
- Step 6: `AccordionHeader` — real, useful finding: `flex_grow: 1` on the headline avoids `add_accordion_header`'s own `headline_width = width - 2*padding - icon_size - gap` arithmetic entirely — ✅
- Step 7: `TreeNodeLeaf`/`TreeNodeBranch` — the two real structural shapes (chevron present/absent) — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_structural.py` (new file) — 9 real pytest tests covering all 15 fragments: `Card`/`Chip` cross-checked against `tesserae.widgets`'s own imperative output across every real variant/case; `Badge`/`Divider` cross-checked too; `ListItem`/`AccordionHeader`/`TreeNodeLeaf`/`TreeNodeBranch` structurally verified (including a real, direct proof that `TreeNodeLeaf` genuinely has no `chevron` node at all, not just an empty one) — ✅
- Step 2: full suite — 119 passed (110 prior + 9 new), 0 regressions — ✅

**15 new fragments this milestone; 40 total so far.**

---

## Milestone 22 — Part 3, Phase 8: Navigation & Shell Component Fragments (Fixed-Shape Members)

**Status: ✅ Complete (2026-09-23).** `ToolbarDocked`/`ToolbarFloating`, `TopAppBar`, `StatusBar` — the real, fixed-shape widgets in this category, all content-free (an app populates them via nested `component:`/`Node.add_child`). `tabs`/`navigation_rail`/`navigation_drawer` stay real, deliberately out of scope — each takes a genuinely variable-length list of entries, the same real structural limit already named for `button_group`/`list_`/`menu`.

Real correction caught before it shipped wrong: an initial `StatusBar_Component.yaml` draft guessed `text=on_surface`/typography `body_medium` without checking the real source first — caught by reading `add_status_bar`'s own body directly before relying on the guess, and fixed to the real values (`on_surface_variant`, `label_small`) before any test ran against it.

`Toolbar`'s own real design carries 3 independent axes (variant, orientation, tone) — real, deliberate scope narrowing: `tone` becomes a plain `background` param (a real MD3 role name the caller passes directly, since it's just one field's value, not a multi-field variant like `button`'s own); only the horizontal orientation ships (a docked toolbar has no vertical variant in real MD3 anatomy at all — `add_toolbar` itself rejects the combination — so this isn't a real gap for `ToolbarDocked`; `ToolbarFloatingVertical` is a real, separate, deferred fragment for `ToolbarFloating` specifically). `elevation: level_3` reused from the FAB fragments' own real token match. `TopAppBar` reuses the `flex_grow: 1` title-fills-remaining-space pattern `AccordionHeader_Component.yaml` already established, avoiding `add_top_app_bar`'s own width-subtraction arithmetic entirely.

### Phase 1 — Fragments ✅
- Step 1: `ToolbarDocked`/`ToolbarFloating` — content-free, horizontal-only, `background` as a real MD3 role-name param — ✅
- Step 2: `TopAppBar` — the common no-leading/no-trailing-icons case, `flex_grow: 1` on the title — ✅
- Step 3: `StatusBar` — real correction applied before shipping (see above) — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_navigation.py` (new file) — 4 real pytest tests, all cross-checked against `tesserae.widgets`'s own imperative output (`corner_radius`/`elevation`) — ✅
- Step 2: full suite — 123 passed (119 prior + 4 new), 0 regressions — ✅

**4 new fragments this milestone; 44 total so far.**

---

## Milestone 23 — Part 3, Phase 9: Overlays Component Fragments

**Status: ✅ Complete (2026-09-23).** `Dialog`, `Snackbar`, `SideSheetModal`/`SideSheetStandard`, `MenuItem`, `Tooltip` — 6 new fragments, every fixed-shape widget in Overlays. `menu` (`build_menu`'s own variable-length list of `MenuItem`s) stays out of scope — the same real structural limit already named for `tabs`/etc.

Real, useful pattern confirmed twice more: `Dialog`/`SideSheetModal` both return the full-window *scrim* imperatively (`self.wrap_node(scrim)`), which has no declarative "auto = window size" equivalent — `scrim_width`/`scrim_height` are required params on both, the same real gap `add_top_app_bar`'s own `self.width.get()` default already established. `flex_grow: 1` (the now-familiar pattern) avoids `Dialog`'s/`Snackbar`'s own text-width-subtraction arithmetic.

**Real, significant finding, not previously encountered:** `add_side_sheet` applies a per-corner `corner_radii_override` (only the sheet's inner edge is rounded) — `StyleSpec.corner_radius` has no per-corner concept at all declaratively. More importantly: **the imperative factory's own base `paint.corner_radius` field is a literal `0.0`** — the real visual rounding lives entirely in the override, which `Node.get("corner_radius")` never reads back. This means a `corner_radius` cross-check against the imperative call is *not meaningful* for `side_sheet` specifically, unlike every other fragment in this catalog — confirmed by direct testing, not assumed. Both fragments use a uniform `corner_radius: large` as the closer real visual approximation instead of matching the imperative's own misleading `0.0` readback (which would mean rendering a fully square panel).

Real bug caught in the test itself, not the fragment, while verifying `side_sheet`: `side_sheet(modal=True)` returns the outer scrim (confirmed live), not the inner panel — an initial test compared the scrim's own `elevation` (always `0.0`) against the declarative *panel*'s real `elevation: level_1`, a real apples-to-oranges mismatch. Fixed by comparing each side's own actually-returned node. A second, unrelated f32-vs-f64 float precision artifact (`0.3199999928474426` vs `0.32`) needed `pytest.approx`, the same real, harmless artifact `Dialog`'s own opacity already produced without needing a fix (that test never asserted opacity directly).

### Phase 1 — Fragments ✅
- Step 1: `Dialog` — real finding: returns the scrim, not the panel; `scrim_width`/`scrim_height` required params; `corner_radius: extra_large`/`elevation: level_3`/`opacity: 0.32` all real, fixed, confirmed values — ✅
- Step 2: `Snackbar` — the common no-action/non-closable case; `corner_radius: extra_small`/`elevation: level_3` — ✅
- Step 3: `SideSheetModal`/`SideSheetStandard` — the two real structural shapes (scrim-wrapped vs. plain panel); the real `corner_radii_override`/base-`0.0` finding named directly in both fragments' own header comments — ✅
- Step 4: `MenuItem` — the common no-icon/no-submenu-chevron case — ✅
- Step 5: `Tooltip` — `corner_radius: extra_small`, the same real token `Snackbar` already uses — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_overlays.py` (new file) — 5 real pytest tests, including the real test-bug fix described above and a `pytest.approx` fix for a harmless float-precision artifact — ✅
- Step 2: full suite — 128 passed (123 prior + 5 new), 0 regressions — ✅

**6 new fragments this milestone; 50 total so far.**

---

## Milestone 24 — Part 3, Phase 10: Search, Progress & Status, Media & Graphics, Date & Time Component Fragments

**Status: ✅ Complete (2026-09-23).** The last 4 widget categories, bundled into one milestone (matching how M14 already bundled Search & Progress/Status together imperatively). 9 new fragments: `SearchBar`, `SearchView`, `Image`, `DatePickerDaySelected`, `DatePickerDayToday`, `DatePickerDayOutsideMonth`, `DatePickerDay`, `PeriodSelectorAM`, `PeriodSelectorPM`.

**Progress & Status ships zero fragments — a real, confirmed-blocked category, not an oversight.** `CircularProgress`/`LinearProgress`/`LoadingIndicator` are all real `engine_core::NodeKind` variants; none has a declarative `NodeKindSpec` equivalent, confirmed directly via failing `unknown variant` YAML parse errors, matching `tre`'s own M74 scope note exactly (M74 added `Icon` but deliberately left progress indicators out). `video`/`node_graph`/`graph_node` (Media & Graphics) and `TimePickerDial` (Date & Time) are the same real, confirmed-blocked story — `Image`/`icon` (already directly usable via `kind: Icon`, no wrapper fragment needed) are the only two Media & Graphics primitives with a declarative path at all.

**Real finding 1 — `TextSpec.content` string-typing:** it's Rust `String`-typed; `DatePickerDay*`'s whole-value `{{ }}` substitution preserves the caller's real Python type verbatim, so a bare `day: 15` fails deserialization with `invalid type: integer, expected a string`. Callers must pass `day: "15"` — documented directly in all 4 `DatePickerDay*` fragments' own header comments. The same class of bug was caught and fixed in this milestone's own test suite: `test_date_picker_day_requires_a_quoted_string_day` originally wrapped `pytest.raises` around `expand_components(...)` (which never raises — it's pure string substitution, no schema validation); fixed to wrap `View(source=expand_components(...))` instead, since the real deserialize error only surfaces once `tre.View` parses the expanded text.

**Real finding 2 — declarative enum values are PascalCase:** `ContentFitSpec`'s real values are `Cover`/`Contain`/`Fill`, not the lowercase strings `image()`'s own imperative `fit=` kwarg accepts (`"cover"`/`"contain"`/`"fill"`) — found and documented directly in `Image_Component.yaml`'s own header after a live test. `src:` also resolves relative to the *calling view's own directory*, not the working directory — confirmed by pointing a test's `path=` at `tests/` itself (where the real `fixtures/pixel.png` already lives) rather than a throwaway temp directory.

With this milestone, every category in the original ~9-category widget-catalog scope has been explored to its real, natural completion point. The remaining unbuilt widgets are a real structural boundary, not mechanical follow-up: dynamic-list widgets (`tabs`/`navigation_rail`/`navigation_drawer`/`button_group`/`list_`/`menu`, no macro-layer loop construct) and primitives with no declarative `NodeKindSpec` (`radio_button`/`switch`/`link`/progress indicators/`video`/`node_graph`/`graph_node`/`time_picker_dial`). Neither gap has further scope without new `tre`-side work or a macro-layer loop construct, neither of which has been requested.

### Phase 1 — Fragments ✅
- Step 1: `SearchBar` — `params: [placeholder, width, corner_radius]` (pill shape, no matching MD3 token); `elevation: level_3`; `flex_grow: 1` for the `TextField` — ✅
- Step 2: `SearchView` — content-free full-screen overlay shape; `corner_radius: extra_large`/`elevation: level_3` — ✅
- Step 3: `Image` — uses `kind: Image` directly; real PascalCase-`fit`-value and relative-`src`-resolution findings documented in its own header — ✅
- Step 4: `DatePickerDaySelected`/`DatePickerDayToday`/`DatePickerDayOutsideMonth`/`DatePickerDay` — the 4 real distinct visual states; `corner_radius: 24` literal (fixed `DATE_CELL_SIZE=48`, no param needed); the quoted-string-`day` requirement documented in all 4 headers — ✅
- Step 5: `PeriodSelectorAM`/`PeriodSelectorPM` — 2 stacked options (`flex_direction: Vertical`), `corner_radius: small` — ✅
- Step 6: Progress & Status confirmed zero-fragment via direct failing-test verification of all 3 primitives — ✅

### Phase 2 — Verification ✅
- Step 1: `tests/test_fragments_remaining_categories.py` (new file) — 6 real pytest tests covering all 9 new fragments plus the quoted-string-`day` requirement; real test bugs caught and fixed during authoring (the `pytest.raises`-wraps-the-wrong-call bug above, and the image fixture path needing to resolve against a real `tests/`-rooted `path=` rather than a throwaway `tmp_path`) — ✅
- Step 2: full suite — 134 passed (128 prior + 6 new), 0 regressions — ✅

**9 new fragments this milestone; 59 total so far — the widget-catalog fragment-authoring pass (item 1 of the standing 3-item follow-up list) is at its real, natural completion point.**

---

## Milestone 25 — Scoping the Next Boundary + `NodeGraph` Component Fragment

**Status: ✅ Complete (2026-09-24).** User asked to scope the two real boundaries M24 named (dynamic-list widgets needing a macro-layer loop construct; primitives with no declarative `NodeKindSpec`). Direct source investigation, not assumption, found M24's own categorization of `video`/`node_graph`/`graph_node` as "confirmed blocked" was wrong for two of the three — a real correction, surfaced to the user before proceeding rather than silently carried forward.

**Real correction 1:** `add_node_graph` (`window_factory.rs`) builds a plain `NodeKind::Rect` — `background: surface_container_low` (real theme role lookup), `corner_radius`/`elevation` both literal `0.0` (`PaintProperties::new(container_color, 0.0, 0.0, 1.0)`), optional `border_color`/`border_width` (both `None` by default). Every field already exists declaratively (`StyleSpec.background`/`corner_radius`/`elevation`/`border_width`/`border_color` all real since M48/M49/M61) — zero new `tre` primitives needed. Shipped today as `NodeGraph_Component.yaml` (the common no-border case, matching this catalog's established "ship the common case, name the rest" pattern).

**Real correction 2:** `add_video` builds a `NodeKind::Image` seeded with a synthetic fully-transparent 1×1 placeholder pixel, real frames pushed later via `Node::push_frame(...)`. `kind: Image` is already declarative, but `ImageSpec.src` (`engine-spec/src/spec.rs`) is a required `String` — no way to declare a blank/synthetic placeholder without a real file on disk, so a faithful port isn't possible today. Rather than ship a non-faithful poster-image approximation (the user was offered this choice directly and declined it), filed **[`tre` issue #2](https://github.com/mindderivative/tre/issues/2)**: make `ImageSpec.src` optional, defaulting to the identical synthetic placeholder `add_video` already builds. Explicitly scoped to just the static placeholder shape in the issue — real frame playback stays imperative (`push_frame` needs a live runtime frame source no static YAML file could express), not requested as a new declarative concept.

**Real reclassification:** `graph_node` was never actually blocked by a missing `NodeKindSpec` — `add_graph_node` requires a live `graph` node reference (an already-existing `Node`) as its own attachment parent, and the macro layer's `{{ }}`-substitution model has no way to express "attach this expanded subtree under a different, already-existing node elsewhere in the tree" — a fragment always expands into a subtree at its own call site. Moved from the "no declarative primitive" bucket into the same "runtime-constructed, not statically declarable" bucket as `tabs`/`navigation_rail`/`navigation_drawer`/`button_group`/`list_`/`menu`, just via a genuinely different real mechanism (cross-tree parenting, not a list of children).

**Scoping output, not yet built:** with the correction applied, two real independent fronts remain for a future milestone — (1) `tre`-side additive `NodeKindSpec` support for `radio_button`/`switch`/`link`/`circular_progress`/`linear_progress`/`loading_indicator`/`time_picker_dial` (7 widgets; checked each real state struct against `WidgetSpec`'s existing fields: `radio_button`/`switch` would reuse `checked` exactly like `Checkbox` already does, `link` would reuse `text` verbatim exactly like `TextField` already does, `circular_progress`/`linear_progress` would reuse `value` exactly like `Slider` already does, `loading_indicator` needs no widget-level field at all — only `time_picker_dial` needs a genuinely new field, `mode: Hour/Minute`); (2) a macro-layer loop/repeat construct for the 6 dynamic-list widgets — real, novel design surface (`_substitute` in `expand.py` only handles scalar param values today; a list-shaped param needs new per-iteration templating and id-namespacing logic), with a permanent limitation regardless of syntax: content built this way is fixed at view-load/hot-reload time, not reactively live the way `tesserae.Repeater` already is. User chose to scope, not build, either front this milestone.

### Phase 1 — Investigation & Correction ✅
- Step 1: direct-source re-verification of `add_video`/`add_node_graph`/`add_graph_node`'s real construction, overturning M24's own "confirmed blocked" categorization for 2 of the 3 — ✅
- Step 2: sized the 2 real remaining fronts (`tre`-side primitives; macro-layer loop construct) against actual `WidgetSpec`/state-struct fields and `expand.py`'s real current logic, not estimated — ✅
- Step 3: filed `tre` issue #2 for `video`'s real, minimal unblocking change, scoped precisely to avoid over-asking (no declarative video-source/streaming concept requested) — ✅

### Phase 2 — `NodeGraph` Fragment ✅
- Step 1: `NodeGraph_Component.yaml` — themed `Rect`, `background: surface_container_low`, no border (common case); real structural boundary for `graph_node` documented directly in its own header — ✅
- Step 2: `tests/test_fragments_media_graph.py` (new file) — 1 real pytest test, live-verified `corner_radius`/`elevation` parity against `tesserae.widgets.node_graph()` — ✅
- Step 3: full suite — 135 passed (134 prior + 1 new), 0 regressions — ✅

**1 new fragment this milestone; 60 total so far. Both remaining fronts (`tre`-side primitives, macro-layer loop construct) are scoped but deliberately not started — next steps for a future milestone, pending user direction on which to pursue.**

---

## Milestone 26 — Detailed Scoping: `tre`-Side Primitive Additions & Macro-Layer Loop Construct

**Status: ✅ Complete (2026-09-24).** User asked to scope both of M25's remaining fronts as separate milestones. No code changed this milestone — pure investigation and design, grounded directly in `tre`'s real source (constructors, `PaintProperties` calls, imperative factory bodies) and in `pyCopper`'s real source (checked directly for a repeat/loop precedent — found none, confirming this is genuinely new design territory for the loop construct, unlike every other part of this macro layer, which was modeled on a real pyCopper precedent).

### Phase 1 — Front A Scope: `tre`-side `NodeKindSpec` Additions for 7 Primitives (tentatively M27) ✅

Mirrors the M74 `Icon` precedent: additive only, no architecture changes, each primitive gets a `NodeKindSpec` variant + a `build.rs` match arm. Sized against each real state struct and constructor:

| Primitive | New `WidgetSpec` field? | `PaintProperties.background` | Internal tint fields needing theme resolution |
|---|---|---|---|
| `Link` | None — reuses `text` verbatim (`TextField`'s own precedent) | `required_background` (role `primary`, exactly like `Text`/`TextField`) | None — simplest of the 7 |
| `RadioButton` | None — reuses `checked` as `selected` | `TRANSPARENT` (hardcoded) | `unselected_tint`("outline")/`selected_tint`("primary") |
| `Switch` | None — reuses `checked` as `on` | `TRANSPARENT` (hardcoded) | 5 fields: `track_off_tint`/`track_on_tint`/`track_outline_tint`/`handle_off_tint`/`handle_on_tint` |
| `CircularProgress` | None — reuses `value` | `TRANSPARENT` (hardcoded) | `indicator_tint`("primary") only |
| `LinearProgress` | None — reuses `value` | `TRANSPARENT` (hardcoded) | `track_tint`("surface_container_highest")/`indicator_tint`("primary") |
| `LoadingIndicator` | None — `style.width`/`height` feed `LoadingIndicatorState::new(w, h)` directly | `required_background` (its "background" is really the glyph tint, role `primary` when unset — same semantic as `Link`/`Text`) | None, but needs an **extra required step**: seed `paint.shape = Animated::new(state.shapes[0].clone())` at construction, or the first real tick visibly flashes (confirmed real bug class, not hypothetical — `add_loading_indicator`'s own code does this explicitly with a comment explaining why) |
| `TimePickerDial` | **Yes — the one real exception**: `hour: u8`, `minute: u8` (both default `0`) | `TRANSPARENT` (hardcoded) | `face_tint`("surface_container_highest")/`hand_tint`("primary") |

**Real, important correction to M25's own summary:** M25 said `radio_button`/`switch`/`circular_progress`/`linear_progress` would need "zero new fields" and left it at that — true for `WidgetSpec` fields, but incomplete: these 4 (plus `time_picker_dial`) hardcode their outer `PaintProperties.background` to `TRANSPARENT` and carry their *entire* real visual in internal per-kind tint fields that `Checkbox`/`Slider` never needed to theme-resolve (neither has any beyond `Checkbox`'s own single, cosmetically-minor `mark_tint`, confirmed to stay hardcoded white even declaratively — real, already-shipped, accepted gap). Without resolving these, a declarative `RadioButton`/`Switch`/progress-indicator would render in flat black regardless of theme — a real functional defect, not a cosmetic one. **Closed with a small reusable helper**, not a new subsystem: `required_background`'s own existing `resolve_color(spec, raw, scheme)` (already MD3-role-aware) generalizes directly — a new private `resolve_role_or_fallback(scheme, role_name, fallback) -> Color` used identically across all 5 arms, mirroring the exact `theme.is_set() ? role : fallback` pattern every one of these primitives' own imperative factory already hardcodes. M25's `mode: Hour/Minute` guess for `TimePickerDial` was also wrong (corrected here): the real constructor takes `hour: u8`/`minute: u8`, not a mode enum — `mode` always starts at `Hour` internally and isn't app-configurable at construction at all.

**Not in scope for M27:** retrofitting `Checkbox`/`Slider`'s own existing `mark_tint`-stays-hardcoded gap — pre-existing, already shipped, not introduced or worsened by this work.

- Step 1: sized all 7 primitives' real constructors (`RadioButtonState::new`/`SwitchState::new`/`CircularProgressState::new`/`LinearProgressState::new`/`LoadingIndicatorState::new`/`TimePickerDialState::new`) against `WidgetSpec`'s existing fields, per the table above — ✅
- Step 2: found and corrected M25's own incomplete summary — 5 of 7 primitives hardcode `PaintProperties.background` to `TRANSPARENT` and need a new internal-tint theme-resolution step `Checkbox`/`Slider` never required; scoped the fix as one small reusable helper, not a new subsystem — ✅
- Step 3: found `loading_indicator`'s real required `paint.shape` seeding step (avoids a confirmed first-tick flash bug) and corrected `time_picker_dial`'s real new fields (`hour: u8`/`minute: u8`, not the `mode` field M25 guessed) — ✅

### Phase 2 — Front B Scope: Macro-Layer Loop/Repeat Construct (tentatively M28) ✅

`expand.py`'s `_substitute` only handles scalar param values today (str/int/float/bool via whole-value typed substitution) — no existing capability to template N children from a list-shaped param. No pyCopper precedent to follow (checked directly). Real design surface: how a list param drives repeated child expansion, and how each repeated instance's `id:` gets namespaced without collision (`item.0.label`, `item.1.label`, ... is the natural extension of the existing per-call-site namespacing `_namespace_ids` already does).

**Real finding: the 6 target widgets are not uniform**, which changes how much the loop construct alone actually buys:

- **`list_`** (`add_list`) takes `items: Vec<PyRef<'_, Node>>` — already-built `Node`s, pure layout composition, zero internal per-item construction logic. The loop construct's cleanest possible target: repeat the *already-shipped* `component: ListItem` fragment over a list of param dicts (`with: {items: [{title: "...", ...}, ...]}`), splice the resulting `WidgetSpec` list into the calling `children:` array. Full fidelity, zero reimplementation — `ListItem_Component.yaml` is already a faithful, correct fragment; this front just repeats it.
- **`tabs`/`button_group`/`navigation_rail`/`navigation_drawer`/`menu`** all take raw `Vec<String>` (labels, optionally parallel `Vec<String>` icons, an `Option<usize>` selected index) and construct every child's real state-dependent active/inactive coloring *internally in Rust* (e.g. `add_tabs`'s own `active_color`/`inactive_color`/`container_color` resolution). A static `{{ }}`-substitution template has no conditional logic — it cannot express "this item's color depends on whether its own index equals `selected`" at all. A loop construct alone gives these 5 only a **static snapshot** (every item pre-styled to whatever state its own `with:` entry says, no live switching, and no way for the template itself to compute active-vs-inactive from a shared `selected` value). Real, faithful coverage would need a **second, separate new capability** on top of the loop construct: conditional per-item component/fragment selection (e.g. picking `TabActive`/`TabInactive` per item based on one of that item's own fields) — genuinely more design surface than "just" a repeat construct, and not scoped in detail here.

**Permanent limitation regardless of design, worth restating plainly:** anything a `repeat:`-shaped fragment produces is fixed at view-load/hot-reload time — not reactively live. An app wanting tabs/a list that changes at runtime (items added/removed, selection changing without a full reload) still needs the existing imperative `tesserae.Repeater`, not this. The loop construct's real value is authoring convenience for content that's fixed-but-data-driven at load time (e.g., a settings list built from a static config), not a replacement for `Repeater`.

**Recommendation, not yet acted on:** stage M28 itself in two parts if pursued — build the loop construct against `list_`/`ListItem` first (clean, fully faithful, real immediate payoff, and the simplest possible version of the mechanism to get right); treat the 5 Rust-internal-construction widgets as a separate, later decision once the conditional-per-item-styling question has its own scope.

- Step 1: checked `pyCopper` (this macro layer's own stated precedent) directly for a repeat/loop construct — found none, confirming this is genuinely new design territory — ✅
- Step 2: found the 6 dynamic-list widgets are not uniform — `add_list` takes pre-built `Node`s (pure composition) while the other 5 take raw `Vec<String>` and construct real state-dependent coloring internally in Rust, which changes how much a loop construct alone actually closes — ✅
- Step 3: scoped `list_`/`ListItem` as the clean, fully-faithful first target; named conditional per-item styling as a second, separate, un-scoped capability needed for full fidelity on the other 5 — ✅

**No fragments shipped this milestone — pure scoping. 60 fragments total, unchanged. User has not yet chosen which front (M27, M28, both, or neither) to build.**

---

## Milestone 27 — `RadioButton`/`Switch`/`CircularProgress`/`LinearProgress`/`LoadingIndicator`/`TimePickerDial`/`Link` Component Fragments

**Status: ✅ Complete (2026-09-24).** User-directed: "Start with M27 and then move onto M28." Front A from M26's own scoping, built for real this time, not just designed.

### Phase 1 — `tre`-Side: Declarative `NodeKindSpec` Support (landed as `tre`'s own M84) ✅

The actual code change (`engine-spec::NodeKindSpec` + `build.rs`) is `tre`-scoped, so it's tracked and numbered in `tre`'s own `BUILD_TRACKER.md`, not duplicated here in full. Real summary: M26's own scoping was verified against real current `tre` source before anything was written, and confirmed accurate on every field/role/constructor name it named. One real gap M26 missed, found and closed there: `Md3Baseline`'s fallback hex values live in `engine-py`, a crate `engine-spec` cannot depend on (dependency runs the other way) — resolved with a small, local copy of just the 4 values these 5 tint-heavy kinds actually need, not a bigger shared-constants refactor. `tre`'s own new `resolve_role_or_fallback` helper is the declarative-build-time sibling of the `theme.is_set() ? role : fallback` closure every affected imperative factory already had. `LoadingIndicator`'s own real required extra step (`paint.shape` seeded to its first real shape, avoiding a confirmed first-tick flash bug) was carried over correctly. `tre`'s own workspace test suite: `engine-spec` 105, up from 96 (+9); full verification chain green there.

### Phase 2 — Tesserae-Side: the 7 Component Fragments ✅

- Step 1: `RadioButton_Component.yaml`/`Switch_Component.yaml` — `selected`/`on` map onto `WidgetSpec.checked`, the identical real reuse `tre`'s own `build.rs` makes. No `background` param on either — both kinds' entire real visual lives in internal tint fields, now real-theme-resolved declaratively (a real improvement over `Checkbox_Component.yaml`'s own honest, still-open `mark_tint` gap, not inherited here) — ✅
- Step 2: `CircularProgress_Component.yaml`/`LinearProgress_Component.yaml` — `value` reused verbatim, the identical shape `Slider_Component.yaml` already established — ✅
- Step 3: `LoadingIndicator_Component.yaml` — the one kind among these 7 that *does* take a `background` param (its own glyph tint, the same real semantic `kind: Icon`'s `style.background` already has) — ✅
- Step 4: `TimePickerDial_Component.yaml` — `hour`/`minute` map onto `WidgetSpec`'s new fields, the one real primitive needing them — ✅
- Step 5: `Link_Component.yaml` — a real, deliberate design decision, not blind porting: `add_link` hardcodes `body_large` typography and `primary` color with zero override at all, but `tre`'s own declarative `kind: Link` (M84) reuses the same `text.role`/`style.background` machinery `Text`/`TextField` already expose, a real widening of capability. This fragment stays a faithful, literal port of `add_link` anyway (hardcoding `role: body_large`/`background: primary` inside the fragment itself, not exposed as params) — the goal every fragment in this catalog shares is identical MD3 behavior to the native widget, not maximum flexibility; a hand-written custom fragment can still use the wider `kind: Link` capability directly if it genuinely needs to — ✅
- Step 6: one real bug caught and fixed during this phase, not shipped: `Switch_Component.yaml`'s first draft named its own param `on` — PyYAML's default loader treats a bare, unquoted `on`/`off` as a real YAML 1.1 boolean literal (confirmed directly: `yaml.safe_load('on: false')` → `{True: False}`), silently breaking `{{ on }}` substitution since `_substitute`'s own string-key lookup never matched a boolean key — renamed to `is_on` — ✅
- Step 7: one real, small `tre`-side fix found and shipped alongside `tre`'s own M84 while writing `Link`'s test: `Node.get_text()` had no match arm for `Link` at all (it wraps the identical `TextState` `Text` does), leaving a `Link`'s content completely unreadable from Python — added the same one-line arm `Text` already has — ✅
- Step 8: 12 new pytest tests across 4 files (`test_fragments_selection.py` for `RadioButton`/`Switch`, new `test_fragments_progress.py` for the 3 Progress & Status kinds, `test_fragments_remaining_categories.py` for `TimePickerDial`, `test_fragments_structural.py` for `Link`), each comparing the declarative fragment's real observable state directly against its own imperative-catalog counterpart — ✅
- Step 9: full verification chain — ✅ (`tre`'s own full chain green, `pytest tests/` here 147 passed, up from 135, +12, 0 regressions; all 3 real examples — `counter`/`multi_screen`/`todo_list` — ran clean end to end.)

**With this milestone, 67 of ~68 real MD3 widgets now have a declarative fragment** (`video`/`node_graph`/`graph_node` are the only real remaining structural blockers, `extended_fab` deliberately deferred, all named in Known gaps above) — everything else left un-fragmented is the dynamic/list-shaped bucket M28 exists to address.

---

## Milestone 28 — Macro-Layer `repeat:` Construct, Staged Against `ListItem` First

**Status: ✅ Complete (2026-09-24).** User-directed, continuing directly from M27: "Start with M27 and then move onto M28." Real design work, not a port -- confirmed directly (again, matching M26's own earlier check) that `pyCopper` has no repeat/loop construct at all.

**Real finding before designing anything, changing the shape of the whole milestone:** checked `tre`'s own imperative `add_list` first, since M26's own scoping named it as the loop construct's "cleanest fit" target. `add_list` takes pre-built `Node`s and does pure layout composition (`window_factory.rs`, confirmed directly -- no `NodeKind::List` primitive exists in `engine-core` at all). This means "a list" was **already** fully expressible today, declaratively, as a plain `kind: Container` with `flex_direction: Vertical` and N literal `component: ListItem` children -- there was never a missing primitive to work around. The real, missing capability is narrower and more specific than "list support": letting a hand-authored `*_View.yaml` repeat one fragment call N times from static, known-at-authoring-time data, without duplicating N near-identical `component:` blocks by hand. Framed this way from the start, not "add a generic loop," kept the design small.

**Design:** a new, optional `repeat:` key on any `component:` node, holding a literal list of per-item mappings. Each item's own keys merge onto the node's shared `with:` values for that one iteration (a key given in *both* is a real, rejected `ComponentError` -- ambiguous which should win, so neither does, matching every other real "fail loudly" check this module already has); the fragment's own declared `params:` are validated per-iteration against that merged set, so a per-item-only required param (like `ListItem`'s own `headline`) works correctly without needing to also appear in the shared `with:` block. Each repeated instance's own id gets a real, automatic `.0`/`.1`/`.2`/... suffix under the call site's own id -- no author-chosen per-item id needed, and guaranteed collision-free by construction. `repeat:` used anywhere other than inside a `children:` list (the document root, or nested directly under a non-list key) is a real, clear error -- there's nowhere for a 2nd/3rd instance to go.

**Deliberately, explicitly out of scope, matching M26's own staging recommendation exactly:** the 5 Rust-internal-state-dependent-coloring widgets (`tabs`/`button_group`/`navigation_rail`/`navigation_drawer`/`menu`) are NOT addressed by this milestone -- their own real active/inactive coloring is computed inside Rust from a selected index, which a static `{{ }}`-substitution template genuinely cannot branch on. `repeat:` alone would only give them a static, always-identically-styled snapshot, not real fidelity -- a second, separate, un-scoped capability (conditional per-item component/fragment selection) is the real remaining gap for those 5, recorded in Known gaps above, not silently claimed as solved here.

**Not reactive, stated plainly, matching this module's own already-established limitation:** `repeat:`'s own items are fixed at macro-expansion time, before `tre` ever sees the file -- an app wanting runtime-changing content (items added/removed, live reordering, selection changing without a full reload) still uses the existing imperative `tesserae.Repeater`, not this.

### Phase 1 — Design + Implementation ✅
- Step 1: checked `add_list`'s own real imperative body directly, found the real gap is repetition, not a missing primitive -- corrected the milestone's own framing before writing any code — ✅
- Step 2: `_REPEAT_KEY` + the new per-item-merge/collision/validation logic in `_expand_component` (now returning a list of 1+ expanded fragments instead of exactly 1) — ✅
- Step 3: `_walk`'s own list-handling flat-maps over a new `_expand_list_item` helper instead of a 1:1 map, so one `repeat:` node can correctly splice N real nodes into a `children:` array — ✅
- Step 4: a real, load-bearing architectural point confirmed with its own test, not assumed: `repeat:`'s own value already supports `{{ param }}` substitution with zero extra code, since the existing general-purpose `_substitute` pass (unchanged) runs over the *entire* fragment template -- including a nested `repeat:` key's own placeholder value -- before `_walk` ever recurses into that nested `component:` node. A `repeat:` sourced from an *outer* component's own list-typed `with:` parameter composes correctly for free — ✅
- Step 5: `expand_components`'s own module docstring updated with M28's real design and its own deliberate scope boundary — ✅
- Step 6: 10 new real pytest tests (`test_spec_expand.py`) — expansion to N nodes with correct namespaced ids, matching the imperative `list_item` catalog as far as `list_item`'s own real return value allows (its root container, not its internal headline child -- no public API reaches that), zero-item repeats producing zero nodes, every real guard (`repeat:` must be a list, each entry must be a mapping, a `with:`/`repeat:` key collision, per-iteration missing-parameter validation, `repeat:` rejected outside a `children:` list), and the nested-substitution composition case named in Step 4 — ✅
- Step 7: one pre-existing test's own exact error-message assertion updated to match the real, intentionally widened message (`repeat:` is now a real, allowed key) — ✅
- Step 8: full verification chain — ✅ (`pytest tests/` 157 passed, up from 147, +10; all 3 real examples ran clean end to end.)

**With this milestone, both real fronts M25/M26 identified are complete.** The only remaining, named, un-scoped future work is the conditional-per-item-styling capability the 5 Rust-internal-coloring widgets would need for full `repeat:` fidelity -- a real, separate design question for whenever it's picked up, not started here.

---

## Milestone 29 — Tesserae Owns All File Handling; `tre` Gets Specs + Bytes Only

**Status: ✅ Complete (2026-09-25).** Scoped 2026-09-24; User direction, relayed verbatim through a handoff from the `tre` session: "Tesserae should not be pushing files directly to tre. It should be pushing spec information and handling the files itself." `tre` offers one data-ingestion path per concern; Tesserae owns reading, parsing, decoding and watching files. The `tre`-side counterpart is `tre`'s own M86 (scoped on `tre`'s `0.3.2` branch, not started). User go-aheads given 2026-09-24 for Phase 1 ("pin CI to 0.3.2 and start Phase 1"), Phase 2 ("push it and use Pillow for Phase 2") Phase 3 ("push it and use a poll loop for Phase 3") and Phase 4 ("push it and start Phase 4").

**Verified against current source before recording, not taken on trust:** every Tesserae line reference below matches today's code. On the `tre` side, `spec=` already exists on `View`, `View.instantiate`/`Component.instantiate` and `reconcile`, and `Window.add_image_from_bytes` (M82) and `Node.push_frame` exist too — on both `tre`'s `main` and `0.3.2`, so Phases 1–3 need no `tre` change and won't widen the CI/`tre`-branch gap (see the CI note below). `default_theme_spec=`/`custom_theme_spec=`/`stylesheet_spec=` and `tre.register_font` do **not** exist yet as Python API (the only source matches are an internal Rust local in `view.rs` and the renderer's own `register_fonts`), confirming Phase 4 is genuinely blocked on M86.

**Where Tesserae breaks the rule today:**
- `src/tesserae/spec/load.py:43` — `View(str(path), source=expanded, ...)`: `expand_components` builds a dict, `yaml.safe_dump`s it back to text (`expand.py:300`), and `tre` re-parses it.
- `src/tesserae/component.py:50` — `parent.instantiate(str(path), into, source=expanded)`: the same text round-trip.
- `src/tesserae/widgets/media.py:36` — `window.add_image(path, ...)`: `tre` opens and decodes the file.
- `src/tesserae/spec/components/Image_Component.yaml` — `image: {src: "{{ src }}"}`: `tre` loads the file during build.
- `load_view(**view_kwargs)` — forwards `custom_theme=`/`default_theme=`/`stylesheet=` to `tre` as file paths.

**Real gotchas carried over from the handoff (each one shapes a phase below):**
1. `include:` is only resolved on `tre`'s YAML-text path (`engine-spec/src/include.rs`); a `spec=` dict goes straight to `WidgetSpec`, which rejects unknown keys. Expand everything before handoff and never pass `include:` through.
2. Any `kind: Image` with `src:` that reaches `tre` makes `tre` open the file — including in hand-written views, not just the `Image` fragment.
3. `tre`'s `poll_reload()` watches a file `tre` read, so it no longer applies; hot reload becomes Tesserae's job.
4. `tre` prefixes `spec=` validation errors with `"spec=: ..."` and can't know the source file — Tesserae must re-raise naming the `*_View.yaml`.

### Phase 1 — `spec=` Handoff, No Text Round-Trip (no `tre` change needed) ✅

**One real change to the handoff's sequencing, found before writing code:** the handoff said to drop `path` entirely (`View(spec=...)`, `instantiate("", ...)`). Reading `tre`'s `View.__new__` showed that `path` does two more jobs even under `spec=`: it's the base directory `tre` resolves `image.src:` against (with none, `tre` raises `ImageSrcNoBaseDir`, and it always rejects absolute paths), and a non-empty `path` starts `tre`'s `ViewWatcher` for `poll_reload`. Dropping it now would break every `kind: Image` (including `Image_Component.yaml`'s own test) and `poll_reload` before Phases 2 and 3 replace them. So Phase 1 keeps passing `path`, with `tre` no longer *reading* the file, and removing it becomes Phase 3's last step.

- Step 1: `expand_components_to_spec(yaml_text, *, component_dirs=None, base_dir=None) -> dict` is now the primary entry point; `expand_components` stays as a thin text wrapper (public API, used across the test suite and docs), and nothing on the `tre` handoff path uses it — ✅
- Step 2: `load_view` → `View(str(path), spec=dict, ...)` — ✅
- Step 3: `instantiate` → `parent.instantiate(str(path), into, spec=dict)` (`path` kept as the `image.src:` base directory; see above) — ✅
- Step 4: `include:` (gotcha 1) — resolved in Tesserae rather than rejected, as a straight port of `tre`'s `engine-spec/src/include.rs`: same sole-key rule, same relative-to-the-including-file resolution, same confinement (no absolute paths, no `../` or symlink escapes), same cycle detection, same depth limit of 8. Resolved *before* `component:` expansion, so an included file can now use `component:` (under `tre`'s own text-path include it reached `tre` unexpanded and failed). `include:` inside a `*_Component.yaml` fragment is a clear `ComponentError` — fragments have no sensible base directory, and nested `component:` covers that use — ✅
- Step 5: `load_view`/`instantiate` re-raise `tre`'s `ValueError` as `"<path>: <tre message>"` (gotcha 4), e.g. `app/Settings_View.yaml: spec=: unknown variant 'Rectangle', ...` — ✅
- Step 6: one real regression found and closed that the handoff didn't mention: PyYAML's `safe_load` turns an unquoted `2026-09-24` into a `datetime.date`, which `tre`'s `spec=` rejects (confirmed directly: `'date' object is not an instance of 'str'`). The old text round-trip had turned it back into the string `"2026-09-24"`; a final `_normalize_scalars` pass does the same with `str()`, which gives exactly that string — ✅
- Step 7: 15 new pytest tests (`test_spec_load.py` 13, `test_component.py` 2) — include resolution, nested relative resolution, `component:` inside an included file, every `include:` guard (cycle, depth, escape, absolute, non-sole key, no base dir, inside a fragment), the date regression, file-named errors from both `load_view` and `instantiate`, and dict/text parity — ✅
- Step 8: full verification chain — ✅ (`pytest tests/` 172 passed, up from 157, +15, 0 regressions; all 3 examples ran clean; `mkdocs build --strict` clean.)
- Step 9: docs — `api/spec.md` rewritten (`spec=` handoff, `expand_components_to_spec`, a new `include:` section, file-named errors, and a note that `path` still reaches `tre` until Phases 2–3); `guide/component-fragments.md`'s loading section updated — ✅

### Phase 2 — Tesserae-Side Image Decoding (Pillow) ✅
- Step 1: decoder decided by the user — Pillow (`Pillow>=10.0` added to `pyproject.toml`'s `dependencies`; 12.3.0 installed). New `tesserae.images.decode_image(path) -> (rgba, pixel_width, pixel_height)`: `.convert("RGBA")` gives straight alpha, the exact contract `tre`'s `add_image_from_bytes`/`push_frame` take and what `tre`'s own `image::open(...).to_rgba8()` produced. Like `tre`: no EXIF orientation, first frame of an animation. Read/decode failures raise `OSError` naming the file, `add_image`'s own existing exception type — ✅
- Step 2: `widgets.image` → `decode_image` then `window.add_image_from_bytes(...)`; same signature, same `OSError` contract. The existing parity test against `tre`'s native `add_image` still passes — ✅
- Step 3: `Image_Component.yaml` needed **no change** — step 4 below strips `src:` from the fully expanded tree, so the fragment's own `src:` is handled the same way as a hand-written one. Only its header comment was updated — ✅
- Step 4: new `spec/images.py` — `extract_images(spec, base_dir)` removes every `kind: Image`'s `image.src:` (hand-written views too, gotcha 2; `fit:` kept), resolves it with `tre`'s own `resolve_image_src` rules (relative to the top-level view's directory, no absolute paths, no `../`/symlink escapes) so existing views behave the same, decodes it, and returns the frames; `push_frames(owner, frames)` pushes each onto its node after `tre` builds the view. Failures are a `ComponentError` naming the widget and file — ✅
- Step 5: **`instantiate` now gives `tre` no path at all** (`parent.instantiate("", into, spec=...)`, the handoff's own original target). Checked `tre`'s `component.rs` first: for an embedded component, `path` is only ever the base directory (and the file to read when there's no `spec=`), and with `include:` and `image.src:` both handled in Tesserae there's nothing left to resolve. `load_view` still passes `path`, now only as `poll_reload`'s watch target — ✅
- Step 6: 16 new pytest tests (`test_images.py`): exact decoded bytes (RGB and greyscale+alpha), missing/corrupt files, extraction (strip + keep `fit:`, nested images, input not mutated, non-image nodes untouched), every path guard, frame pushing, and end to end — wrapping `tre`'s `View`/`instantiate` entry points proves no `src:` and (for `instantiate`) no path reaches `tre`. `tre` has no API to read pixels back, but `push_frame` rejects a wrongly sized frame, so a clean real load proves `tre` accepted the frame. **Mutation-checked:** with `src:` stripping disabled, 3 of the 4 end-to-end tests fail, and the failures show `tre` opening the file itself — ✅
- Step 7: full verification chain — ✅ (`pytest tests/` 188 passed, up from 172, +16, 0 regressions; all 3 examples ran clean; `mkdocs build --strict` clean.)
- Step 8: docs — `api/spec.md` (new "Images" section; the `path` note now says only `poll_reload` remains), `guide/widget-catalog.md` (`image` is the one non-delegate), `installation.md` (Pillow comes with `pip install`) — ✅

### Phase 3 — Tesserae-Owned Hot Reload (poll loop) ✅

**Real finding, before designing the API:** `tre`'s `View` is `#[pyclass(unsendable)]` (can't be touched from another thread), and `App.run()` hands control to `tre`'s Rust event loop with no hook that calls back into Python periodically — checked every candidate: `canvas_draws` run only on an explicit `redraw_canvas`, an animation's `on_complete` fires once. So nothing can poll from inside `App.run()` today without a `tre` addition. Chaining animations to fake a timer was rejected as a hack. `tre`'s own `poll_reload` never had this either — it's an explicit method, called only from a loop the app controls (`tre`'s `examples/hot_reload.py`). Phase 3 therefore ships a watcher for app-controlled loops, and `App.run()` integration is recorded as a known gap, pending a `tre` hook.

- Step 1: user chose a plain poll loop (no new dependency). New `tesserae.spec.ViewWatcher(view, path, *, component_dirs=None)`: `poll()` compares each watched file's `(st_mtime_ns, st_size)` against the last poll; `files` lists them. Dependencies are recorded during expansion itself (`expand_with_dependencies`, plus `extract_images(..., dependencies=...)`), so the watched set is exactly what the build read: the view, every `include:`d file, every `*_Component.yaml` fragment used, and every image — wider than the handoff's "view + fragments", since includes and images changing are just as real. Recomputed on every reload, so a newly added include/fragment/image is watched from then on — ✅
- Step 2: on change, re-runs the whole pipeline via a new shared `build_view_spec` (the same one `load_view` now uses, so a reload can't drift from a first load), calls `view.reconcile(spec=...)`, then pushes every image again. Stamps are recorded *before* reading, so a write landing mid-reload is picked up by the next poll instead of lost — ✅
- Step 3: failures raise naming the file (`ComponentError`, or `ValueError` prefixed with the view path for a spec `tre` rejects) and leave the view unchanged; the error is raised once per edit — polling again without a further change returns `False`, so a log-and-continue loop isn't flooded — ✅
- Step 4: `load_view` now calls `View(spec=...)` with **no path at all**. With Phases 1–3 together, Tesserae gives `tre` no file path anywhere — view, component, include or image — ✅
- Step 5: 8 new pytest tests (`test_watch.py`): no-change polls, view-file edit (same `Node` updated in place), include edit, fragment edit, image edit, a newly added include watched after reload, a broken edit raising once and then recovering, and a `tre`-rejected spec named by file. **Mutation-checked:** with dependency tracking reduced to the view file only, exactly the 4 include/fragment/image tests fail — ✅
- Step 6: full verification chain — ✅ (`pytest tests/` 196 passed, up from 188, +8, 0 regressions; all 3 examples ran clean; `mkdocs build --strict` clean.)
- Step 7: docs — new `guide/hot-reload.md` (usage, error behavior, and the three limits: same thread, not yet inside `App.run()`, don't use `tre`'s `poll_reload`), nav entry, and a `ViewWatcher` section in `api/spec.md` replacing the old "path still reaches `tre`" note — ✅

### Phase 4 — Theme, Stylesheet & Font Loading ✅

**Update 2026-09-24:** the `tre` session reported M86 complete on `tre`'s `0.3.2` branch (`babef68`, `abcba45`, `d6c30ef`); since pushed, and CI is pinned to `d6c30ef`. API as scoped, plus: `*_spec=` kwargs come after `json=` (no positional callers change); an unknown key raises `ValueError` prefixed with the kwarg name; `register_font` takes `bytes` only (a `str` raises `TypeError`), is process-wide and deduplicated by content, and a `font_family` naming an unregistered family still silently falls back to a bundled face — so checking `register_font`'s return value against the theme's families is the only real guard. (The earlier CI caveat is resolved: CI's `tre` checkout is pinned to `d6c30ef`, which includes M86.)

**Checked against `tre` at `d6c30ef` before writing anything:** the `*_spec=` signatures on `View(...)`/`View.set_theme`/`Window.set_theme`, `ThemeSpec`/`TypographyOverride` (`engine-spec/src/theme.rs`), the stylesheet shape (`{styles: [...]}`), `tre`'s real error text for a bad dict (schema errors are prefixed `custom_theme_spec=: ...`; apply-time errors such as an invalid color are **not**), and that `tre` has no `set_stylesheet` (a stylesheet is construction-time only). The bundled families were read from `tre` itself by registering its four vendored font files (content-deduplicated, so harmless): `Roboto`, `Noto Sans Arabic`, `Hack Nerd Font Mono`.

- Step 1: new `tesserae.spec.load_theme(path)`/`load_stylesheet(path)` (`spec/themes.py`) read a YAML file into the dict `tre`'s `*_spec=` arguments take — empty file → `{}`, non-mapping or invalid YAML → `ValueError` naming the file, dates normalized like views. For `View.set_theme(custom_theme_spec=load_theme(...))` and `Window.set_theme(seed, custom_theme_spec=...)` — ✅
- Step 2: `load_view`'s `stylesheet=`/`default_theme=`/`custom_theme=` still take file paths (current-directory-relative, as `tre` treated them), but Tesserae reads them and hands `tre` only `*_spec=` dicts; the `*_spec=` forms still pass straight through, and giving both forms is a clear error. A `tre` error in a theme/stylesheet dict is re-raised naming that file rather than the view — ✅
- Step 3: new `tesserae.register_font(path) -> list[str]` (`tesserae/fonts.py`, exported at top level): reads the file and calls `tre.register_font(bytes)`; errors name the file. Tesserae records registered families so `available_families()` = bundled + registered — ✅
- Step 4: `tre` silently substitutes a bundled face for an unknown `font_family`, so Tesserae now issues a `FontFallbackWarning` naming the file and family, for a theme's `typography:` (in `load_theme`) and a view's own `text.font_family` (in `build_view_spec`, so reloads check too). A warning, not an error, because `tre` supports registering a font after a view exists; `warnings.filterwarnings("error", category=FontFallbackWarning)` makes it strict. The whole existing suite passes with it as an error, so no current view or fragment names an unavailable family — ✅
- Step 5: 18 new pytest tests (`test_themes.py`): theme/stylesheet reading and every error case, `load_view` handing `tre` only dicts (by wrapping `View`), a theme file and a stylesheet file really applying (observed through `corner_radius`), spec pass-through, the both-forms error, a bad theme key named by file, `set_theme` with a loaded theme, a real `register_font` on `tre`'s own Roboto file, family recording, a no-font-faces file, and all three warning cases. **Mutation-checked:** with the file-to-dict conversion disabled (paths passed to `tre` as before), the "`tre` gets only dicts" test fails — ✅
- Step 6: full verification chain — ✅ (`pytest tests/` 214 passed, up from 196, +18, 0 regressions; all 3 examples ran clean; `mkdocs build --strict` clean, new anchors checked in the built HTML.)
- Step 7: docs — new `guide/themes-and-fonts.md` (nav entry), `load_view`'s theme arguments and a `load_theme`/`load_stylesheet` section in `api/spec.md`, three new rows in `api/index.md` — ✅

**Real, recorded limits (not silently dropped):** `App.load()` still takes no theme arguments (the pre-existing known gap — use `load_view` + `App.register`); `ViewWatcher` doesn't watch theme/stylesheet files; and a `tre` error found while *applying* a theme (e.g. an invalid color) carries no `*_spec=` prefix, so Tesserae can only attribute it to the view file.


### Phase 5 — Docs ✅

Most of the per-feature docs had already landed phase by phase (`api/spec.md`, `guide/component-fragments.md`, `guide/widget-catalog.md`, `guide/hot-reload.md`, `guide/themes-and-fonts.md`, `installation.md`). This phase stated the rule once, in the places a user reads first, and swept the rest for anything contradicting it.

- Step 1: **real finding — Tesserae's own code broke the rule.** A sweep for `tre` being handed a path found `examples/multi_screen/app.py` building both screens with `tre.View(path)`, `guide/apps-and-screens.md`'s `register()` example doing the same, and `App.register`'s docstring suggesting it. All three now use `tesserae.spec.load_view`; the example still runs clean — ✅
- Step 2: the rule, stated for users: a new "Files: Tesserae reads them, `tre` gets data" section in `README.md` and `docs/index.md` (the latter also says how to keep to it when using `tre` directly: `*_spec=` forms, `ViewWatcher` not `poll_reload`) — ✅
- Step 3: `ARCHITECTURE.md` — layering diagram now shows `tesserae.spec`/`tesserae.fonts`/`tesserae.widgets` as the file-handling layers; new "Files and data (M29)" section with a file → what Tesserae does → what `tre` receives table; the Components section's stale `parent.instantiate(str(path), into)` corrected; "hot-reload via `View.poll_reload()`" replaced with Tesserae's own. `docs/architecture.md` got the same layering and statement — ✅
- Step 4: stale claims corrected along the way: `README.md`'s status and "Explicitly deferred" list (and `ARCHITECTURE.md`'s) still called the widget catalog deferred — it's real (67 fragments + `tesserae.widgets`); the docs home page's "every file a screen depends on can be hot-reloaded" overstated it (theme files aren't watched) and now says exactly what is — ✅
- Step 5: full verification chain — ✅ (`pytest tests/` 221 passed, 0 regressions; all 3 examples ran clean; `mkdocs build --strict` clean; a final sweep found no remaining `View(path)`, `str(path), into` or `poll_reload()` guidance.)

### Phase 6 — Hot Reload Inside `App.run()` (`watchfiles` + `tre` M87) ✅

*Built between Phases 4 and 5 and called "Phase 3b" in commits, PLAN.md and LOG.md — numbered 6 here because it was added after the original five were scoped.*

User-directed follow-up to Phase 3, after `tre` M87 closed [`tre` issue #6](https://github.com/mindderivative/tre/issues/6) with `App.thread_handle() -> LoopHandle` and a thread-safe `call_soon(fn)` (a callback queue, the user's choice in the `tre` session, not the issue's proposed `set_interval`). User, here: "push it and use watchfiles for the watcher". CI's `tre` pin moved to `0066203` (M87) first.

- Step 1: `watchfiles>=1.0` added as a dependency (1.3.0 installed). Checked its `watch()` first: `stop_event` goes straight to the Rust watcher, so `stop()` returns promptly (tested: under 2 s) — ✅
- Step 2: `ViewWatcher.start(handle)`/`stop()`/`running`. A background thread watches the *directories* of every dependency (robust to editors that save by replacing the file), filtered to exactly the dependency files, non-recursive. On a change it rebuilds the spec and decodes images **on the watcher thread** (`_rebuild()`, pure file work) and queues only `reconcile` + `push_frame` (`_apply()`) with `handle.call_soon`, each lambda binding its own spec as a default argument. The watcher thread never touches the view. A failed rebuild is queued as a callable that re-raises, so `tre` logs it like an input handler's exception and the loop and watcher carry on. If a reload moves a dependency into a new directory, the watch restarts with the new directory set — ✅
- Step 3: `poll()` kept for app-controlled loops (no thread, no events); it refuses to run while `start()`'s thread is active. Shares `_rebuild()`/`_apply()` with the threaded path — ✅
- Step 4: `App.run(max_frames=None, *, hot_reload=False)`: `hot_reload=True` starts a `ViewWatcher` for every screen registered through `load()` (which now records the view path) on the `tre` app's thread handle, and stops them all when `run()` returns. Screens given to `register()` directly have no known file and aren't watched. New `App.thread_handle()` exposes the same `LoopHandle` before `run()` (the `tre` app is created on first use and reset after each run, so a second `run()` still starts fresh) — ✅
- Step 5: 7 new tests. `test_watch_thread.py` (6): a real `watchfiles` watcher with a recording fake handle — the reload is queued from the `tesserae-watch:` thread and applies only when run on the main thread, include edits, a broken edit queued as a raising callable with the watcher still running and then recovering, a new dependency in a new directory, unrelated files ignored, prompt `stop()` and the start/poll guards. Edits retry with identical content in case the watcher isn't listening yet; 10 consecutive runs all passed. `test_hot_reload_live.py` (1): a real `App.run(hot_reload=True)` in a fresh subprocess (a second `App.run()` in one process can break unrelated tests), deterministic rather than raced — a first-frame callable makes the edit and re-queues itself at 20 ms/frame until the change reaches the live tree (locally: seen after 6 frames on a real display). **Mutation-checked:** with `hot_reload=False` the same script ran 97 frames and never saw the change. Skips when no frame renders: GitHub's runner has no display, so `App.run()` renders zero frames there (as the `tre` session confirmed with `tre` M88); verified locally with `env -u DISPLAY -u WAYLAND_DISPLAY -u WAYLAND_SOCKET` — 220 passed, the live test skipped — ✅
- Step 6: full verification chain — ✅ (`pytest tests/` 221 passed, up from 214, +7, 0 regressions; all 3 examples ran clean; `mkdocs build --strict` clean.)
- Step 7: docs — `guide/hot-reload.md` rewritten around `App.run(hot_reload=True)` (the "not inside `App.run()`" limit is gone), `api/app.md` (`run(hot_reload=)`, new `thread_handle`), `api/spec.md` (`start`/`stop`), `installation.md` (watchfiles) — ✅

**Related, not part of this milestone:** CI failed 9 of 157 tests because `ci.yml` checked out `tre`'s `main` (v0.3.1) while `tre`'s M84 lives only on the `0.3.2` branch. Fixed 2026-09-24 (user-directed): `ci.yml`'s `tre` checkout is now pinned to `ref: "0.3.2"`, with a comment to switch it to the `v0.3.2` tag once that ships. Confirmed green on the next push (run 36083895390, `82cf4f2`: 172 passed), and again after Phase 2 (run 36084805952, `7108c9e`: 188 passed). Then refined, relayed from the `tre` session as user-directed there: pinned to the exact commit `d6c30ef` (tip of `0.3.2`, now pushed, carrying M84 and M86) instead of the branch name, so later `0.3.2` work can't break Tesserae's CI (`9b643b0`); later moved to `0066203` for M87 (`07d0c53`). Finally pinned to the `v0.3.2` release tag once `tre` v0.3.2 shipped (relayed from the `tre` session as user-directed there; verified: annotated tag on origin → `c6f0913` on `tre`'s `main`, `0066203` an ancestor, only `tre`'s tracker and one test changed since).

---

## Milestone 30 — Theme Arguments on `App` and `App.load()`

**Status: 🚧 In progress — Phase 2 of 3 done (2026-09-25).** Scoped 2026-09-25; User-directed: "scope adding theme args to App.load()". Closes the long-standing known gap that `App` has no theme API at all. Since M29, `load_view` already accepts every theme argument (`theme_seed`/`dark`/`default_theme`/`custom_theme`/`stylesheet`, reading the files in Tesserae and handing `tre` `*_spec=` dicts), so the plumbing exists — the real work is deciding where a theme *lives* in a multi-screen `App`, which `tre` itself constrains.

**Real finding, checked against `tre` v0.3.2 before scoping, not assumed — it decides the API shape:** in `tre`, a theme belongs to the *window*, and the window gets it from the first screen. `Window.from_view(view)` shares that view's theme state with the window (`theme: view.theme.clone()`, `crates/engine-py/src/window.rs`), and `Window.show_view(view)` swaps the tree, handlers and context menus but **not** the theme. `App.show()` uses exactly these two calls. So if each screen had its own theme, after `app.show("Settings")` the declarative nodes would resolve against Settings' theme while everything drawn from the window's theme — imperative `tesserae.widgets` calls, interaction tints — would still use the first screen's. A stylesheet is different: it's genuinely per-`View` (a construction-time cascade layer, no window involvement).

**Also checked:** `View.set_theme(...)` re-resolves every node in place (`Reconciler::retheme`) and stores the new layers for later reconciles, so re-theming a live screen is possible — but each call is a *complete* selection (omitted arguments reset to defaults, not "keep previous"), and `{{ }}` bindings aren't re-applied. `tre` has no `set_stylesheet`, so a stylesheet can only be set when a `View` is built.

**Could change this design — [`tre` issue #8](https://github.com/mindderivative/tre/issues/8) (filed 2026-09-25, user-directed):** reproduced against v0.3.2, `set_theme` makes every bound node show its static YAML value until its `Signal` next changes (a label bound to `'bound'` reads `'static'` after a re-theme), and `reconcile` does the same to any bound node an edit touches. #8 asks `tre` to re-apply bindings after both (part 1) and to add `View.set_stylesheet` (part 2). If part 1 lands, Phase 3's theme-file hot reload is safe to ship as-is; until then it would visibly revert bound values on every theme edit. If part 2 lands, stylesheet files can be hot-reloaded too, instead of being left unwatched (Phase 3 Step 3). Worth deciding Phase 1 Step 3 with #8's status in mind.

### Phase 1 — Decide the API Shape ✅
- Step 1: where a theme lives — user chose **app-wide, on the constructor**: `App(..., theme_seed=, dark=, default_theme=, custom_theme=)` plus the `*_spec=` forms, applied to every screen `load()` builds (the recommended option; matches `tre`, where a theme is window-level) — ✅
- Step 2: stylesheets — user chose **per screen on `load()`, with an app-wide default**: `App(..., stylesheet=/stylesheet_spec=)` is the default for every screen, and `App.load(..., stylesheet=/stylesheet_spec=)` replaces it for that one screen — ✅
- Step 3: theme-file hot reload — user chose to **wait until `tre` issue #8 is fixed**. It moves out of this milestone into M31 (not started), so M30 can finish without a phase it can't build — ✅

### Phase 2 — Implementation ✅
- Step 1: `App.__init__` gains keyword-only `theme_seed=`, `dark=`, `default_theme=`/`default_theme_spec=`, `custom_theme=`/`custom_theme_spec=` and the default `stylesheet=`/`stylesheet_spec=` (existing positional calls unchanged). Theme and stylesheet files are read once, at construction, through `load_theme`/`load_stylesheet`, and kept as dicts — `tre` still never gets a path. Giving a path and its `*_spec=` twin together is a `ValueError` — ✅
- Step 2: `App.load(view_path, viewmodel_cls, name=None, *, stylesheet=None, stylesheet_spec=None)` builds the screen with the app's theme and either its own stylesheet or the app's default — ✅
- Step 3: `register()` itself is unchanged; to give a registered screen the app's theme and stylesheet there is now `App.build_view(view_path, *, stylesheet=, stylesheet_spec=)`, which `load()` also uses internally, so a registered screen and a loaded one are built the same way. `register()`'s docstring points to it, and `examples/multi_screen/` (whose ViewModels need the `app`, so it uses `register()`) now builds its views with it — ✅
- Step 4: `App.load()`'s docstring note that it takes no theme arguments is gone — ✅
- Step 5: checked with a throwaway script before calling this done (Phase 3 adds the committed tests): a custom theme's `styles:` reached every `load()`ed screen (`elevation` 3.0), the default stylesheet applied (`corner_radius` 8.0), a per-screen stylesheet replaced it (20.0), `build_view` gave a `register()` screen the same theme and stylesheet, the both-forms error fired, and a theme naming an unavailable font warned exactly once across three screens. `pytest tests/` 221 passed, 0 regressions; all 3 examples ran clean — ✅
- Step 6: MkDocs, per the standing rule — `api/app.md` (new constructor and `load()` signatures, why the theme is app-wide, new `build_view` section, `register` note), `guide/themes-and-fonts.md` (new "for an app" section; the "`App.load()` doesn't take theme arguments" note removed; the hot-reload note now points at `tre` issue #8), `guide/apps-and-screens.md` (`register()` example uses `app.build_view`); `mkdocs build --strict` clean, new anchors checked — ✅

### Phase 3 — Tests, Docs, Tracker ⬜
- Step 1: tests — an app-wide theme reaching every `load()`ed screen (observed through `corner_radius` via a theme's `styles:`, as M29 Phase 4's tests do), the app-wide default stylesheet, a per-screen stylesheet replacing it, the path/`*_spec=` exclusivity errors, the font warning firing once, and `register()` unaffected — ⬜
- Step 2: MkDocs — the pages were updated in Phase 2 (Step 6), per the standing rule; re-check them against the final tests and fix anything the tests turn up; `mkdocs build --strict` clean — ⬜
- Step 3: `BUILD_TRACKER.md` (move the closed gaps to "Fixed gaps"), republish the tracker artifact, `PLAN.md`/`LOG.md` — ⬜

---

## Milestone 31 — Hot Reload for Theme and Stylesheet Files

**Status: ⬜ Not started — waiting on the tre 0.3.3 migration.** Split out of M30 on 2026-09-25: the user chose to wait until [`tre` issue #8](https://github.com/mindderivative/tre/issues/8) is fixed rather than ship theme-file hot reload now. Today `View.set_theme` makes every node with a `{{ }}` binding show its static YAML value until its `Signal` next changes (reproduced against `tre` v0.3.2), so re-theming a running app on every theme-file save would visibly revert live data; and `tre` has no `View.set_stylesheet`, so stylesheet files can't be re-applied at all. Builds on M30's app-wide theme and per-screen stylesheets.

**Update 2026-09-25: `tre` issue #8 is fixed upstream, in `tre` M91** (`b15db6e` on the unreleased `0.3.3` branch). Verified here against the locally built `tre`: the original reproduction now reads `'bound'` after `set_theme` and after both kinds of `reconcile` edit, and the new `View.set_stylesheet(stylesheet_spec=/stylesheet=)` re-styles in place (a Rect's `corner_radius` became 9.0) while keeping bound values. So M31 now waits on Tesserae moving to 0.3.3 (see the 0.3.3 known gap), not on #8. Two consequences to design for: re-applying a `checked`/`text` binding goes through `set_checked`/`set_text`, so a declared `on_change` handler fires **once per live update**; and `set_theme`/`set_stylesheet` don't re-resolve an embedded `Component`'s static styles (it has its own reconciler), so screens using `tesserae.instantiate` won't fully re-theme.

### Phase 1 — Theme Files ⬜
- Step 1: once Tesserae is on `tre` 0.3.3 (bindings re-applied after `set_theme`, `tre` M91), with `run(hot_reload=True)` also watch the app's theme files; on change, re-read them on the watcher thread and queue one `View.set_theme(...)` per `load()`ed screen via `call_soon`, passing the complete selection each time (seed, dark, both theme dicts), since `tre` treats omitted arguments as defaults — ⬜
- Step 2: confirm with a real test that re-theming the first-shown screen also re-themes the window (they share one theme state), and that the other screens pick up the change too — ⬜

### Phase 2 — Stylesheet Files ⬜
- Step 1: once Tesserae is on `tre` 0.3.3 (`View.set_stylesheet`, `tre` M91), watch the app's default stylesheet and each screen's own, re-applying them the same way — ⬜
- Step 2: decide how to handle the two M91 consequences — `on_change` handlers firing once per live update, and embedded components not re-themed — and document whatever remains — ⬜

### Phase 3 — Tests, Docs, Tracker ⬜
- Step 1: tests (fake-handle watcher tests plus a subprocess live test, following M29 Phase 6's pattern); MkDocs (`guide/hot-reload.md`, `guide/themes-and-fonts.md`); `BUILD_TRACKER.md` and the tracker artifact; `PLAN.md`/`LOG.md` — ⬜
