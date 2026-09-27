# `App`

## `App`

**`App(width=480, height=320, title="Tesserae App", *, theme_seed=None, dark="system", default_theme=None, custom_theme=None, stylesheet=None)`**

(Each of `default_theme=`, `custom_theme=` and `stylesheet=` also has a
`*_spec=` twin that takes a dict instead of a file path.)

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
bound values kept. It **starts dark**, because `tre` 0.3.4 can't read the
OS's appearance until the first switch. `dark=True` or `dark=False` fixes
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

**`load_shell(path) -> AppShell`**

Builds the shell a `*_Shell.yaml` describes and uses it, as `use_shell`
does (M52): its top bar, navigation rail, status bar, docked zones and
center tabs. The bars stretch across the window, and everything follows
the app's theme. A file not named `*_Shell.yaml`, broken YAML, or a key
the schema doesn't have raises `tesserae.shell_file.ShellSpecError` (a
`ValueError`) naming the file and the key. See
[App Shell & Docking](../guide/app-shell.md#from-a-shell-file).

## `current`

**`current -> str | None`**

The name last passed to `show()`, or `None` before the first real
call.

## `run`

**`run(max_frames=None, *, hot_reload=False) -> None`**

The one blocking call -- opens the real window `show()` already built
and runs `tre`'s own real render loop. `max_frames` caps it (headless/
CI-safe); omit it for a real, interactive run. Raises `RuntimeError`
if called before `show()`.

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
[Hot Reload](../guide/hot-reload.md#components-added-at-run-time)).

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
