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
tesserae.spec           -- every file a screen is built from, read
  | (load_view,                by Tesserae: include:, component:/with:/
  |  load_theme,               repeat: expansion against 67 built-in MD3
  |  ViewWatcher)              *_Component.yaml fragments, images
  |                             (Pillow), themes/stylesheets, and hot
  |                             reload (watchfiles) -- tre gets only the
  |                             finished spec, dicts and pixels
  |
tesserae.fonts          -- register_font(path): font file -> bytes for
  |                          tre, plus a warning for unavailable families
  |
tesserae.widgets        -- one Python function per MD3 widget (~68),
  |                          thin delegates to tre's own Window.add_*
  |                          factories, for widgets built dynamically
  |
tesserae.Repeater       -- one list Signal as the single source of
  |                          truth; keeps one Component+ViewModel alive
  |                          per item present, via instantiate (above)
  |
tesserae.{Signal,ViewModel,Computed,
  |        Effect,batch,untrack}                -- tesserae.reactive: Tesserae's
  |                                               own reactivity (M35, taken
  |                                               over from tre); feeds tre's
  |                                               binding tracking until M36
  |
tesserae.{View,Component}                    -- re-exports of tre's, until
  |                                               Tesserae builds views (M37)
  |
tre (Rust/Python hybrid engine)   -- Tree/layout/paint/dispatch/render,
                                        the declarative YAML+binding layer
                                        (engine-spec), live-window wiring,
                                        and real multi-instance component
                                        embedding
```

**Files stay on Tesserae's side.** Tesserae reads, parses, decodes and
watches every file; `tre` receives only data (`View(spec=...)`,
`reconcile(spec=...)`, `*_spec=` theme/stylesheet dicts, `push_frame`/
`add_image_from_bytes` pixels, `register_font` bytes). Tesserae never
gives `tre` a file path (M29).

`tre` is moving everything a framework can build out of the engine (its
M93–M103), and Tesserae is taking it over (M34–M43, see
[the design page](design/building-blocks.md)). Reactivity is Tesserae's
since M35; `View`/`Component` are still `tre`'s. Tesserae's own real,
additive value is `App`, `instantiate`, `Repeater`, the declarative
`component:`/`with:`/`repeat:` macro layer, the `tesserae.widgets`
imperative catalog, and all file handling -- images, themes, fonts and
hot reload.

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
