# Architecture

This page is a short orientation. The full design reference --
`ARCHITECTURE.md`, honest about what's real vs. planned -- lives in the
repository root:

[**Read the full `ARCHITECTURE.md`**](https://github.com/mindderivative/tesserae/blob/main/ARCHITECTURE.md){ .md-button }

## Layering

```
app.py                 -- the real entry point (owns one App instance)
  |
tesserae.App            -- registry of named (View, ViewModel) pairs +
  |                          one live tre.Window; App.show(name) switches
  |                          which pair that Window currently renders
  |
tesserae.instantiate    -- embeds a Component with its own ViewModel
  |                          into a View/Component, enforcing the same
  |                          naming convention as App.load
  |
tesserae.Repeater       -- one list Signal as the single source of
  |                          truth; keeps one Component+ViewModel alive
  |                          per item present, via instantiate (above)
  |
tesserae.{Signal,View,ViewModel,Component,
  |        Computed,Effect,batch,untrack}       -- thin re-exports of tre's
  |                                               own real, already-
  |                                               working MVVM + reactivity
  |                                               primitives
  |
tre (Rust/Python hybrid engine)   -- Tree/layout/paint/dispatch/render,
                                        the declarative YAML+binding layer
                                        (engine-spec), live-window wiring,
                                        and real multi-instance component
                                        embedding
```

Tesserae does not duplicate `tre`'s own real capability in slower,
less-tested Python -- `Signal`/`View`/`ViewModel`/`Component` are
`tre`'s own classes, imported unmodified. Tesserae's own real,
additive value is `App`, `instantiate`, and `Repeater`.

## Build history

See [`BUILD_TRACKER.md`](https://github.com/mindderivative/tesserae/blob/main/BUILD_TRACKER.md)
for the complete, phase-by-phase build history -- every real milestone
this project has built, what was learned, and every real gap found and
closed.

Tesserae's own shape follows [pyCopper](https://github.com/mindderivative/pycopper)
(an earlier, standalone framework by the same author, powered by a
direct GLFW/wgpu-py stack instead of `tre`) -- its `*_View.yaml`/
`*_ViewModel.py` naming convention, stylesheet cascade precedence, and
safe-expression-not-`eval` stance are proven decisions, credited
rather than reinvented from nothing.
