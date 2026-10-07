# Python API Reference

Every public class, function and constant, with its signature and what it does. This page is written from the code by `tools/generate_api_docs.py`, so it can't fall behind it.

## Contents

- [App](#app): The entry point: screens, one window, the loop.
- [Reactivity](#reactivity): Signals, computed values, effects and the ViewModel base class.
- [Views and components](#views-and-components): A loaded `*_View.yaml`, and an embedded instance of one.
- [Embedding](#embedding): A component with a ViewModel of its own, inside a view.
- [Repeater](#repeater): A list signal kept in step with a list of components.
- [Projects](#projects): A project's files, found by name.
- [Themes](#themes): A resolved MD3 theme, read from code.
- [Tokens](#tokens): MD3's colour, type, shape and motion tokens.
- [Widgets](#widgets): One function per MD3 widget, called against a window.
- [Controls](#controls): MD3's stateful controls.
- [Overlays](#overlays): Dialogs, menus, snackbars, tooltips, sheets, drawers.
- [App shell](#app-shell): Bars, navigation and docked zones around the screens.
- [Shell files](#shell-files): Reading and building a `*_Shell.yaml`.
- [Docking](#docking): Panels the user can drag between zones.
- [Interaction](#interaction): State layer, ripple and focus ring.
- [Accessibility](#accessibility): What a node tells assistive technology.
- [Bindings](#bindings): The `{{ expression }}` language.
- [Fonts](#fonts): Registering font files.
- [Icons](#icons): The built-in icon set.
- [Logging](#logging): Tesserae's log format.
- [Spec loading](#spec-loading): Reading, expanding and watching view files.

## App

`tesserae.app`: The entry point: screens, one window, the loop.

### `App`

```python
class App(
    width: int = 480,
    height: int = 320,
    title: str = 'Tesserae App',
    *,
    theme_seed: tuple[int, int, int, int] | None = None,
    dark: bool | str = 'system',
    default_theme: str | Path | None = None,
    default_theme_spec: dict[str, Any] | None = None,
    custom_theme: str | Path | None = None,
    custom_theme_spec: dict[str, Any] | None = None,
    stylesheet: str | Path | None = None,
    stylesheet_spec: dict[str, Any] | None = None,
    state: Any = None,
    root: str | Path | None = None,
    search: Any = (),
    recursive: bool = False,
    decorations: bool = True,
    resize_border: int | None = None,
    min_width: int = 0,
    min_height: int = 0,
    fullscreen: bool = False,
    system_menu: bool = False,
    icon: str | Path | None = None,
    window_border: bool = True,
    dpi_scaling: bool = True,
    present_mode: str = 'vsync',
    transparent: bool = False,
    blur_behind: bool = False,
    click_through: bool = False,
    glyph_cache: bool = False,
    system_fonts: bool = False,
    reduced_motion: bool | str = 'system',
    high_contrast: bool | str = 'system'
) -> None
```

`width`/`height`/`title` describe the one real `Window` this `App` opens the first time `show()` is called -- every registered view is shown inside that same window, at whatever size it already is, not its own independent size (matching `Window.show_view`'s own real, stated scope: only the *currently* active view's `width`/ `height` are kept in sync with the window).

- `back() -> bool`: Shows the history's previous entry, calling its ViewModel's `on_navigated` with that entry's params.
- `blur_behind` *(property)*: Whether the compositor blurs what is behind a see-through window (Wayland with KDE, macOS; ignored elsewhere).
- `build_view(view_path: str | Path, *, stylesheet: str | Path | None = None, stylesheet_spec: dict[str, Any] | None = None) -> Any`: Builds a view with this app's theme and stylesheet, without registering it -- for a screen given to `register()`, e.g. one whose `ViewModel` needs the `app` itself.
- `click_through` *(property)*: Whether the whole window ignores the pointer, so clicks reach what is behind it.
- `close() -> None`: Closes the window as the user's close would: `close_requested` fires first, so an app's "save changes?" check still runs and can cancel it.
- `current` *(property)*: The name last passed to `show()`, or `None` before the first real call -- lets a registered handler ask "which screen is this, anyway" without the app keeping its own separate bookkeeping.
- `dark` *(property)*: Whether the app is showing its dark scheme right now.
- `dark_mode` *(property)*: `"system"` (following the OS), or the app's fixed `True`/`False`.
- `decorations` *(property)*: Whether the OS draws the title bar and borders.
- `dpi_scaling` *(property)*: Whether the window lays out in logical pixels and draws at the display's scale (on by default), so it is sharp on a HiDPI screen.
- `forward() -> bool`: Shows the entry `back()` left, if any.
- `frame_stats(reset: bool = False) -> dict[str, Any]`: What the window's frames cost: `frames`, `skipped`, `last` (the last frame's stage times in milliseconds) and `recent` (the last 240 frames: `fps`, and the mean, 95th percentile and maximum of the total and the CPU time).
- `fullscreen` *(property)*: Whether the window fills its monitor, borderless.
- `glyph_cache` *(property)*: Whether text is drawn from a glyph cache: about four times cheaper a label, with slightly different edge pixels.
- `high_contrast` *(property)*: Whether the app uses MD3's highest-contrast colours: the user asked the OS for more contrast (or the app says so).
- `high_contrast_mode` *(property)*: `"system"` (following the OS), or the app's fixed `True` or `False`.
- `load(view_path: str | Path, viewmodel_cls: type | None = None, name: str | None = None, *, stylesheet: str | Path | None = None, stylesheet_spec: dict[str, Any] | None = None) -> tuple[Any, Any]`: Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it.
- `load_shell(path: str | Path, viewmodel: Any = None) -> Any`: Builds the app shell a `*_Shell.yaml` describes -- its top bar, navigation rail, status bar, docked zones, center tabs and panels -- and shows screens in it, as `use_shell` does.
- `location` *(property)*: The screen showing, as a route string (for saving where the user was): from the first route of its screen that reads its params back exactly, or `None` if none does.
- `maximize() -> None`: Maximizes the window (before `run()`, it opens maximized).
- `min_height` *(property)*: The shortest the user can resize the window to (0 for no limit).
- `min_width` *(property)*: The narrowest the user can resize the window to (0 for no limit).
- `minimize() -> None`: Minimizes the window (before `run()`, it opens minimized).
- `navigate(name: str, **params: Any) -> Window`: Shows the screen registered under `name` as a step in the history : `back()` returns from it.
- `navigate_to(route: str) -> Window`: Navigates to the screen the first matching route names, with the params it reads from `route` (a deep link, say `"notes/42"`).
- `of(view: Any) -> 'App | None'`: The live app whose window `view` (a view, a component, or a window) is on, or `None`: for a ViewModel's constructor, before `super().__init__(view)` gives it `self.app`.
- `on_file_drop(handler: Any) -> None`: Calls `handler(event)` when files are dropped anywhere on the window (`event.paths`); `None` stops it.
- `platform` *(property)*: `"windows"`, `"macos"`, `"wayland"` or `"x11"`.
- `present_mode` *(property)*: How frames are paced: `"vsync"` (one a display refresh, the default: an animating window uses a few percent of a core) or `"low_latency"` (the newest frame at once, and a whole core while something animates).
- `profile_nodes` *(property)*: Whether each node's drawing time is measured, so `frame_stats()["profile"]` says where it went.
- `reduced_motion` *(property)*: Whether the app is to reduce motion: the user asked the OS for it (or the app says so).
- `reduced_motion_mode` *(property)*: `"system"` (following the OS), or the app's fixed `True` or `False`.
- `register(name: str, view: Any, viewmodel: Any) -> None`: Registers `view` (already loaded) and its already-`_attach`ed `viewmodel` (e.g. `FooViewModel(view)`) under `name`, for a later `show(name)` to display.
- `resize_border` *(property)*: How many pixels along each edge resize an undecorated window (`tre` turns it off while maximized or fullscreen, and on macOS).
- `restore() -> None`: Restores the window from maximized or minimized.
- `route(pattern: str, name: str) -> None`: Adds a route: a pattern like `"notes/{id}"` for the screen registered (now or later) under `name`.
- `run(max_frames: int | None = None, *, hot_reload: bool = False, keepalive: bool | float = False) -> None`: The one blocking call -- opens the real `Window` and runs `tre`'s own real render loop, showing the screen `show()` made current and any nodes added to `app.window.root` by calls.
- `scale_factor` *(property)*: The display's scale (2.0 on a 2x screen); 1.0 until the window opens.
- `screen(name: str) -> tuple[Any, Any]`: The `(view, viewmodel)` registered under `name` -- by `register`, `load`, or a shell file's panels, whose ViewModels the app builds; `viewmodel` is `None` for a view with none.
- `set_dark(dark: bool | str) -> None`: `True`/`False` fixes the app dark or light, re-theming every screen in place; `"system"` goes back to following the OS from its next switch.
- `set_high_contrast(value: bool | str) -> None`: `True` or `False` fixes the app's contrast, re-theming every screen in place; `"system"` follows the OS.
- `set_icon(icon: str | Path | None) -> None`: The window's icon, from an image file (a PNG, best square), or `None` for none.
- `set_reduced_motion(value: bool | str) -> None`: `True` or `False` fixes the app's motion; `"system"` goes back to following the OS.
- `set_stylesheet_spec(stylesheet_spec: dict[str, Any] | None) -> None`: Replaces the app's default stylesheet in place: every view `build_view()`/`load()` made with the default -- not one given its own `stylesheet=` -- is re-styled, and views built later use it too.
- `set_theme_specs(default_theme_spec: Any, custom_theme_spec: Any) -> None`: Re-themes the running app in place: every view `build_view()`/`load()` made.
- `show(name: str) -> Window`: Shows the view registered under `name` in the app's window: its root is attached, and the screen shown before it is detached (kept alive, with its state and bindings).
- `start_trace(path: str | Path) -> None`: Writes every frame drawn from now on to `path`, for ui.perfetto.dev or chrome://tracing, until `stop_trace()`.
- `stats_handle() -> Any`: An object any thread can read the frame stats from: `handle.read()` is `frame_stats()` without the profile.
- `stats_overlay` *(property)*: Whether a small readout of the frame rate and what a frame costs shows in the window's top right corner.
- `stop_trace() -> int`: Ends the trace `start_trace` began and returns how many frames it holds.
- `system_menu` *(property)*: Whether a secondary press on the title bar opens the OS's window menu (Windows, and Wayland compositors with one).
- `theme` *(property)*: The app's resolved theme (`tesserae.Theme`): roles, component shape and elevation, typography, and motion tokens.
- `thread_handle() -> Any`: `tre`'s thread-safe `LoopHandle` for this app: the one object that may cross threads.
- `toggle_maximized() -> None`: Maximizes the window, or restores it if it's maximized: a title bar's maximize button.
- `transparent` *(property)*: Whether the window was made see-through (`App(transparent=True)`); `transparent_active` says whether it took.
- `transparent_active` *(property)*: Whether the window really is see-through (the platform may not allow it); `None` until it opens.
- `use_shell(shell: Any) -> None`: Shows screens inside `shell.content`: an `AppShell` built on this app's window -- a top app bar, navigation, docked panels and a status bar around the screens.
- `watch_component(path: str | Path) -> None`: While `run(hot_reload=True)` runs, watches a component file and reloads every live instance of it on change; `tesserae.instantiate` calls it, so a component first added while the app runs is watched too.
- `window` *(property)*: The app's one window (it exists from the start).
- `window_border` *(property)*: Whether an undecorated window gets its 1 px border (on by default): around the window, in the theme's `outline_variant`, a node of class `window_border` a theme or stylesheet can restyle.

## Reactivity

`tesserae.reactive`: Signals, computed values, effects and the ViewModel base class.

### `Computed`

```python
class Computed(fn: Callable[[], Any]) -> None  # extends _Notifiable
```

A derived, cached value. `fn` runs inside a recording frame to find its dependencies; when one changes, it runs again, and notifies its own subscribers only if the result changed:

Also has everything `_Notifiable` has.

- `get() -> Any`: The derived value, recomputed only when something it read has changed.

### `Effect`

```python
class Effect(fn: Callable[[], None]) -> None
```

Runs `fn` now, and again whenever something it read last time changes -- for side effects:

- `dispose() -> None`: Stops the effect: it no longer runs when what it read changes.

### `Signal`

```python
class Signal(value: Any) -> None  # extends _Notifiable
```

A reactive value. `get()` records a dependency when read inside a `Computed`, an `Effect` or a binding; `set()`/`update()` notify when the value actually changes.

Also has everything `_Notifiable` has.

- `get() -> Any`: The value.
- `set(value: Any) -> None`: Replaces the value, and tells everything that depends on it if it changed.
- `update(fn: Callable[[Any], Any]) -> None`: Sets the value to `fn(current)`, e.g. `clicks.update(lambda n: n + 1)`, unless that's the value it already holds.

### `ViewModel`

```python
class ViewModel(view: Any) -> None
```

The object a view's bindings and handlers resolve against. Constructing one attaches it to `view`: every declared handler is wired and every binding evaluated and subscribed.

### `batch`

```python
batch(fn: Callable[[], Any]) -> Any
```

Runs `fn()` with every `Signal`/`Computed` notification deferred until it returns, then runs each affected subscriber once -- not once per write, and not once per signal it depends on. Nested batches flush when the outermost returns.

### `untrack`

```python
untrack(fn: Callable[[], Any]) -> Any
```

Runs `fn()` and returns its result, without its reads being recorded by the enclosing `Computed`, `Effect` or binding.

## Views and components

`tesserae.view`: A loaded `*_View.yaml`, and an embedded instance of one.

### `Component`

```python
class Component(
    host: View,
    source: Any,
    frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
    path: Optional[Path] = None
) -> None  # extends View
```

An embedded view with its own ViewModel, built by `View.instantiate`/`Component.instantiate` (or `tesserae.instantiate`) in its host's window, with its host's theme and stylesheet. It follows them when the host is re-themed or re-styled.

Also has everything `View` has.

- `remove() -> None`: Unwires this component (its `Signal`s stop reaching it) and frees its nodes, and any components inside it.

### `View`

```python
class View(
    source: Any,
    *,
    window: Any = None,
    frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
    theme_seed: Optional[tuple[int, int, int, int]] = None,
    dark: Optional[bool] = None,
    default_theme_spec: Optional[dict[str, Any]] = None,
    custom_theme_spec: Optional[dict[str, Any]] = None,
    stylesheet_spec: Optional[dict[str, Any]] = None,
    project: Any = None,
    contrast: float = 0.0
) -> None
```

A built view. `spec` is an expanded view spec (from `tesserae.spec.build_view_spec` or `expand_components_to_spec`); `frames` maps an Image's id to its decoded `(rgba, width, height)`.

- `click(node: Any) -> None`: A synthetic click on `node`, for tests: `window.simulate`.
- `control(widget_id: str) -> Any`: The MD3 control (`tesserae.controls`) behind `widget_id`, one of the eight control kinds; its `.node` is `node(widget_id)`.
- `embedded(node_id: str) -> 'Component'`: The view the `view:` node `node_id` embeds.
- `instantiate(path: Any, into: Any, spec: Optional[dict[str, Any]] = None, frames: Optional[dict[str, tuple[bytes, int, int]]] = None) -> 'Component'`: Builds a component -- a view of its own, with its own ViewModel -- under `into`, a node of this view, in this view's window.
- `interaction(widget_id: str) -> Optional[Interaction]`: The state layer and ripple on `widget_id`'s node, or `None` when it has none.
- `move_to(window: Any) -> None`: Rebuilds this view in `window`, keeping its spec, theme and ViewModel: bindings and handlers are wired again on the new nodes.
- `node(widget_id: str) -> Any`: The node `widget_id` names (a TextField's `text_input`; a Link's box, which holds its text).
- `reconcile(spec: dict[str, Any], frames: Optional[dict[str, tuple[bytes, int, int]]] = None) -> None`: Brings the live tree in line with `spec`, in place.
- `root` *(property)*: The root node of this view's tree.
- `set_stylesheet(stylesheet_spec: Optional[dict[str, Any]] = None) -> None`: Replaces the stylesheet and re-styles every node in place; `None` clears it.
- `set_theme(theme_seed: Optional[tuple[int, int, int, int]] = None, dark: bool = False, default_theme_spec: Optional[dict[str, Any]] = None, custom_theme_spec: Optional[dict[str, Any]] = None, contrast: float = 0.0) -> None`: Re-themes every node in place.
- `spec` *(property)*: The expanded spec the view was built from: every `component:` and `include:` resolved.
- `theme` *(property)*: This view's resolved theme (`tesserae.Theme`).
- `viewmodel` *(property)*: The ViewModel attached to this view, or `None`.

## Embedding

`tesserae.component`: A component with a ViewModel of its own, inside a view.

### `instantiate`

```python
instantiate(
    parent: Any,
    path: str | Path,
    viewmodel_cls: type | None = None,
    into: Any = None,
    *args: Any,
    **kwargs: Any
) -> tuple[Any, Any]
```

Instantiates the component at `path` into `into` (a `Node`, e.g. from `parent.node(widget_id)`), constructs `viewmodel_cls(component, *args, **kwargs)`, and returns `(component, viewmodel)`.

## Repeater

`tesserae.repeater`: A list signal kept in step with a list of components.

### `Repeater`

```python
class Repeater(
    parent: Any,
    items_signal: Any,
    path: str | Path,
    viewmodel_cls: type | None = None,
    into: Any = None,
    key: Callable[[Any], Any] = <lambda>,
    args: Callable[[Any], tuple[Any, ...]] = <lambda>
) -> None
```

Keeps one component and ViewModel alive for each item of a list `Signal`, adding and removing them as the list changes.

- `remove() -> None`: Real, structural teardown -- removes every currently-tracked instance and unsubscribes from `items_signal`, mirroring `Component.remove()`'s own "unsubscribe before tearing down" ordering.

## Projects

`tesserae.project`: A project's files, found by name.

### `Project`

```python
class Project(
    root: str | Path,
    search: Iterable[str | Path] = (),
    recursive: bool = False
) -> None
```

The files under `root`, found by name. See the module docstring.

- `component_dirs() -> list[Path]`: The folders the components are in (each once), for `component:` to look in.
- `find(kind: str, name: str) -> Path`: The file of `kind` called `name`; `ProjectError` if there is none, or two.
- `folders(kind: str) -> list[Path]`: The folders that exist where `kind` is looked for, in order; with `recursive`, every folder under the root.
- `index(kind: str) -> dict[str, Path]`: Every name of `kind` and its file.
- `resolve(kind: str, ref: str | Path) -> Path`: `ref` as a file: a path is used as it is, a bare name is found.
- `style_dirs() -> list[Path]`: The folders that have `*_Style.yaml` files, for a node's `style:` that names one.
- `viewmodel(name: str) -> type`: The class `NameViewModel` in `Name_ViewModel.py`, imported.

### `ProjectError`

```python
class ProjectError
```

A name that is nowhere, or in two places.

## Themes

`tesserae.theme`: A resolved MD3 theme, read from code.

### `Theme`

```python
class Theme(
    seed: Optional[RGBA],
    dark: bool,
    roles: Optional[dict[str, RGBA]],
    components: dict[str, _Component] = <factory>,
    type_overrides: dict[str, dict[str, Any]] = <factory>,
    contrast: float = 0.0
) -> None
```

A resolved theme. Build one with `Theme.resolve(...)`.

- `duration(name: str) -> int`: An MD3 duration token, in milliseconds.
- `easing(name: str) -> Easing`: An MD3 easing token, as `animate(easing=...)` takes it.
- `elevation(component: str, variant: Optional[str] = None) -> Optional[float]`: A component's elevation level from `components:`, or `None`.
- `is_set` *(property)*: Whether there's a colour scheme (a seed was given somewhere).
- `resolve(theme_seed: Optional[RGBA] = None, dark: bool = False, default_theme_spec: Optional[dict[str, Any]] = None, custom_theme_spec: Optional[dict[str, Any]] = None, contrast: float = 0.0) -> 'Theme'`: Resolves a theme; raises `ValueError` for an unknown role, an unknown token in `components:` or an unknown `typography:` field.
- `role(name: str) -> Optional[RGBA]`: An MD3 colour role, or `None` without a scheme or for an unknown name.
- `shape(component: str, variant: Optional[str] = None) -> Optional[float]`: A component's corner radius from `components:`, or `None` when the theme doesn't say (the widget uses its own MD3 default).
- `spring(bounce: float = 0.0) -> Easing`: A spring easing: `bounce` from -1 to 1 (exclusive), 0 settling without overshoot, above 0 overshooting.
- `typography(role: str) -> Optional[tokens.TypeStyle]`: An MD3 type role with the theme's `typography:` overrides, or `None` for an unknown role.

**Constants**

- `DURATIONS` = `dict of 16`
- `EASINGS` = `dict of 8`

## Tokens

`tesserae.tokens`: MD3's colour, type, shape and motion tokens.

### `TypeStyle`

```python
class TypeStyle(
    font_family: str,
    font_weight: float,
    font_size: float,
    line_height: float
) -> None
```

TypeStyle(font_family: 'str', font_weight: 'float', font_size: 'float', line_height: 'float')

### `baseline_scheme`

```python
baseline_scheme() -> dict[str, RGBA]
```

Every role, for widgets with no theme: the scheme MD3's baseline seed (#6750A4) generates, with MD3's published `BASELINE` values over it where they differ.

### `color_scheme`

```python
color_scheme(seed: RGBA, dark: bool = False, contrast: float = 0.0) -> dict[str, RGBA]
```

Every MD3 role for `seed`, light or dark. `contrast` is MD3's contrast level, from -1 (less) through 0 (the standard) to 1 (the most): the roles for a user who asked the OS for more contrast.

### `elevation`

```python
elevation(name: str) -> Optional[float]
```

The level (0 to 5) of the MD3 elevation token `name`, or `None` if it isn't one.

### `elevation_shadows`

```python
elevation_shadows(level: float) -> list[Shadow]
```

MD3 elevation `level` (0–5, fractional allowed) as a `shadows` list, `(color, offset_x, offset_y, blur, spread)`: `tre`'s key shadow (30% black) first, so it paints on top, then its ambient shadow (15%). Level 0 is no shadow.

### `parse_color`

```python
parse_color(raw: str) -> RGBA
```

A colour string as `tre` parses it: hex (`#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`), a CSS colour name, `transparent`, or `rgb()`/`rgba()`/`hsl()`/`hsla()` in CSS Color 4's comma or space syntax with an optional alpha, and CSS's wide-gamut functions (`color()`, `lab()`, `lch()`, `oklab()`, `oklch()`, `hwb()`), clipped into sRGB. Raises `ValueError`.

### `resolve_scheme`

```python
resolve_scheme(
    theme_seed: Optional[RGBA],
    dark: bool,
    default_theme: Optional[dict[str, Any]],
    custom_theme: Optional[dict[str, Any]],
    contrast: float = 0.0
) -> Optional[dict[str, RGBA]]
```

The scheme a view resolves roles against, by `tre`'s `View` rules: the seed is `theme_seed`, else the custom theme's `seed:`, else the default theme's; `colors:` overrides apply default theme first, then custom. `None` when there's no seed at all: roles then don't resolve, as in `tre`.

### `shape`

```python
shape(name: str) -> Optional[float]
```

The corner radius of the MD3 shape token `name` (`"small"`, `"medium"`, ...), or `None` if it isn't one.

### `type_style`

```python
type_style(role: str) -> Optional[TypeStyle]
```

The font size, weight, line height and tracking of the MD3 type role `role`, or `None` if it isn't one.

**Constants**

- `BASELINE` = `dict of 24`
- `ELEVATION_LEVELS` = `dict of 6`
- `ROLES` = `tuple of 49`
- `SHAPES` = `dict of 6`
- `TYPE_SCALE` = `dict of 15`

## Widgets

`tesserae.widgets`: One function per MD3 widget, called against a window.

### `accordion_header`

```python
accordion_header(
    window: 'Window',
    title: str,
    expanded: bool = False,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

An accordion header: a title and a chevron that turns over when `.expanded` (a `Signal`) is on. A click, Enter or Space toggles it; `.on_change(fn)` hears the user's toggles.

### `badge`

```python
badge(
    window: 'Window',
    label: str | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's badge: a 6 px `error` dot when `label=None`, otherwise a 16 px pill with a `label_small` `on_error` label (`width` defaults to fit it).

### `button`

```python
button(
    window: 'Window',
    label: str,
    width: float,
    height: float,
    variant: str = 'filled',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    corner_radius: float | None = None,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

MD3's button. `variant`: elevated, filled, filled_tonal, outlined or text.

### `button_group`

```python
button_group(
    window: 'Window',
    labels: list[str],
    width: float,
    height: float,
    variant: str = 'filled',
    x: float | None = None,
    y: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[int], Any] | None = None
) -> Widget
```

MD3's button group: one button per label, `width`x`height`, 8 px apart; parts `b0`, `b1`, ... While one is pressed, its corners tighten and it grows 12 px, its neighbours sharing the loss, and it all comes back on release -- the intent of `tre`'s, whose reflow compounded and never restored.

### `card`

```python
card(
    window: 'Window',
    width: float,
    height: float,
    variant: str = 'elevated',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

MD3's card: elevated, filled or outlined. Content-free: add to `.node`.

### `carousel`

```python
carousel(
    window: 'Window',
    width: float,
    height: float,
    layout: str = 'multi_browse',
    items: Optional[list[Any]] = None,
    x: float | None = None,
    y: float | None = None,
    *,
    label: str = 'Carousel',
    theme: 'Theme | None' = None
) -> Widget
```

MD3's carousel: a clip holding items 16 px in, 8 apart and 8 above and below, each masked to 28 px corners (`extra_large`) on `surface_container_highest`. `hero` and `multi_browse` snap through large/medium/small slots (`small` 56, `medium` 112, `large` what's left), items before the current one small; moving blends the widths.

### `checkbox`

```python
checkbox(
    window: 'Window',
    background: tuple[int, int, int, int],
    width: float,
    height: float,
    checked: bool = False,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any
) -> controls.Checkbox
```

MD3's checkbox, `width`×`height` its touch target. A click, Space or Enter toggles it; `.checked` is its state.

### `chip`

```python
chip(
    window: 'Window',
    label: str,
    width: float,
    variant: str = 'assist',
    icon: str | None = None,
    selected: bool = False,
    removable: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None,
    on_remove: Callable[[], Any] | None = None
) -> Widget
```

MD3's chip: assist, filter, input or suggestion, 32 px tall, with an optional leading `icon`.

### `circular_progress`

```python
circular_progress(
    window: 'Window',
    size: float = 48.0,
    value: Optional[float] = 0.0,
    x: float | None = None,
    y: float | None = None,
    foreground: tuple[int, int, int, int] | None = None,
    **kwargs: Any
) -> controls.CircularProgress
```

MD3's circular progress; `value=None` spins indeterminately.

### `date_picker_day`

```python
date_picker_day(
    window: 'Window',
    day: int,
    selected: bool = False,
    today: bool = False,
    outside_month: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    on_click: Any = None,
    theme: Any = None
) -> Any
```

MD3's date-picker day: a 48 px target holding a 40 px circle with a `body_large` number. Selected, the circle is `primary` with `on_primary`; today (unselected) is outlined in `primary`; outside the month the number is `on_surface_variant`.

### `dialog`

```python
dialog(
    window: 'Window',
    headline: str,
    supporting_text: str,
    width: float,
    height: float,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    actions: list[tuple[str, Optional[Callable[[], Any]]]] | None = None,
    theme: 'Theme | None' = None
) -> overlays.Dialog
```

MD3's dialog (`tesserae.overlays.Dialog`). `open()` it; Escape or an action closes it.

### `divider`

```python
divider(
    window: 'Window',
    length: float,
    orientation: str = 'horizontal',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's divider: a 1 px `outline_variant` line `length` long. `border_color`/`border_width` recolour or thicken it.

### `extended_fab`

```python
extended_fab(
    window: 'Window',
    label: str,
    width: float,
    icon: str | None = None,
    variant: str = 'primary',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

MD3's extended FAB: an optional leading icon and a label, 56 px tall.

### `fab`

```python
fab(
    window: 'Window',
    icon: str,
    size: str = 'default',
    variant: str = 'surface',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    label: str | None = None,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

MD3's floating action button. `size`: small (40), default (56) or large (96, with a 36 px icon).

### `graph_node`

```python
graph_node(
    window: 'Window',
    graph: 'Widget',
    label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> 'Widget'
```

A node in a `node_graph`: a `surface_container_high` card with 12 px corners and an `outline_variant` border, a 32 px `title_small` title bar (`surface_container_highest`) over its body, at `x`, `y` in the graph's coordinates. Drag it to move it (its edges follow); focused, the arrow keys move it 8 px.

### `icon`

```python
icon(
    window: 'Window',
    name: str,
    foreground: tuple[int, int, int, int],
    size: float,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: 'Theme | None' = None,
    label: str | None = None
) -> 'Widget'
```

One of Tesserae's icons (`tesserae.icons`: home, search, menu, close, check, arrow_back, add, settings, expand_more, remove, arrow_forward, chevron_right), `size` square in `foreground`. It is Tesserae's own Icon.

### `icon_button`

```python
icon_button(
    window: 'Window',
    icon: str,
    size: float = 40.0,
    variant: str = 'standard',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    label: str | None = None,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

MD3's icon button. `variant`: standard, filled, filled_tonal or outlined.

### `image`

```python
image(
    window: 'Window',
    path: str,
    width: float,
    height: float,
    fit: str = 'fill',
    x: float | None = None,
    y: float | None = None,
    *,
    label: str | None = None
) -> 'Widget'
```

An image from a file, `width`x`height`, `fit` cover, contain or fill. Tesserae decodes the file (Pillow) and builds the node itself (`window.create("image")` with the pixels).

### `svg`

```python
svg(
    window: 'Window',
    source: 'str | Path | bytes',
    width: float | None = None,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    *,
    color: str | None = None,
    base: 'str | Path | None' = None,
    label: str | None = None
) -> 'Widget'
```

An SVG drawn by the engine: `source` is a `.svg` or `.svgz` file, or the document's text or bytes. It is scaled to fit `width` by `height`, or one of them if the other is left out.

### `linear_progress`

```python
linear_progress(
    window: 'Window',
    width: float,
    height: float = 4.0,
    value: Optional[float] = 0.0,
    x: float | None = None,
    y: float | None = None,
    foreground: tuple[int, int, int, int] | None = None,
    **kwargs: Any
) -> controls.LinearProgress
```

MD3's linear progress; `value=None` sweeps indeterminately.

### `link`

```python
link(
    window: 'Window',
    content: str,
    width: float,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

A link: `body_large` text in `primary`, `role="link"`, a Tab stop that Enter follows (`on_click`).

### `list_`

```python
list_(
    window: 'Window',
    items: list[Any],
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

Lays out `list_item(...)`s (or any nodes) as MD3's list: a column `width` wide. The items move into it.

### `list_item`

```python
list_item(
    window: 'Window',
    headline: str,
    leading_icon: str | None = None,
    trailing_icon: str | None = None,
    supporting_text: str | None = None,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None
) -> Widget
```

One MD3 list row: a `body_large` headline, 56 px tall, or 72 with `supporting_text` (`body_medium`, `on_surface_variant`) under it; 24 px `on_surface_variant` icons either side. Parts: `headline`, `supporting`, `leading`, `trailing`.

### `loading_indicator`

```python
loading_indicator(
    window: 'Window',
    size: float = 48.0,
    foreground: tuple[int, int, int, int] | None = None,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any
) -> controls.LoadingIndicator
```

MD3's loading indicator: a shape morphing forever.

### `menu`

```python
menu(
    window: 'Window',
    items: list[Any],
    width: float = 200.0,
    *,
    theme: 'Theme | None' = None
) -> overlays.Menu
```

MD3's menu (`tesserae.overlays.Menu`) of `menu_item(...)`s or `(label, fn)` pairs. `open(anchor)` below a node, `open_at(x, y)`, or `attach_context(node)` for a right-click.

### `menu_item`

```python
menu_item(
    window: 'Window',
    label: str,
    icon: str | None = None,
    submenu: bool = False,
    width: float = 200.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    on_click: Callable[[], Any] | None = None,
    theme: 'Theme | None' = None
) -> Widget
```

One of MD3's 48 px menu items, for `menu(...)`: a `label_large` label, an optional 24 px leading `icon`, and a trailing chevron when `submenu`. `on_click` runs when it's chosen (the menu closes).

### `navigation_drawer`

```python
navigation_drawer(
    window: 'Window',
    labels: list[str],
    icons: list[str],
    selected: int | None = None,
    modal: bool = False,
    width: float = 360.0,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's navigation drawer: `surface_container_low`, 12 px in, each item 56 px with a 24 px icon and a `label_large` label; the selected one a full-width `secondary_container` pill. `modal=True` is the modal drawer's look (rounded on its end side); open it as an overlay with `tesserae.overlays.NavigationDrawer`.

### `navigation_rail`

```python
navigation_rail(
    window: 'Window',
    labels: list[str],
    icons: list[str],
    selected: int | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    style: dict[str, Any] | None = None
) -> Widget
```

MD3's navigation rail: 80 px wide on `surface`, each item a 24 px icon over a `label_medium` label; the selected item's icon sits in a 56x32 `secondary_container` pill, in `on_secondary_container`. `.selected`, `.on_change(fn)`; the up and down arrows move it.

### `node_graph`

```python
node_graph(
    window: 'Window',
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> 'Widget'
```

A node graph's viewport: a clipped `surface_container_low` area whose content pans and zooms. Drag the background to pan; the wheel zooms about the pointer (`ZOOM_RANGE`).

### `pagination`

```python
pagination(
    window: 'Window',
    page_count: int,
    current: int = 0,
    x: float | None = None,
    y: float | None = None,
    *,
    max_visible: int = 7,
    theme: 'Theme | None' = None
) -> Widget
```

Previous, a numbered button per page, and next: 40 px circles 4 px apart, `label_large` numbers in `on_surface_variant`, the current page `primary` with an `on_primary` number. `.current` is a `Signal` (0-based) and `.on_change(fn)` hears the user's moves.

### `period_selector`

```python
period_selector(
    window: 'Window',
    selected: str = 'AM',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: Any = None
) -> Any
```

MD3's AM/PM period selector: 52x80, two 40 px halves in a 1 px `outline` frame with 8 px corners; the selected half `tertiary_container`/`on_tertiary_container`, the other `on_surface_variant`. `.period` (`"AM"`/`"PM"`) is a `Signal`; a click, Enter or the arrow keys switch it; `.on_change(fn)` hears the user's switches.

### `popover`

```python
popover(
    window: 'Window',
    supporting_text: str,
    subhead: str | None = None,
    width: float = 312.0,
    *,
    actions: list[tuple[str, Optional[Callable[[], Any]]]] | None = None,
    anchor: Any = None,
    theme: 'Theme | None' = None
) -> overlays.Popover
```

MD3's rich tooltip, `tre`'s popover (`tesserae.overlays.Popover`). `open(anchor)` it, or `attach(anchor)` (or `anchor=`) to open and close it on the anchor's click; an outside press, Escape or an action closes it.

### `radio_button`

```python
radio_button(
    window: 'Window',
    size: float = 48.0,
    selected: bool = False,
    x: float | None = None,
    y: float | None = None,
    group: Optional[controls.RadioGroup] = None,
    **kwargs: Any
) -> controls.RadioButton
```

MD3's radio button, `size` its touch target; pass a shared `controls.RadioGroup()` as `group=` for buttons that exclude each other.

### `search_bar`

```python
search_bar(
    window: 'Window',
    placeholder: str,
    width: float,
    leading_icon: str | None = 'search',
    trailing_icons: list[str] | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's search bar: a 56 px `surface_container_high` pill with elevation, a leading icon (`on_surface`), a `body_large` field whose `placeholder` is hint text in `on_surface_variant`, and trailing icon buttons (`on_surface_variant`). `.query` is a `Signal` of what's typed; `.on_query(fn)` hears each change.

### `search_view`

```python
search_view(
    window: 'Window',
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    bar: Widget | None = None,
    results: list[tuple[str, Optional[Callable[[], Any]]]] | None = None,
    theme: 'Theme | None' = None
) -> 'SearchView'
```

MD3's docked search view (`tesserae.overlays.SearchView`): the results panel under a `search_bar`, `height` its most. Give it the `bar` and it opens and closes with it; `set_results([(text, fn)])`.

### `segmented_button`

```python
segmented_button(
    window: 'Window',
    labels: list[str],
    width: float | None = None,
    height: float = 40.0,
    selected: 'int | list[int] | None' = None,
    multi: bool = False,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's outlined segmented button: equal segments in one 1 px `outline` pill, 1 px dividers between them, `label_large` labels in `on_surface`. A selected segment is `secondary_container` with an 18 px check before its `on_secondary_container` label.

### `side_sheet`

```python
side_sheet(
    window: 'Window',
    width: float = 360.0,
    height: float | None = None,
    modal: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> 'Widget | overlays.SideSheet'
```

MD3's side sheet. `modal=True` is `tesserae.overlays.SideSheet` (an overlay: `open()` it); otherwise a standard sheet, a `surface` panel in the layout.

### `slider`

```python
slider(
    window: 'Window',
    background: tuple[int, int, int, int],
    width: float,
    height: float,
    value: float = 0.0,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any
) -> controls.Slider
```

MD3's slider; `value` in 0.0..=1.0 unless `min=`/`max=` say otherwise. Dragging and the arrow keys set `.value`.

### `snackbar`

```python
snackbar(
    window: 'Window',
    text: str,
    width: float,
    action_label: str | None = None,
    closable: bool = False,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    on_action: Callable[[], Any] | None = None,
    duration: int | None = 4000,
    theme: 'Theme | None' = None
) -> overlays.Snackbar
```

MD3's snackbar (`tesserae.overlays.Snackbar`). `open()` it; it hides itself after `duration` ms (`None` keeps it).

### `spin_box`

```python
spin_box(
    window: 'Window',
    value: float | str = 0,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any
) -> controls.SpinBox
```

A number field between − and + buttons (`min=`, `max=`, `step=`). `value` may be a number or its text, as `tre`'s took.

### `splitter`

```python
splitter(
    window: 'Window',
    first: Any,
    second: Any,
    width: float,
    height: float,
    orientation: str = 'horizontal',
    position: float = 0.5,
    x: float | None = None,
    y: float | None = None,
    *,
    label: str = 'Resize panes',
    theme: 'Theme | None' = None
) -> Widget
```

Two panes and the handle between them: `first` and `second` (nodes or widgets) share `width` (a `horizontal` splitter) or `height` (`vertical`) less the 16 px handle, `first` getting `.position` (a `Signal`, 0..1) of it. The handle holds MD3's 4x48 `outline` drag handle, shows a `col_resize` (or `row_resize`) cursor, and is a focusable `role="slider"`: dragging it (with pointer capture) puts the split under the pointer, clamped, at once; the arrow keys move it by 5%, Home and End to the ends.

### `split_button`

```python
split_button(
    window: 'Window',
    label: str,
    width: float,
    height: float,
    variant: str = 'filled',
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    on_click: Callable[[], Any] | None = None,
    on_menu: Callable[[], Any] | None = None
) -> Widget
```

MD3's split button: a `leading` action and a `trailing` chevron, parts of the returned `Widget`. While it's hovered, the corners where the two meet tighten, as `tre`'s did.

### `status_bar`

```python
status_bar(
    window: 'Window',
    text: str,
    width: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    style: dict[str, Any] | None = None
) -> Widget
```

A window-bottom status strip: 24 px of `surface_container` with `label_small` text in `on_surface_variant`, announced politely when its text changes. `style` is laid over its own: `{height: 32}`, `background`, ...

### `switch`

```python
switch(
    window: 'Window',
    width: float = 52.0,
    height: float = 48.0,
    selected: bool = False,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any
) -> controls.Switch
```

MD3's switch, `width`×`height` its touch target (the track is MD3's 52×32); `.selected` is its state.

### `tabs`

```python
tabs(
    window: 'Window',
    labels: list[str],
    icons: list[str] | None = None,
    selected: int | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's primary tabs: 48 px tall, or 64 with `icons`; the labels `title_small`, `primary` when selected and `on_surface_variant` otherwise; a 3 px `primary` indicator under the selected label that slides to a new one; a 1 px `surface_variant` divider below. `.selected` (a `Signal`), `.on_change(fn)`; the left and right arrows move the selection.

### `text`

```python
text(
    window: 'Window',
    content: str,
    typography_role: str = 'body_medium',
    color: str = 'on_surface',
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

Plain text in a type role and a colour of the theme: `color` is a colour role (`on_surface` by default) or any colour string. `.content` is a `Signal`; setting it re-measures the text in its resolved font, keeping `width` when one was given.

### `time_input_field`

```python
time_input_field(
    window: 'Window',
    value: int | str = 0,
    unit: str = 'hour',
    x: float | None = None,
    y: float | None = None,
    *,
    label: str | None = None,
    theme: Any = None
) -> Any
```

MD3's time input field: 96x72, `surface_container_highest` with 8 px corners and a centred `display_medium` numeral in `on_surface`; focused, `primary_container` with a 2 px `primary` outline. `unit` is `"hour"` (0-23) or `"minute"` (0-59).

### `time_picker_dial`

```python
time_picker_dial(
    window: 'Window',
    hour: int = 0,
    minute: int = 0,
    size: float = 256.0,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any
) -> 'controls.TimePickerDial'
```

MD3's time picker dial (a Tesserae control): `.hour`, `.minute` and `.mode` are `Signal`s.

### `toolbar`

```python
toolbar(
    window: 'Window',
    variant: str = 'docked',
    orientation: str | None = None,
    vibrant: bool = False,
    width: float | None = None,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

MD3's toolbar, for action icon buttons: add them to `.node`. `docked` spans its width, 64 px tall; `floating` is a pill with elevation, horizontal or vertical.

### `tooltip`

```python
tooltip(
    window: 'Window',
    text: str,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    anchor: Any = None,
    theme: 'Theme | None' = None
) -> overlays.Tooltip
```

MD3's plain tooltip (`tesserae.overlays.Tooltip`). `attach(anchor)` (or `anchor=`) shows it on hover and keyboard focus.

### `top_app_bar`

```python
top_app_bar(
    window: 'Window',
    title: str,
    leading_icon: str | None = None,
    trailing_icons: list[str] | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None,
    window_controls: bool | None = None,
    style: dict[str, Any] | None = None
) -> Widget
```

MD3's small top app bar: 64 px of `surface`, a `title_large` title, an optional leading icon button (`on_surface`) and trailing ones (`on_surface_variant`), each 48 px. Parts: `title`, `leading`, `trailing0`, ...; wire them with `on_click(fn, part="leading")`.

### `tree_node`

```python
tree_node(
    window: 'Window',
    title: str,
    depth: int = 0,
    expanded: bool = False,
    leaf: bool = False,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: 'Theme | None' = None
) -> Widget
```

A tree row, indented 16 px plus 24 per `depth`, `role="treeitem"` at `level` `depth + 1`. A branch has a chevron (pointing right, down when `.expanded`), toggled by a click, Enter or Space, and set by the right and left arrows.

### `video`

```python
video(
    window: 'Window',
    width: float,
    height: float,
    fit: str = 'fill',
    x: float | None = None,
    y: float | None = None,
    *,
    label: str | None = None
) -> 'Widget'
```

A surface for video frames (an `image` node Tesserae builds). `video.frame(rgba, width, height)` shows a frame (RGBA bytes, `width*height*4` of them); frames can change size.

## Controls

`tesserae.controls`: MD3's stateful controls.

### `Checkbox`

```python
class Checkbox(
    window: Any,
    *,
    checked: bool = False,
    color: Optional[RGBA] = None,
    **kwargs: Any
) -> None  # extends Control
```

MD3's checkbox: an 18 px box with a 2 px outline, filled with `primary` and a check mark in `on_primary` when checked. `color` replaces `primary` (a fragment's `background:`).

Also has everything `Control` has.

### `Control`

```python
class Control(
    window: Any,
    *,
    theme: Optional[Theme] = None,
    label: Optional[str] = None,
    disabled: bool = False,
    listen: Optional[Listen] = None,
    size: Optional[float] = None,
    width: Optional[float] = None,
    height: Optional[float] = None
) -> None
```

The shared part of every control. A subclass sets `role`, builds its drawing in `_build()`, paints its state in `_paint(animate)` (reading its `Signal`s, so a change repaints), and acts in `_activate()` when the user clicks it or presses Space or Enter.

- `color(role: str) -> RGBA`: A colour role of this control's theme, or MD3's baseline.
- `destroy() -> None`: Stops the control and frees its nodes.
- `dispose() -> None`: Stops the control (its repainting and listeners) but leaves its node, for a caller about to free the tree it sits in.
- `on_change(fn: Callable[[Any], None]) -> Callable[[], None]`: Calls `fn(value)` after each change the user makes.
- `set_theme(theme: Theme) -> None`: Re-tints the control for `theme`, at once.

### `RadioButton`

```python
class RadioButton(
    window: Any,
    *,
    selected: bool = False,
    group: Optional[RadioGroup] = None,
    color: Optional[RGBA] = None,
    **kwargs: Any
) -> None  # extends Control
```

MD3's radio button: a 20 px ring, 2 px wide, in `on_surface_variant`, and when selected a `primary` ring with a 10 px `primary` dot that grows in. A click selects it (it never deselects itself); in a `group`, it deselects the others.

Also has everything `Control` has.

### `RadioGroup`

```python
class RadioGroup() -> None
```

Radio buttons that exclude each other, as HTML's same-`name` radios. Selecting one deselects the rest.

- `selected` *(property)*: The radio button that is selected, or `None`.

### `CircularProgress`

```python
class CircularProgress(window: Any, *, size: float = 48.0, **kwargs: Any) -> None  # extends Indicator
```

MD3's circular progress indicator: a 4 px `primary` arc in a 48 px box. Determinate, the arc runs clockwise from 12 o'clock for the value's share of the circle; indeterminate, the arc spins (one turn per 1568 ms) while it lengthens and shortens (666 ms each way).

Also has everything `Indicator` has.

### `LinearProgress`

```python
class LinearProgress(window: Any, *, width: float = 240.0, **kwargs: Any) -> None  # extends Indicator
```

MD3's linear progress indicator: a 4 px `surface_container_highest` track and a `primary` bar. Determinate, the bar fills to the value (sliding in over `medium1`); indeterminate, a bar 40% of the width sweeps across again and again (MD3's two-bar sweep, simplified to one).

Also has everything `Indicator` has.

### `LoadingIndicator`

```python
class LoadingIndicator(window: Any, *, size: float = 48.0, **kwargs: Any) -> None  # extends Indicator
```

MD3's loading indicator: a filled `primary` shape, 38 px in a 48 px box, morphing forever through a pentagon, a pill, a cookie and an oval, 650 ms per step, linear. These are the outlines `tre`'s MD3 handover defines (its `intended` pill and oval, not the diamonds `tre` drew).

Also has everything `Indicator` has.

### `Slider`

```python
class Slider(
    window: Any,
    *,
    value: float = 0.0,
    min: float = 0.0,
    max: float = 1.0,
    step: Optional[float] = None,
    width: float = 200.0,
    height: float = 48.0,
    color: Optional[RGBA] = None,
    **kwargs: Any
) -> None  # extends Control
```

MD3's slider: a 4 px track, `primary` up to the value and `surface_container_highest` after it, and a 20 px `primary` handle. Dragging the handle, or pressing anywhere on the track, sets the value (the pointer is captured, so a drag can leave the slider).

Also has everything `Control` has.

### `SpinBox`

```python
class SpinBox(
    window: Any,
    *,
    value: float = 0,
    min: Optional[float] = None,
    max: Optional[float] = None,
    step: float = 1,
    theme: Optional[Theme] = None,
    label: Optional[str] = None,
    disabled: bool = False,
    listen: Optional[Listen] = None
) -> None
```

A number field between − and + buttons, as `tre`'s spin box was (MD3 has no spin box of its own, so it's built from MD3's parts: two 40 px icon buttons and a filled field).

- `color(role: str) -> RGBA`: A colour role of this control's theme, or MD3's baseline.
- `destroy() -> None`: Stops the spin box and frees its nodes.
- `dispose() -> None`: Stops the spin box (its repainting and listeners) but leaves its nodes, for a caller about to free the tree it sits in -- as a view does with its controls.
- `on_change(fn: Callable[[Any], None]) -> Callable[[], None]`: Calls `fn(value)` after each change the user makes.
- `set_theme(theme: Theme) -> None`: Re-tints the spin box for `theme`, at once.

### `Switch`

```python
class Switch(
    window: Any,
    *,
    selected: bool = False,
    color: Optional[RGBA] = None,
    **kwargs: Any
) -> None  # extends Control
```

MD3's switch: a 52×32 track and a handle that slides across it. Off, the track is `surface_container_highest` with a 2 px `outline` border and a 16 px `outline` handle; on, it's `primary` with a 24 px `on_primary` handle.

Also has everything `Control` has.

### `TimePickerDial`

```python
class TimePickerDial(
    window: Any,
    *,
    hour: int = 0,
    minute: int = 0,
    mode: str = 'hour',
    auto_advance: bool = True,
    size: float = 256.0,
    **kwargs: Any
) -> None  # extends Control
```

MD3's time picker dial: a 256 px `surface_container_highest` face with the twelve hours (or the minutes, in fives) around it, a `primary` hand from the centre to a 48 px `primary` selector, which shows its number in `on_primary`.

Also has everything `Control` has.

**Constants**

- `DISABLED_CONTAINER` = `0.12`
- `DISABLED_CONTENT` = `0.38`
- `STATE_LAYER_SIZE` = `40.0`
- `TARGET_SIZE` = `48.0`

## Overlays

`tesserae.overlays`: Dialogs, menus, snackbars, tooltips, sheets, drawers.

### `Dialog`

```python
class Dialog(
    window: Any,
    headline: str,
    text: str,
    *,
    width: float = 312.0,
    height: float = 200.0,
    actions: Optional[list[tuple[str, Optional[Callable[[], Any]]]]] = None,
    theme: Optional[Theme] = None
) -> None  # extends Overlay
```

MD3's basic dialog (from its fragment): a `surface_container_high` panel with 28 px corners, a `headline_small` headline, `body_medium` supporting text, and text-button `actions` (`(label, fn)`, right- aligned, each closing it after calling `fn`), over a scrim. Modal: focus moves into it, and Escape closes it.

Also has everything `Overlay` has.

### `Menu`

```python
class Menu(
    window: Any,
    items: list[Any],
    *,
    width: float = 200.0,
    theme: Optional[Theme] = None
) -> None  # extends Overlay
```

MD3's menu: a `surface_container` panel, 4 px corners, elevation 2, 8 px top and bottom, of 48 px `label_large` items (`(label, fn)`, or a ready `menu_item` widget). Clicking or Enter on an item calls it and closes the menu; the up and down arrows move between items; an outside press or Escape closes it.

Also has everything `Overlay` has.

- `attach_context(node: Any) -> Callable[[], None]`: Makes this `node`'s context menu: a right-click opens it at the pointer.
- `open_at(x: float, y: float) -> None`: Opens it with its top-left corner at the window point `x`, `y`.

### `NavigationDrawer`

```python
class NavigationDrawer(
    window: Any,
    labels: list[str],
    icons: list[str],
    *,
    selected: Optional[int] = None,
    width: float = 360.0,
    theme: Optional[Theme] = None
) -> None  # extends _EdgeSheet
```

MD3's modal navigation drawer: `tesserae.widgets.navigation_drawer`'s drawer, `modal=True`, over a scrim at the window's start; it slides in, and Escape closes it. Choosing an item closes it.

Also has everything `_EdgeSheet` has.

- `set_theme(theme: Theme) -> None`: Re-tints it for `theme`, at once.

### `Overlay`

```python
class Overlay(window: Any, widget: Widget) -> None
```

The shared part: a `Widget` shown as a layer. `modal` blocks input beneath it and traps focus; `dismissible` closes it on `dismiss`.

- `close() -> None`: Hides it and calls the `on_close` functions.
- `is_open` *(property)*: Whether it is showing.
- `on_close(fn: Callable[[], Any]) -> Callable[[], None]`: Calls `fn()` each time it closes.
- `open(anchor: Any = None, placement: str = 'below') -> None`: Shows it, next to `anchor` (a node) on the `placement` side, or centred if there is none.
- `set_theme(theme: Theme) -> None`: Re-tints it for `theme`, at once.

### `Popover`

```python
class Popover(
    window: Any,
    supporting_text: str,
    *,
    subhead: Optional[str] = None,
    width: float = 312.0,
    actions: Optional[list[tuple[str, Optional[Callable[[], Any]]]]] = None,
    theme: Optional[Theme] = None
) -> None  # extends Overlay
```

MD3's rich tooltip, `tre`'s popover: a `surface_container` panel, 12 px corners, elevation 2, padded 16, with an optional `title_small` `subhead`, `body_medium` supporting text (both in `on_surface_variant`, the text wrapped to the width) and optional text-button `actions` (`(label, fn)`, in `primary`, each closing it after calling `fn`). It opens below its anchor and stays until an outside press, Escape or an action closes it; with actions, focus moves to the first.

Also has everything `Overlay` has.

- `attach(anchor: Any) -> Callable[[], None]`: Opens it below `anchor` when the anchor is clicked (or activated with Enter or Space), and closes it on the next.

### `SearchView`

```python
class SearchView(
    window: Any,
    *,
    bar: Optional[Widget] = None,
    width: float = 360.0,
    max_height: float = 336.0,
    results: Optional[list[tuple[str, Optional[Callable[[], Any]]]]] = None,
    max_results: int = 8,
    theme: Optional[Theme] = None
) -> None  # extends Overlay
```

MD3's docked search view: the results under a search bar, a `surface_container_high` panel with 28 px corners and elevation, of 56 px `body_large` rows (`role="menuitem"`), at most `max_height` tall.

Also has everything `Overlay` has.

- `on_query(fn: Callable[[str], Any]) -> Callable[[], None]`: Hears the bar's typing (`fn(text)`).
- `set_results(results: list[tuple[str, Optional[Callable[[], Any]]]]) -> None`: Replaces the rows with `results`, `(text, fn)` each.

### `SideSheet`

```python
class SideSheet(
    window: Any,
    *,
    width: float = 360.0,
    label: Optional[str] = None,
    theme: Optional[Theme] = None
) -> None  # extends _EdgeSheet
```

MD3's modal side sheet (from its fragment): a `surface_container_low` panel `width` wide at the window's end, with 16 px corners on its open side, over a scrim; it slides in, and Escape closes it. Put its content in `.panel`.

Also has everything `_EdgeSheet` has.

### `Snackbar`

```python
class Snackbar(
    window: Any,
    text: str,
    *,
    width: float = 344.0,
    action: Optional[str] = None,
    on_action: Optional[Callable[[], Any]] = None,
    closable: bool = False,
    duration: Optional[int] = 4000,
    theme: Optional[Theme] = None
) -> None  # extends Overlay
```

MD3's snackbar (from its fragment): 48 px of `inverse_surface`, `body_medium` `inverse_on_surface` text, an optional `action` text button (`inverse_primary`, calling `on_action` and closing) and an optional close icon button. It opens 24 px in and 72 px up from the bottom, isn't modal, ignores outside presses and Escape, and hides itself after `duration` ms (4000; `None` keeps it).

Also has everything `Overlay` has.

### `Tooltip`

```python
class Tooltip(
    window: Any,
    text: str,
    *,
    width: Optional[float] = None,
    theme: Optional[Theme] = None
) -> None  # extends Overlay
```

MD3's plain tooltip (from its fragment): 24 px of `inverse_surface` with `body_small` text, below its anchor. `attach(anchor)` shows it 500 ms after the anchor is hovered, or at once when it gets keyboard focus, and hides it when the pointer or focus leaves; an outside press or Escape closes it too.

Also has everything `Overlay` has.

- `attach(anchor: Any) -> Callable[[], None]`: Shows it for `anchor` on hover and keyboard focus.

## App shell

`tesserae.shell`: Bars, navigation and docked zones around the screens.

### `AppShell`

```python
class AppShell(
    window: Any,
    *,
    top_bar: Any = None,
    navigation: Any = None,
    status_bar: Any = None,
    zones: Optional[dict[str, float]] = None,
    dock: Optional[Dock] = None,
    center: bool = False,
    theme: Optional[Theme] = None,
    styles: Optional[dict[str, dict[str, Any]]] = None
) -> None
```

An app's frame: `top_bar`, `navigation` and `status_bar` (widgets or nodes, placed as they are), a `Dock` (`dock=`, or a new one) whose zones -- `zones={side: size}`, from left, right, top and bottom -- sit around `content`, where `App.use_shell` shows screens; with `center=True`, `content` is the dock's center zone and screens are its tabs. `size`, `set_size`, `layout`, `restore`, `set_theme`.

- `layout() -> dict[str, Any]`: Where each panel is (by title), which is shown, and each zone's size (`None` for the center, which takes what's left), as plain data.
- `restore(layout: dict[str, Any]) -> None`: Puts back a `layout()`: moves each titled panel into its zone, shows the one that was shown, and sizes the zones.
- `set_size(side: str, size: float) -> float`: Sets `side`'s zone size, clamped between `MIN_ZONE` and 70% of the area it sits in; returns the size it got.
- `set_style(part: str, style: Optional[dict[str, Any]]) -> None`: Styles `part` (`frame`, `content`, or a zone's side) with a node's `style:`; `None` or `{}` puts back what the shell itself had.
- `set_theme(theme: Theme) -> None`: Re-colours the shell, its dock and the widgets it was given.
- `show_screen(root: Any, title: str, previous: Any = None) -> None`: Shows a screen's root (`App.show` calls this): in `content`, replacing the screen there; or, with `center=True`, as a center tab, docked the first time and brought forward after.
- `size(side: str) -> float`: `side`'s zone size, px (its width, or height for top and bottom).

**Constants**

- `HANDLE_SPAN` = `16.0`
- `MIN_ZONE` = `120.0`
- `STEP` = `16.0`

## Shell files

`tesserae.shell_file`: Reading and building a `*_Shell.yaml`.

### `ShellSpecError`

```python
class ShellSpecError
```

A `*_Shell.yaml` that doesn't follow the schema.

### `bind_navigation`

```python
bind_navigation(
    app: Any,
    shell: Any,
    spec: dict[str, Any],
    path: Path,
    viewmodel: Any = None
) -> None
```

Choosing a rail item navigates to its screen, a step `back()` returns from, or calls the `on_navigate` method of `viewmodel` with the screen's name.

### `build_shell`

```python
build_shell(app: Any, spec: dict[str, Any]) -> Any
```

Builds `spec`'s `AppShell` on `app`'s window: its bars stretch across the window, its rail lists the navigation items' screens, and it takes the app's theme and follows it.

### `check_references`

```python
check_references(
    app: Any,
    spec: dict[str, Any],
    path: Path,
    viewmodel: Any = None
) -> None
```

Checks what the file names outside itself -- each panel's screen or view file, and `on_navigate`'s method -- before anything is built, so a mistake leaves the app as it was.

### `load_shell_spec`

```python
load_shell_spec(path: str | Path) -> dict[str, Any]
```

Reads and checks a `*_Shell.yaml`, returning its spec with every key filled in (`None`, `{}` or `False` for one it leaves out).

### `parse_shell_spec`

```python
parse_shell_spec(raw: Any, where: str = 'shell') -> dict[str, Any]
```

Checks a shell spec (the parsed YAML); `where` names it in errors.

### `place_panels`

```python
place_panels(app: Any, shell: Any, spec: dict[str, Any], path: Path) -> None
```

Docks each named panel in its zone: the screen registered under that name, or else the `<Name>_View.yaml` next to the shell file (with its `<Name>_ViewModel.py`, if any), loaded and registered under it.

### `reload_shell`

```python
reload_shell(
    app: Any,
    shell: Any,
    old: dict[str, Any],
    new: dict[str, Any],
    path: Path,
    viewmodel: Any = None
) -> list[str]
```

Applies an edited shell file in place and returns what it couldn't: the structural changes that need a restart. The bars, the rail, the zones and `center` are compared with the live shell; panels with the file as it was, so a panel the user dragged stays where it is unless the file moved it.

**Constants**

- `SHELL_SUFFIX` = `'_Shell.yaml'`

## Docking

`tesserae.docking`: Panels the user can drag between zones.

### `Dock`

```python
class Dock(window: Any, *, theme: Optional[Theme] = None) -> None
```

The docking of one window (see the module doc). `add_zone(side, size)` returns the zone's node to place in the layout (an `AppShell` places them); `add_panel(side, node, title)` docks a panel; `show`, `move`, `side_of`, `panels`, `shown`, `titles`, `shown_title`, `panel(title)`; `on_move(fn)` hears a panel moving, `fn(node, side)`; `set_theme(theme)` re-colours it.

- `add_panel(side: str, panel: Any, title: str) -> Any`: Docks `panel` (a node, or a widget's `.node`) in `side`'s zone, titled `title` on its tab, and shows it.
- `add_zone(side: str, size: float) -> Any`: Creates `side`'s zone -- a tab strip over the area that shows its selected panel -- `size` px wide (left, right) or tall (top, bottom), or filling what's left (center).
- `move(panel: Any, side: str) -> None`: Moves `panel` to `side`'s zone and shows it there, as a drag would, moving it between zones.
- `on_move(fn: Callable[[Any, str], Any]) -> Callable[[], None]`: Calls `fn(node, side)` when a panel moves zone.
- `panel(title: str) -> Optional[Any]`: The docked panel titled `title`, or `None` (for `AppShell.restore`).
- `panels(side: str) -> list[Any]`: `side`'s panels, in their tabs' order.
- `remove_panel(panel: Any) -> Any`: Undocks `panel`: its tab goes, and if it was shown the zone shows the next panel, else the previous.
- `set_theme(theme: Theme) -> None`: Re-colours the zones, tabs and highlight for `theme`, at once.
- `show(panel: Any) -> None`: Shows `panel` in its zone.
- `shown(side: str) -> Optional[Any]`: The panel `side`'s zone is showing, or `None` if it has none.
- `shown_title(side: str) -> Optional[str]`: The title of the panel showing in the `side` zone, or `None` if none is.
- `side_of(panel: Any) -> Optional[str]`: The side `panel` is docked on, or `None` if it isn't docked.
- `titles(side: str) -> list[str]`: `side`'s panel titles, in their tabs' order.

**Constants**

- `DRAG_THRESHOLD` = `4.0`
- `SIDES` = `('left', 'right', 'top', 'bottom', 'center')`
- `TAB_HEIGHT` = `48.0`

## Interaction

`tesserae.interaction`: State layer, ripple and focus ring.

### `Interaction`

```python
class Interaction(
    window: Any,
    node: Any,
    tint: RGBA,
    listen: Listen,
    ring_color: RGBA,
    surface: Any = None,
    ring_around: Any = None
) -> None
```

The state layer, ripple and focus ring on one `box` node: the layer and ripple tinted `tint`, the ring `ring_color`.

- `detach() -> None`: Removes the listeners, the layer and any ripples.
- `enabled` *(property)*: Whether the node shows state feedback (hover, focus, press); set it to turn that on or off.
- `opacity` *(property)*: The state layer's resting opacity for the current state.
- `refresh() -> None`: Follows the node's corners (and, for the ring, its size).
- `retint(tint: RGBA, ring_color: RGBA) -> None`: New colours (a theme change), for the layer, live ripples and ring.
- `ring_visible` *(property)*: Whether the focus ring is showing.
- `ripples` *(property)*: The live ripples' circle nodes, oldest first.
- `set_dragged(dragged: bool) -> None`: For widgets that drag: MD3's dragged state.

**Constants**

- `DRAGGED` = `0.16`
- `FOCUSED` = `0.1`
- `HOVERED` = `0.08`
- `PRESSED` = `0.1`

## Accessibility

`tesserae.a11y`: What a node tells assistive technology.

### `bind`

```python
bind(node: Any, **fields: Any) -> Callable[[], None]
```

Keeps `node`'s `label`, `hidden` or `level` up to date: each is a `Signal` or `Computed` (anything with `.get()`), a function of no arguments, or a plain value, and it's set now and again whenever what it read changes, checked as `describe` checks it (a wrong value raises, naming the field). `node` is a node, or a widget or control (its `.node`).

### `check`

```python
check(fields: dict[str, Any], where: str = '') -> dict[str, Any]
```

Checks `describe`'s fields and returns them as `tre` properties (`hidden` becomes `a11y_hidden`). Raises `ValueError` naming the field.

### `describe`

```python
describe(node: Any, **fields: Any) -> None
```

Sets what `node` tells assistive technology, for example `describe(node, role="switch", label="Wi-Fi", checked=True)`. Every field is checked before any is set.

### `on_action`

```python
on_action(
    node: Any,
    handlers: dict[str, Callable[[Any], Any]],
    listen: Callable[[Any, str, Callable[[Any], None]], Callable[[], None]] | None = None
) -> Callable[[], None]
```

Routes `node`'s `a11y_action` events to `handlers[action]`, each given the event (`event.value` carries `set_value`'s value). Returns a function that removes the routing.

**Constants**

- `ACTIONS` = `{'collapse', 'decrement', 'expand', 'increment', 'scroll_into_view', 'set_value'}`
- `BINDABLE` = `('label', 'hidden', 'level')`
- `LIVE` = `{'assertive', 'off', 'polite'}`
- `ROLES` = `frozenset of 23`

## Bindings

`tesserae.binding`: The `{{ expression }}` language.

### `BindingError`

```python
class BindingError
```

A binding that doesn't parse, or fails to evaluate. The message is `tre`'s.

### `Expression`

```python
class Expression(kind: str, value: Any = None, left: Any = None, right: Any = None) -> None
```

One node: `kind` is `Ident`, `Literal`, `Attr`, `Index`, `Call`, `Not` or `BinaryOp`.

### `Handle`

```python
class Handle(obj: Any, id: int) -> None
```

An opaque Python object inside an evaluation. `id` numbers the handles one evaluation made, in order, as `tre` does.

### `evaluate`

```python
evaluate(expr: Expression, viewmodel: Any) -> Any
```

Evaluates `expr` against `viewmodel` and returns the Python value: a primitive, or the object a handle stands for. Signal reads inside it are recorded on `tesserae.reactive`'s stack.

### `parse_binding`

```python
parse_binding(raw: str) -> Expression
```

Parses `"{{ expression }}"`. Raises `BindingError` with `tre`'s message if it isn't wrapped in `{{ }}` or doesn't parse.

### `value_debug`

```python
value_debug(value: Value) -> str
```

A value as `tre` prints it (`Int(3)`, `Str("a")`, `Handle(0)`).

## Fonts

`tesserae.fonts`: Registering font files.

### `register_font`

```python
register_font(path: str | Path) -> list[str]
```

Reads the font file at `path` and registers it with `tre`, process-wide. Returns the family names it contains -- the exact names to use as `font_family`.

## Icons

`tesserae.icons`: The built-in icon set.

### `icon_path`

```python
icon_path(name: str) -> str | None
```

The path data for `name`, or `None` if there's no such icon.

**Constants**

- `ICON_VIEW_BOX` = `(0.0, -960.0, 960.0, 960.0)`
- `ICONS` = `dict of 15`

## Logging

`tesserae.log`: Tesserae's log format.

### `configure_logging`

```python
configure_logging(
    level: str | int = 'INFO',
    *,
    sink: Any = sys.stderr,
    format: str = '<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>',
    capture_warnings: bool = True
) -> int
```

Sends log messages at `level` and above to `sink` (stderr by default) in Tesserae's format, and returns the loguru handler id.

**Constants**

- `DEFAULT_FORMAT` = `str of 112`

## Spec loading

`tesserae.spec`: Reading, expanding and watching view files.

### `ComponentError`

```python
class ComponentError
```

A `component:` reference that cannot be expanded, with the call chain that led to it.

### `ViewWatcher`

```python
class ViewWatcher(
    view: Any,
    path: str | Path,
    *,
    component_dirs: list[Path] | None = None,
    project: Any = None
) -> None
```

Watches every file `view` was built from and reloads it on change.

- `files` *(property)*: Every file currently being watched, resolved.
- `poll() -> bool`: Reloads the view if any watched file changed since the last poll.
- `running` *(property)*: Whether `start()`'s background thread is watching.
- `start(handle: Any) -> None`: Starts watching on a background thread.
- `stop(timeout: float = 5.0) -> None`: Stops the background thread and waits for it to finish.

### `expand_components`

```python
expand_components(
    yaml_text: str,
    *,
    component_dirs: list[Path] | None = None,
    base_dir: Path | None = None
) -> str
```

`expand_components_to_spec`, dumped back to YAML text -- for inspecting an expansion, or for `tre`'s own text-based `source=` path. Nothing on Tesserae's own `tre` handoff path uses this any more (`load_view`/`instantiate` pass the dict via `spec=`).

### `expand_components_to_spec`

```python
expand_components_to_spec(
    yaml_text: str,
    *,
    component_dirs: list[Path] | None = None,
    base_dir: Path | None = None,
    project: Any = None
) -> Any
```

Resolves every `include:` and expands every `component:` entry in `yaml_text`, returning the finished `WidgetSpec`-shaped dict with no `include:`/`component:`/`with:`/`params:`/`repeat:` keys remaining -- ready for `tesserae.View(spec)`, with no YAML-text round-trip.

### `load_stylesheet`

```python
load_stylesheet(path: str | Path) -> dict[str, Any]
```

Reads a stylesheet YAML file into the dict `tre`'s `stylesheet_spec=` takes.

### `load_theme`

```python
load_theme(path: str | Path) -> dict[str, Any]
```

Reads a theme YAML file into the dict `tre`'s `default_theme_spec=`/`custom_theme_spec=` take, for `load_view` or for switching themes later:

### `load_view`

```python
load_view(
    path: str | Path,
    *,
    component_dirs: list[Path] | None = None,
    **view_kwargs: Any
) -> Any
```

Reads `path`, resolves its `include:`s and expands its `component:` usage, and builds a Tesserae `View` from the result .
