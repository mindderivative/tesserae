# `App`

## `App`

**`App(width=480, height=320, title="Tesserae App", *, theme_seed=None, dark="system", default_theme=None, custom_theme=None, stylesheet=None, state=None, decorations=True, resize_border=None, min_width=0, min_height=0, fullscreen=False, system_menu=False, icon=None, window_border=True)`**

(Each of `default_theme=`, `custom_theme=` and `stylesheet=` also has a
`*_spec=` twin that takes a dict instead of a file path.) `state=` is the
app's [shared state](../guide/apps-and-screens.md#shared-state), and the
last eight arguments are [the window's](#the-window).

`width`/`height`/`title` describe the one real window this `App`
creates and shows its screens in. A screen root with no size of its own
is sized to its content.

The theme arguments set **one theme for the whole app**, used by every
screen `load()` builds. `stylesheet=` is the **default stylesheet** for
every screen; `load(stylesheet=...)` replaces it for one screen. The
theme and default stylesheet files are read once, when the `App` is
created (a screen's own stylesheet file is read when that screen
loads), and `tre` is given only the parsed data. Passing a file and its `*_spec=` twin together raises
`ValueError`. See [Themes & Fonts](../guide/themes-and-fonts.md).

The theme is app-wide rather than per screen: every screen gets it, and
`app.theme` is it resolved (a `tesserae.Theme`). Widgets and controls
made with `tesserae.widgets` on `app.window` with no `theme=` take it and
follow it: `set_dark`, the OS's light and dark, and `set_theme_specs`
re-colour them with the screens, and roll them back with the screens if
one fails (M50). An explicit `theme=` pins a widget; a widget's
`destroy()` stops it following. Since M42 the window itself has
no theme: nothing `tre` draws reads one.

## The window

*0.3.0, on `tre` 0.5.0.1.* Each option is also a property, and can change
while the app runs. The [Custom Title Bars](../guide/custom-title-bars.md)
guide and [The window](../guide/apps-and-screens.md#the-window) explain
them; here is the reference.

| Property | |
| --- | --- |
| `decorations -> bool` | Whether the OS draws the title bar and borders. `False` leaves them to the app (on macOS the title bar stays, transparent, with the traffic lights). |
| `resize_border -> int` | Pixels along each edge that resize an undecorated window; `None` (unset) is 6 while undecorated and 0 otherwise. |
| `min_width`, `min_height -> int` | The smallest the user can resize the window to (0: no limit). |
| `fullscreen -> bool` | Whether the window fills its monitor, borderless. |
| `system_menu -> bool` | Whether a right-click on the title bar opens the OS's window menu (Windows, and Wayland compositors that have one). |
| `window_border -> bool` | Whether an undecorated window gets its 1 px border, in the theme's `outline_variant`; it hides while maximized or fullscreen and on macOS. Restyle it by its `window_border` class. |
| `platform -> str` | `"windows"`, `"macos"`, `"wayland"` or `"x11"`. |

**`set_icon(icon) -> None`** -- the window's icon from an image file (a
PNG, best square), or `None`. Shown on Windows and X11; Wayland and macOS
take it from the app's desktop entry or bundle, which
`tesserae build --installer` makes.

**Actions:** `minimize()`, `maximize()`, `restore()`,
`toggle_maximized()` and `close()`. Before `run()`, `minimize()` and
`maximize()` set how the window opens. `close()` closes it as the user's
close would, so `close_requested` fires first and a "save changes?" check
can cancel it.

**State**, as read-only [Computeds](../guide/reactivity.md) a binding or
an `Effect` can follow: `app.maximized`, `app.active` (the window has the
OS's focus), `app.titlebar_inset` (the `(height, width)` macOS's traffic
lights take, `(0, 0)` elsewhere) and `app.native_controls` (whether the OS
draws its own window buttons). Window buttons can call the actions with no
ViewModel method: `handlers: {on_click: window.close}`.

## `set_theme_specs`

**`set_theme_specs(default_theme_spec, custom_theme_spec) -> None`**

Re-themes the running app in place: every view `load()` or
`build_view()` made. Views built later use the new
theme too. Both dicts are the complete new selection (`None` for none).
The seed and the light/dark appearance stay as they are. Bound values stay live.
If `tre` rejects the theme, it raises, and the app keeps its old theme.
Call it on the event-loop thread; `run(hot_reload=True)` calls it when a
theme file changes.

## Light and dark

`dark="system"` (the default) follows the OS: when it switches between
light and dark, every screen is re-themed in place, with
bound values kept. It **starts in the OS's appearance** (M53): `tre`
0.3.5.2 reports it (`window.get("dark")`,
[`tre` #18](https://github.com/mindderivative/tre/issues/18)) at once on
Linux, and once the window opens on macOS and Windows, where the app
starts dark and `run()` switches on the first frame. Where the OS can't
say (headless), it starts dark. `dark=True` or `dark=False` fixes
the appearance, whatever the OS does.

**`set_dark(dark) -> None`** -- `True`/`False` switches to that
appearance now, and keeps it; `"system"` goes back to following the OS
from its next switch.

**`dark -> bool`** -- whether the dark scheme is showing now.
**`dark_mode -> bool | str`** -- `"system"`, or the fixed `True`/`False`.
**`theme -> tesserae.Theme`** -- the app's resolved theme, for the
current appearance.

## `set_stylesheet_spec`

**`set_stylesheet_spec(stylesheet_spec) -> None`**

Replaces the app's default stylesheet in place. Every screen using the
default is re-styled, and screens built later use the new one. Screens
given their own `stylesheet=` aren't touched. `None` means no
stylesheet. If `tre` rejects it, it raises, and every screen keeps its
old stylesheet. Call it on the event-loop thread;
`run(hot_reload=True)` calls it when the default stylesheet file changes.

## `build_view`

**`build_view(view_path, *, stylesheet=None, stylesheet_spec=None) -> View`**

Builds a view with the app's theme and stylesheet without registering
it -- for a screen you pass to `register()` yourself. `stylesheet=`
replaces the app's default for this view.

## `register`

**`register(name, view, viewmodel) -> None`**

Registers an already-loaded `view` and its already-`_attach`ed
`viewmodel` under `name`, for a later `show(name)` to display. Raises
`ValueError` if `name` is already registered, and `TypeError` if `view`
isn't a `tesserae.View`. Build the view with
[`build_view`](#build_view) to give it the app's theme and stylesheet; a
view built on its own (`tesserae.View(path)`) is rebuilt in the app's
window, keeping its ViewModel and its own theme. A view built from a file
either way keeps that file, so `run(hot_reload=True)` watches it (M48).

## `load`

**`load(view_path, viewmodel_cls, name=None, *, stylesheet=None, stylesheet_spec=None) -> (view, viewmodel)`**

Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it -- see
[Naming Convention](../guide/naming-convention.md). `name` defaults to
the shared prefix. The screen uses the app's theme, and its own
`stylesheet=` if given, otherwise the app's default. Returns the
constructed `(view, viewmodel)` pair.

## `show`

**`show(name) -> Window`**

Shows the view registered under `name` in the app's window -- or in
its shell's content, after `use_shell` -- detaching the one shown
before, which stays alive with its state. Returns the window, the same
one every time.

## `window`

**`window -> Window`**

The app's one window, which exists from the start: build widgets, a
`Dock` or an `AppShell` on it.

## `use_shell`

**`use_shell(shell) -> None`**

Shows screens inside `shell.content` from now on (M45): an
`AppShell(app.window, ...)` -- a top app bar, navigation, docked panels
and a status bar around the screens. A screen already showing moves into
it. A shell built on another window is a `ValueError`.

## `load_shell`

**`load_shell(path, viewmodel=None) -> AppShell`**

Builds the shell a `*_Shell.yaml` describes and uses it, as `use_shell`
does (M52): its top bar, navigation rail, status bar, docked zones,
center tabs and panels. A panel is the screen registered under its name,
or else `<Name>_View.yaml` (and `<Name>_ViewModel.py`) next to the shell
file, loaded and registered under it. Choosing a rail item calls
`show(screen)`, or the `on_navigate` method of `viewmodel`, and `show`
moves the rail's selection. `show` on a docked panel brings its tab
forward. The bars stretch across the window, and everything follows
the app's theme. A file not named `*_Shell.yaml`, broken YAML, or a key
the schema doesn't have raises `tesserae.shell_file.ShellSpecError` (a
`ValueError`) naming the file and the key. See
[App Shell & Docking](../guide/app-shell.md#from-a-shell-file).

## `screen`

**`screen(name) -> (view, viewmodel)`**

The view and ViewModel registered under `name`: by `register`, by
`load`, or by a shell file's panels (M52), whose ViewModels the app
builds. `viewmodel` is `None` for a view with none. An unknown name is a
`KeyError`, as for `show`.

## Routes and history

A screen navigated to is a step in a history, as in a browser; see
[Routes and deep links](../guide/apps-and-screens.md#routes-and-deep-links).

**`navigate(name, /, **params) -> Window`** -- shows the screen `name` as
a step in the history, after calling its ViewModel's
`on_navigated(params)` if it has one. Forward entries are dropped, and
navigating to the entry already showing does nothing.

**`route(pattern, name) -> None`** -- adds a route: a pattern such as
`"notes/{id}"` (`{param}` is a string, `{param:int}` an `int`) for the
screen registered under `name`. Routes are tried in the order added.

**`navigate_to(route) -> Window`** -- navigates to the screen the first
matching route names, with the params read from `route` (a deep link such
as `"notes/42"`). `KeyError` if none matches.

**`back() -> bool`**, **`forward() -> bool`** -- move through the history,
calling the entry's `on_navigated`; they return whether they moved.

**`location -> str | None`** -- the screen showing, as a route string (to
save where the user was), or `None` if no route reads its params back
exactly.

## `App.of`

**`App.of(view) -> App | None`** -- the live app whose window `view` (a
view, a component or a window) is on, or `None`: for a ViewModel's
constructor, before `super().__init__(view)` gives it `self.app`.

## `watch_component`

**`watch_component(path) -> None`** -- while `run(hot_reload=True)` runs,
watches a component file and reloads every live instance of it
(`tesserae.instantiate` calls it). Outside hot reload it does nothing.

## `current`

**`current -> str | None`**

The name last passed to `show()`, or `None` before the first real
call.

## `run`

**`run(max_frames=None, *, hot_reload=False) -> None`**

The one blocking call -- opens the real window and runs `tre`'s own real
render loop, showing the screen `show()` made current and any nodes you
added to `app.window.root` by calls. `max_frames` caps it (headless/
CI-safe); omit it for a real, interactive run. Raises `RuntimeError` if
the window has neither (before 0.3.1, if `show()` hadn't been called).

`hot_reload=True` reloads every screen built from a file while the app
runs -- one `load()` made, or one built with `build_view()` and given to
`register()` (M48) -- whenever its view file, or anything it was built
from, changes on disk. See [Hot Reload](../guide/hot-reload.md). A
screen built from a spec dict has no file, so it isn't watched (the log
names it). The theme files given to `App(...)` are watched too, and an
edit re-themes the running app (see
[Hot Reload](../guide/hot-reload.md#theme-and-stylesheet-files)). So are
stylesheet files: the default from `App(stylesheet=)`, and each screen's
own `load(stylesheet=)` file. Components built with `tesserae.instantiate`
are watched by their file, one watcher per file for all its live
instances, including ones added while the app runs (M51; see
[Hot Reload](../guide/hot-reload.md#components-added-at-run-time)). A
shell file from `load_shell` is watched too, and an edit is applied in
place where it can be; a structural one is logged as needing a restart
(M52; see [Hot Reload](../guide/hot-reload.md#the-shell-file)).

## `thread_handle`

**`thread_handle() -> tre.LoopHandle`**

The one object that may be used from another thread. Views, windows and
the app itself may only be used from the thread that created them; a
background thread calls `handle.call_soon(fn)` instead, and `fn` (no
arguments) runs on the event-loop thread at the next frame, waking the
loop if it's idle. Callables run in the order they were queued, and one
queued before `run()` runs on the first frame.

```python
handle = app.thread_handle()

def on_download_done(result):          # called on a worker thread
    handle.call_soon(lambda: viewmodel.status.set(result))
```
