# LOG — M15: Part 3, Phase 1 — Component Macro-Expansion Engine

- The real start of Part 3: `component: Name` / `with: {...}` in a
  `*_View.yaml` expands to a real `*_Component.yaml` fragment's own
  `WidgetSpec` subtree before `tre` ever parses the file. Modeled
  directly on pyCopper's own real, proven `source:`/`with:`/`params:`
  design (`pyCopper/src/pycopper/spec/include.py`, read in full first,
  not worked from memory of the earlier compacted summary).

## What shipped

1. `src/tesserae/spec/expand.py` — `expand_components`/`ComponentError`.
   Real investigation before writing any code: `tre` already has a
   working, unparameterized `include:` splice
   (`engine-spec/src/include.rs`), deliberately left untouched by this
   pass; `tre`'s declarative layer resolves MD3 color roles/shape
   tokens for real (verified with a live `theme_seed` call); the
   declarative cascade never consults a theme's per-component
   `components:` override (imperative-only) — a real, named gap.
2. A real, load-bearing bug found while testing, not assumed: PyYAML's
   `safe_dump` quotes a numeric-looking Python `str`, which would have
   turned every numeric param into a quoted string `tre`'s own
   `f32`/`f64` fields reject. Fixed by preserving a param's real type
   on a whole-value (not embedded) placeholder match — the same rule
   that lets a live `tre` binding expression forwarded as a param value
   survive untouched.
3. `src/tesserae/spec/load.py` — `load_view`, the real integration
   point (a plain function, not a `tre.View` subclass — `View` is a
   native `pyo3` class, and a function returning the genuine object
   works just as well for every real caller so far).
4. `src/tesserae/spec/components/Button_Component.yaml` — one real,
   faithful "filled"-variant fragment (container=`primary`,
   label=`on_primary`, matching `resolve_button_colors` exactly), with
   its own real, stated limitation: `corner_radius` is a required
   param, not derived from `height`, since `{{ }}` substitution has no
   arithmetic and no MD3 "full/pill" shape token exists to reach for
   instead.
5. Real, separate finding while scoping the integration point:
   `Component.instantiate` (`tesserae.instantiate()`'s own path) has
   no `source=` override at all — confirmed directly, it calls
   `std::fs::read_to_string(path)` with no way to inject pre-expanded
   text. `component:` can reach a top-level screen (`App.load()`
   constructs a `View` directly) but not an embedded component yet — a
   real, deferred gap needing a small `tre`-side widening, mirroring
   M71's own `View.__new__`/`poll_reload` precedent.
6. `pyproject.toml` — added a real `pyyaml>=6.0` dependency (previously
   only present transitively via `mkdocs`, never declared).
7. `tests/test_spec_expand.py` (13 tests) / `test_spec_load.py`
   (3 tests) — every guard named above, plus the real cross-check that
   matters most: constructing the same button both ways
   (`component: Button` through `load_view`, and
   `tesserae.widgets.button(...)` directly) and asserting identical
   `corner_radius`.
- Verification: `pytest tests/` 97 passed (81 prior + 16 new), 0
  regressions.

## Status

**M15 is complete.** The macro-expansion engine is real, tested, and
committed (`d5917cc`); push deferred pending explicit user
confirmation.

Deliberately deferred, named not dropped: the other 37 component
fragments; wiring `App.load()`/`tesserae.instantiate()` to use
`load_view` by default; a `poll_reload`-integrated re-expansion helper;
embedded-component `component:` support (blocked on the `tre`-side
`Component.instantiate(source=...)` gap).

Next: the remaining 37 component fragments (a separate, mostly-
mechanical milestone), or the `App.load()`/`instantiate()` wiring
follow-ups, whichever the user directs next.
