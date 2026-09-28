# Tesserae Architecture

Honest about what's real vs. planned, matching `tre`'s own
`BUILD_TRACKER.md` documentation discipline -- this file describes what
exists today, not an aspirational design.

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
  |                          naming convention as App.load (below)
  |
tesserae.Repeater       -- one list Signal as the single source of
  |                          truth; keeps one Component+ViewModel alive
  |                          per item present, via instantiate (above)
  |
tesserae.spec           -- all file handling for a screen (M15-M29):
  |                          include: resolution, component:/with:/repeat:
  |                          expansion against spec/components/*_Component
  |                          .yaml, image decoding (Pillow), theme and
  |                          stylesheet loading, and hot reload
  |                          (ViewWatcher: watchfiles on a background
  |                          thread, applied via tre's LoopHandle)
  |
tesserae.fonts          -- register_font(path) -> font bytes for tre;
  |                          FontFallbackWarning for unavailable families
  |
tesserae.widgets        -- one Python function per MD3 widget, built
  |                          by Tesserae from tre's building blocks
  |                          (M40-M42), most from the fragments
  |
tesserae.{Signal,ViewModel,Computed,
  |        Effect,batch,untrack}                -- tesserae.reactive: Tesserae's
  |                                               own reactivity (M35, taken
  |                                               over from tre)
  |
tesserae.{View,Component}                    -- tesserae.view: views built,
  |                                               reconciled and wired by
  |                                               Tesserae (M37)
  |
tre (Rust/Python hybrid engine)   -- Tree/layout/paint/dispatch/render,
                                        the declarative YAML+binding layer
                                        (engine-spec), the live-window
                                        wiring (Window.from_view/show_view, no longer used by Tesserae since M37,
                                        tre's own M42), and real
                                        multi-instance component embedding
                                        (View.instantiate/Component,
                                        tre's own M43)
```

`tre` is moving everything a framework can build out of the engine (its
M93–M103); Tesserae takes it over in M34–M43
(`docs/design/building-blocks.md`). Reactivity is Tesserae's since M35
(`tesserae/reactive.py`, taken over from `tre`'s pure-Python module with
the same behaviour). Until M36, `tre` still evaluates `{{ }}` bindings on
its native recording stack, so a Tesserae read with no Tesserae frame
open was passed on to `tre._core._record_read` (removed in M37 Phase 6,
once no view used `tre`'s evaluation). `View`/`Component` are Tesserae's
since M37 (`tesserae/view.py`). Files are Tesserae's too (next section). Tesserae's own real, additive value is
`App` (the real "one entry point, named-screen registry, switch without
re-bootstrapping" layer neither `tre` nor pyCopper's own `App`/`Engine`
split provide in this exact shape), `instantiate` (the same real
enforced-naming discipline, applied to embedded components), and
`Repeater` (automatic keyed add/remove diffing over `instantiate`, built
entirely in Python on top of it -- no new `engine-spec`/`engine-core`
work needed; see its own module doc comment for why a YAML-level
`for_each:` keyword was considered and set aside). M51: `View.instantiate`
sets a component's `path` when given a spec and a file, `reconcile`
re-inserts a rebuilt root at its old index (`insert_child`), and
`_prune_components` forgets components whose root a reload destroyed
(`_follow_alive`, then `_forget_dead`, which unwires them; `tre`'s `off`
on a destroyed node is harmless).

## Files and data (M29)

User direction: "Tesserae should not be pushing files directly to tre.
It should be pushing spec information and handling the files itself."
`tre` offers one data-ingestion path per concern; Tesserae owns reading,
parsing, decoding and watching.

| File | Tesserae does | `tre` receives |
| --- | --- | --- |
| `*_View.yaml`, `include:`d files, `*_Component.yaml` fragments | reads, resolves `include:` (a port of `tre`'s `include.rs` rules), expands `component:` | one finished dict: `View(spec=...)`, `instantiate("", into, spec=...)`, `reconcile(spec=...)` |
| images (`kind: Image` `src:`, `widgets.image`) | decodes with Pillow to straight-alpha RGBA | pixels: `push_frame`, `add_image_from_bytes` |
| themes, stylesheets | reads YAML (`load_theme`/`load_stylesheet`) | dicts: `stylesheet_spec=`/`default_theme_spec=`/`custom_theme_spec=` |
| fonts | reads bytes (`register_font`), tracks families, warns on fallback | bytes: `tre.register_font` |
| all of the above, over time | `ViewWatcher`: `watchfiles` events on a background thread, rebuild off the UI thread | `reconcile(spec=...)` + `push_frame`, queued on `App.thread_handle()` |

Because `tre` only ever sees a dict, it can't say which file a problem
came from; Tesserae re-raises `tre`'s `ValueError`s naming the source
file. Theme and stylesheet files are watched too (M31, `FileWatcher`).

**Logging:** Tesserae logs through loguru's shared `logger`
(`tesserae/log.py`) and adds no handler of its own, so an app's loguru
setup decides where messages go; `configure_logging()` is the one-call
console setup. A background hot reload that fails is logged at `ERROR`
(traceback at `DEBUG`) rather than raised through `tre`'s loop;
`ViewWatcher.poll()` still raises.

## `*_View.yaml` / `*_ViewModel.py`

Mirrors pyCopper's own real, validated convention (see its
`ARCHITECTURE.md`/`LESSONS_LEARNED.md`): a `ViewModel` is scoped
one-per-view-file, so a self-contained, independently-loadable pair is
what lets `app.py` register several and switch which one is currently
shown without re-bootstrapping each one from scratch. **Enforced at
runtime** (`tesserae.naming.check_naming_convention`, checked via
`inspect.getfile` against the `ViewModel` class's own defining file),
by both `App.load` (top-level screens) and `instantiate` (embedded
components) -- a mismatched pair raises `ValueError` immediately rather
than failing later when a handler name doesn't resolve.

## `App`

```python
app = App(width=240, height=120, title="My App")
view, viewmodel = app.load("Counter_View.yaml", CounterViewModel)  # or register() directly
app.show("Counter")   # attaches Counter's root to the app's window
...
app.show("Settings")  # detaches Counter (kept alive), attaches Settings
app.run(max_frames=...)
```

M37: `App` creates its `tre.Window` up front (themed with the app's
theme) and builds every screen into it with Tesserae's `View`. `show()`
attaches a screen's root under `window.root` (no padding, and content-
sized like a `from_view` root) and detaches the previous one with
`remove()`, which keeps it alive; `Window.from_view`/`show_view` aren't
used. Neither call re-parses YAML or re-attaches a `ViewModel`. A view
built on its own is rebuilt in the app's window by `register()`
(`View.move_to`). Components are built in their host's window with its
theme and stylesheet, and follow them.

**Themes (M30):** one theme per `App` -- `App(theme_seed=, dark=,
default_theme=, custom_theme=)` -- because in `tre` a theme belongs to
the window (`Window.show_view` never switches it). M31 had `App.show()`
call `Window.set_theme` too, for `tre`'s imperative widgets and tints;
M42 Phase 7 removed that, since nothing `tre` draws reads the window's
theme any more (and `tre` 0.3.5 removes `Window.set_theme`).
`App.set_theme_specs()` re-themes every built screen;
`run(hot_reload=True)` calls it when a
theme file changes (a `FileWatcher` thread). Stylesheet files are
watched too: `App.set_stylesheet_spec()` re-applies the default to every
screen using it, and a screen's own file re-styles the screens built with
it (`View.set_stylesheet`, `tre` M91). A stylesheet is per-`View`:
`App(stylesheet=)` is the default and `App.load(..., stylesheet=)`
replaces it for one screen. `App.build_view()` gives a `register()`ed
screen the same theme and stylesheet.

**Theme, M38:** `tesserae.Theme` (`theme.py`) is the resolved theme --
roles, `components:` shape and elevation, `typography:`, and MD3 motion
tokens -- replacing `tre`'s `Window.theme` for Tesserae's own widgets
(M39–M42). A theme's `typography:` styles display text in views (Text,
Link; not text inputs), carried on the cascade's prepared layers.
`App(dark="system")` is the default: it starts dark and follows the
window's `color_scheme` event; `set_dark` fixes or releases it. `App`
no longer themes the window (M42 Phase 7).

**Following the app's theme, M50:** `follow.py` finds an app by its
window: `App.__init__` calls `register_app`, which keeps a weak
reference keyed by `id(window)`. `tre`'s `Window` can't be weakly
referenced, and a live app keeps its window alive, so the id can't be
reused. A `Widget`, `Control`, `SpinBox` or `Indicator` made with no
`theme=` asks `initial_theme(window, None, self)`: on an app's window it
gets `app.theme` and joins `app._followers`, an insertion-ordered dict
held strongly so a widget no one kept still follows. An explicit theme
pins it, and a bare window gives MD3's baseline. `App._retheme` re-colours
the `build_view` views, then the followers, as one `_apply_all` with
rollback, used by `set_dark`, the `color_scheme` event and
`set_theme_specs`. `destroy`/`dispose` call `unfollow`, and a follower
whose node was destroyed under it is dropped at the next re-theme
(`alive`). YAML controls inside views are built with an explicit theme,
so their view re-colours them, as before. Phase 3: a `tesserae.View` on an
app's window with no theme argument at all (`dark` now defaults to
`None`, so `dark=False` counts as given) starts from `app._view_theme()`
and follows. `Dock` and `AppShell` start from `initial_theme` too.
Followers can define `_follow_theme(theme, view_theme)`, which
`follow.retheme` prefers to `set_theme`: a view takes the app's theme
arguments, and a shell re-colours itself and the dock it made, not the
widgets it was given, so a pinned bar stays pinned. `_follow_alive` lets a
view (whose `node` is a lookup method) say whether its root still exists.
Overlays follow through their widgets.

**Interaction, M39:** a clickable YAML node is a focusable
`role="button"` Tab stop (the compiler sets it, as `tre`'s
`set_on_click` did). `tesserae.interaction.Interaction` draws MD3's
state layer, ripple and focus ring from building blocks. It adds two
absolute children after the content. One is a clip box that follows the
node's corners and holds the layer and one circle per press. The other is
the ring, a stroked box 5 px outside the node, since a box's stroke is
drawn inside it. The node itself stays unclipped. A `View` keeps one per
`Rect` or `Container` whose spec wants it (`interaction_tint`,
`focus_ring_color`). `_sync_interactions` adds, removes and re-tints
them after every build, reconcile, re-theme and re-style. The extra
children stay after the spec's children, so the reconciler's indices
still hold. Their listeners go through the same per-node dispatcher as
the ViewModel's (`View._listen`), but they aren't unwired with it.
**Bound accessibility, M47:** an `a11y:` value that is a `{{ }}` binding
is left out of the compiler's fixed fields (`build._a11y_fields`, which
rejects a bound `role` or `live`) and out of a patch's resets, and
`View._wire_a11y` evaluates it like `bindings:` -- dependency-tracked,
checked with `tesserae.a11y`'s rules, set on the node that carries the
widget's accessibility (a Link's box, a TextField's input, a control's
target) -- so every reconcile, re-theme and re-style, which rewire, set
it again. A Link's text binding no longer renames a Link that `a11y:`
names, and a control's fixed `a11y:` fields now reach it at build and
patch (before, they were checked and dropped). From Python,
`tesserae.a11y.bind` does the same with one `Effect` per field.

**Hot reload for registered screens, M48:** `App._start_watchers` takes
each screen's file from its view (`view.path`, set when a `View` is built
from a file, kept by `register()`'s `move_to`), so a `build_view()`ed,
`register()`ed screen is watched as a `load()`ed one is; the separate
`_Registered.path` that only `load()` set is gone. A spec-built screen is
named in the log instead.

**Hot reload for components, M51:** `ComponentWatcher` (`spec/watch.py`)
is a `ViewWatcher` with no view of its own. `instances()` returns the
live components built from its file at reload time, and each reconciles
from a deep copy of the one rebuilt spec (a view keeps the spec it's
given). A trial build fails on the first instance before any has
changed, so a bad edit raises once. `App._live_components(path)` walks
the screens', `build_view()`'s and following views' `_components`,
nested ones included, pruning dead ones as it goes. `_start_watchers`
records the loop handle and starts one watcher per file found.
`tesserae.instantiate` calls `app.watch_component(path)` through
`follow.app_of(window)`, which starts a watcher for a file used for the
first time while hot reload runs and does nothing otherwise.
`_stop_watchers` (run's `finally`) stops them all, mid-run ones
included.

**Shell files, M52:** `shell_file.py` reads a `*_Shell.yaml`, a small
schema rather than a widget tree (`top_bar`, `navigation`, `status_bar`,
`zones`, `center`, `panels`), and `parse_shell_spec` checks every key,
raising `ShellSpecError` with `file: key: problem`. `build_shell` builds
the existing `AppShell` and widgets from it: the bars at `width="100%"`,
the rail from the navigation items' screen names, and no `theme=`, so
it follows the app (M50). `App.load_shell` builds, remembers the file
(`_shell_file`, for hot reload) and calls `use_shell`. The view pipeline
is untouched, since it has no pluggable kinds, and its reconcile would
fight the dock (M52 Q1).
Phase 3: `check_references` checks each panel (registered, or its
`<Name>_View.yaml` exists) and `on_navigate` before anything is built.
`place_panels` docks each by name, loading and registering a file one
(its ViewModel class `<Name>ViewModel`, imported once under the module's
own name so an app's earlier import is reused). `bind_navigation` wires
the rail to `app.show` or the method, and `app._navigation` lets `show`
move the rail's selection (`selected.set`, which doesn't fire
`on_change`). `AppShell.show_screen` now brings a docked root's tab
forward (a panel is a screen) and tracks the screen in `content` itself
(`_in_content`), removing it only while it's still there, so a screen
docked as a panel is never pulled back out. `tre`'s `dock_panel` takes a
node from wherever it's attached.

**Docking, M45:** `tesserae.docking.Dock` draws what `tre` 0.3.5 leaves to
the framework (D10). Each zone is a column -- a tab strip, a divider, and
the body registered with `window.add_dock_zone` -- since `tre` keeps a
zone's body to the one shown panel (it leaves other children, which is
where the drop highlight goes). Tabs are built with `window.create`, each
with an `Interaction`, and rebuilt when a zone's panels change. A press
starts `start_panel_drag` only once the pointer has moved 4 px, so a
click still selects; `dock_target` moves the highlight and `dock_drop`
moves the panel in the model and rebuilds both strips. `move()` calls
`dock_panel`, which moves a docked panel since `tre` 0.3.5.1 (`tre` issue
#14; on 0.3.5 it ran a drag with a synthetic release instead), and updates
the model itself, since `dock_panel` fires no `dock_drop`. The `Dock` owns
the window's two docking events, so a window has one.

**The app shell, M45:** `tesserae.shell.AppShell` is a vertical box at
100% of the window (so it follows resizes with no listener): the top
bar, a middle row -- navigation, the left zone and its handle, a centre
column (top zone, `content`, bottom zone) and the right zone -- and the
status bar. Zones keep a pixel size and the content flexes, so the
handles set a zone's size (clamped between 120 px and 70% of its area)
rather than sharing a proportion as M42's `splitter` does. `App.show`
mounts screens through `shell.show_screen` once `use_shell` is called: in `content`, one at a time, or -- with `center=True`, where `content` is the dock's center zone -- as center tabs, docked on first show and brought forward after.
`layout()` records panels by title, the shown one and each size;
`restore()` moves panels first, then shows and sizes.

**Controls, M40:** `tesserae.controls.Control` is the base of the
stateful MD3 controls that replace `tre`'s. It holds `.node`, a
focusable 48 px target with the control's role. A 40 px circle inside the
target is the `Interaction`'s `surface`, so events come from the target
while the feedback draws in the circle. The state and `disabled` are
Tesserae `Signal`s, and one `Effect` repaints when they change. `on_change`
hears only the user's changes. `tesserae.listeners.Listeners` is the
shared per-node dispatcher, which `View` uses too. `listeners.handled(fn)`
wraps every activation listener Tesserae adds (YAML `on_click`,
`Widget.on_click`, controls, `SpinBox`, overlay items, context menus,
`Dock` tabs). It calls `event.stop()` after `fn`, even if `fn` raises or
ignores the click (a disabled control), so `tre`'s bubbling `click` and
`secondary_click` reach only the innermost clickable (M49). `Interaction`'s
own `click` listener is feedback only and isn't wrapped. `tokens.BASELINE` is
MD3's published colours, for controls with no theme. `RadioGroup` keeps
one radio selected and one Tab stop (a roving focus, via `_focusable()`),
and moves the selection with the arrow keys. A `Switch` slides its handle
and state-layer circle with `translate_x` and sizes the handle with
`scale`, since tre won't animate layout; its focus ring goes around the
track (`Interaction`'s `ring_around`). A `Slider` captures the pointer
on press, so a drag can leave it, and positions its handle at once
rather than animating it. Its value snaps half up, as HTML's range input
does. `SpinBox` isn't a `Control`, since it's three targets (two icon
buttons, each with its own `Interaction`, and a `text_input` field), but
it has the same API. The indicators (`LinearProgress`, `CircularProgress`,
`LoadingIndicator`) share an `Indicator` base. It isn't focusable. It loops
its indeterminate animation by chaining `on_complete`, with a generation
counter so a settled or destroyed indicator stops. The loading indicator
lets tre morph `path` `data` between outlines, which tre resamples itself.
`TimePickerDial` is a `Control`: its hand is a `path`, and the selector
and state-layer circle move by `translate_x`/`translate_y`.

**Controls in views, M40 Phase 5:** the compiler builds the eight
control kinds as controls (`build._control`), recorded in
`Built.controls`, and `View.control(id)` returns one. They share the
view's `Listeners`. A trial build gets its own dispatcher, and its
controls are disposed. Bindings on `checked`/`selected`/`value`/`hour`/
`minute`/`disabled` set the control's `Signal`s. `on_change` and
`two_way:` use the control's `on_change`. A reconcile patches a control
in place (placement, colour, theme, and the YAML's state), but rebuilds
it when its size or `group:` changes (`control_shape`). A forgotten or
moved control is disposed. RadioButtons sharing a `group:` name share a
`RadioGroup` per view.

**Composed widgets, M41:** `tesserae.widgets._composed.Widget` expands a
fragment with a factory's arguments (through `expand_components_to_spec`)
and builds it as a `View` into the window, so it gets the compiler,
feedback, listeners and re-colouring (`View._use_scheme`) for free. With
no theme it uses `tokens.baseline_scheme()`: all 49 roles, from MD3's
baseline seed with the published baseline values over it. The compiler
sizes a `Text`/`Link` with no width or height to its content
(`build.natural_size`, via `window.measure_text`; `tre`'s `line_height`
is a multiple of the font size), and a bound `text` is measured again.
A widget built from several fragments (the button group) passes `Widget`
a spec made with `_composed.fragment`. A part's feedback takes its
content's colour (`content_role`). The split button's hover and the
button group's press morph animate `corner_radius` on the part and on
its feedback's clip together. Widths don't animate in tre, so the group's
reflow is set at once, from the resting width, which can't compound.
A `Link` compiles to a box (events, focus, `role="link"`, its text as its
label) holding a `text` (`build._link_props`, `_INNER`), because `tre`
0.3.4's `text` never gets pointer events. Handlers go on the box and text
bindings on the text. `Widget.on_click` gives any part feedback on
demand (`interactive`), and `after_theme` lets a widget whose state sets
colours (the filter chip) reapply them after a re-colour. Tabs, the
navigation rail and the drawer share `navigation._Selection`: a
`selected` `Signal`, one roving Tab stop, and wrapping arrow keys. The
tabs' indicator is a box whose width is set to the label's and whose
`translate_x` animates. A factory's `edit` runs before its `interactive`
parts are marked, so parts it adds can be interactive.

**Overlays, M41 Phase 5:** `tesserae.overlays.Overlay` wraps a `Widget`
built with `attach=False` and shows it with `window.show_layer`
(`modal`, `dismissible`). On `dismiss` it closes itself, so each overlay
chooses which dismissals apply by its flags and its scrim: a full-window
scrim takes outside presses, which leaves Escape. Timers (the snackbar's
4 s, the tooltip's 500 ms) are animations of a private box in no tree
(`_Timer`), since animations run there too. `SearchView` (M42) listens
to its bar's field through the bar's own dispatcher. It builds its
`max_results` rows once and attaches or detaches them as results change,
so no listener outlives a node. `image` and `video` (M42) are `Widget`s
over a `kind: Image` spec, built with frames (`Widget(frames=)`).
`video.frame()` sets the pixels and records them in the view's frames, so
a re-colour, which re-applies the frames, keeps the latest. The node
graph's content is a 0×0 box, which scales about its own origin, so a
graph point `p` shows at `offset + p × zoom` and zooming about the
pointer is arithmetic. `tre` hit-tests through the transform. Edges are
`path`s spanning a fixed coordinate space around the origin, re-routed
when a node moves. The segmented button (M42 Phase 5) is a 1 px-outlined
pill padded 1 px, so a selected segment's fill never covers the outline;
its end segments and their feedback clips take per-corner radii, set
again after a re-colour, since a style holds one radius. Pagination's
previous arrow is `chevron_right` turned 180° (`rotation_deg` isn't a
style property, so a re-colour keeps it). `Popover` sizes its text's
height with `measure_text(max_width=)` after building, and again after a
re-colour, because the compiler measures a Text with no height as one
line. The carousel (Phase 6) needs its item widths to change every frame
while it moves, but `tre` animates no `width` and has no frame callback.
So its fractional position is the `stroke_width` of a private node in no
tree, animated with the standard easing (`get` reads it mid-animation),
and `containment._Ticker`, a one-frame animation chained from its own
`on_complete`, re-lays the items out from it each frame until it
arrives. Its layout (`carousel_layout`) is a pure function of the
position, blending the snapped layouts either side of it. The splitter
is three flex children; a drag sets the panes' sizes at once.

`tesserae.a11y` checks accessibility fields against `tre`'s lists
(`describe`) and routes `a11y_action` (`on_action`). The YAML `a11y:`
field compiles through it (`build._a11y_props`, which also owns the
clickable node's focus and role, and resets dropped fields on a patch).

`App.load` is the enforced-naming-convention path (`*_View.yaml`/
`*_ViewModel.py`, checked via `inspect.getfile` against the
`ViewModel` class's own defining file -- `tre.View` has no `path`
getter of its own, confirmed by reading `view.rs` before designing
this, so `load` takes the path directly rather than trying to recover
it from an already-constructed `View`); `App.register` is the lower-
level path for a `ViewModel` that needs a live `app` reference at
construction time (to call `app.show(...)` from its own handler --
`examples/multi_screen/`'s own real reason for using it instead).

**Staying off `tre`'s removed API, M40–M43:** `tests/test_no_tre_controls.py`
scans `src/tesserae`'s code (not its prose) for every name `tre` 0.3.5
removes, taken from `tre`'s own `_removed.py`, and for `set_theme`/`theme`
on a window. The parity tests, which once compared Tesserae with a live
`tre` `View`, `Signal` or window theme, replay `tre`'s answers recorded on
0.3.4 (`tests/reference.py`, `tests/reference/*.json`, re-recorded with
`tools/record_tre_reference.py`): a test wraps each question in
`reference.tre(fn)`, keyed by the test and the order it asks, and the
answer (or the exception, re-raised with its type and message) comes back
from the recording. So the whole suite passes with `tre`'s
`TRE_FORBID_REMOVED` switch on (M43). Since M46 Tesserae runs on `tre`
0.3.5, where those names are gone, so the switch and its vendored copy
are retired; `test_tesserae_runs_on_a_tre_without_the_removed_api` checks
it.

## Components

```python
component, viewmodel = instantiate(view, "Card_View.yaml", CardViewModel, container)
```

`instantiate(parent, path, viewmodel_cls, into, *args, **kwargs)`
(`tesserae.component`) checks the naming convention, reads and expands
`path` itself (see Files and data above), then calls
`parent.instantiate("", into, spec=...)` (real `tre` M43 capability,
given a finished dict and no path -- `parent` is a `View` or another
`Component`, so components nest for free) and constructs
`viewmodel_cls(component, *args, **kwargs)`.
Extra `*args`/`**kwargs` are the real, common case a bare `App.load`
call doesn't need: a component's own `ViewModel` often needs data (an
item's own id) or a reference to shared state (`examples/todo_list/`'s
own `TodoItemViewModel` takes the shared `items` `Signal`, so its own
`remove_self` can mutate the single source of truth directly).

Multiple simultaneous instances of the same component are fully
independent -- each `instantiate()` call gets its own `Component`, its
own `ViewModel`, and (confirmed by `tre`'s own M43 investigation) its
own real `NodeId`s, even for widget ids repeated identically across
instances.

## Repeater

```python
items = Signal([])
repeater = Repeater(view, items, "Card_View.yaml", CardViewModel, container)
items.update(lambda lst: [*lst, new_id])   # adds; a removed id drops it
```

`Repeater.__init__` checks the naming convention once, subscribes to
`items_signal` (via its own real `_subscribe`, the same mechanism
`View._attach`'s bindings already use), and does an initial sync. On
every change, it diffs the new list's own keys (`key(item)`, default
identity) against the previously-rendered set: new keys call
`instantiate` (above); keys no longer present call `component.remove()`.

**Real, deliberate scope boundary:** no reordering (an already-present
key keeps its prior position in the shared `Tree` -- `engine_core::Tree`
has no child-reorder primitive today, confirmed by reading its source;
`tre`'s own `Reconciler` carries the identical real limitation), and no
re-application of a changed item's own *data* to an already-alive
instance (that's the item's own `ViewModel`'s job, via its own
`Signal`s -- see `examples/todo_list/`'s own `TodoItemViewModel`).
`Repeater.remove()` tears every remaining instance down and
unsubscribes, mirroring `Component.remove()`'s own real "unsubscribe
before tearing down" ordering.

## What's real today

- `App.register`/`load`/`show`/`run`, exercised end to end by
  `examples/counter/` (single screen, `load`) and
  `examples/multi_screen/` (two screens switching via `App.show()`
  from inside a real dispatched handler, `register`).
- `instantiate`/`Component.remove()`/`Repeater`, exercised end to end
  by `examples/todo_list/` -- a real dynamic list driven by one list
  `Signal`, `Repeater` adding/removing components automatically.
- What `tre.View`/`tre.Component` used to provide, now Tesserae's
  (`tesserae.View`/`Component`, M37), with Tesserae's own `Signal`/`ViewModel`: `{{ }}` binding expressions (a strict, non-`eval`
  whitelist), real `on_click`/`on_hover_enter`/`on_hover_exit`/
  `on_change` handler wiring, two-way binding for `checked` (Checkbox),
  `selected` (Switch/RadioButton), `value` (Slider) and `text` -- the
  `tre` 0.3.3 names (M32).
- Hot reload, owned by Tesserae (`tre`'s `View.poll_reload()` has no
  file to watch, since `tre` reads none): `app.run(hot_reload=True)`,
  or `tesserae.spec.ViewWatcher` directly.
- `Computed`/`Effect`/`batch`/`untrack`, Tesserae's own since M35
  (taken over from `tre`'s M45, same behaviour) -- derived/cached values, side-effect-only reactions, and
  collapsing related writes into one notification pass, all duck-typed
  against `Signal`'s own subscribe shape so a `{{ }}` binding can depend
  on a `Computed` with no special handling. See `README.md`'s own
  Reactivity section.

## Explicitly deferred

See `README.md`'s own "Explicitly deferred" section -- app-level
state/routing beyond `App.show`, a `tesserae new` CLI, PyPI publishing.
(The widget catalog once listed here is real now: 67 fragments plus
`tesserae.widgets`.)
`Repeater`'s own real, stated scope boundaries (no reordering, no
per-item data re-application) are named directly above, not repeated
here.
