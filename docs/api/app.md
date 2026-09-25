# `App`

## `App`

**`App(width=480, height=320, title="Tesserae App", *, theme_seed=None, dark=False, default_theme=None, custom_theme=None, stylesheet=None)`**

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

The theme is app-wide rather than per screen because in `tre` a theme
belongs to the window. Building a view never themes the window, and
switching screens never changes it, so `show()` gives the window the
app's theme the first time it opens. Widgets created with
`tesserae.widgets` and hover/press tints use it.

## `set_theme_specs`

**`set_theme_specs(default_theme_spec, custom_theme_spec) -> None`**

Re-themes the running app in place: every view `load()` or
`build_view()` made, and the window. Views built later use the new
theme too. Both dicts are the complete new selection (`None` for none).
The seed and `dark` stay as given to `App(...)`. Bound values stay live.
If `tre` rejects the theme, it raises, and the app keeps its old theme.
Call it on the event-loop thread; `run(hot_reload=True)` calls it when a
theme file changes.

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
window, keeping its ViewModel and its own theme.

## `load`

**`load(view_path, viewmodel_cls, name=None, *, stylesheet=None, stylesheet_spec=None) -> (view, viewmodel)`**

Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it -- see
[Naming Convention](../guide/naming-convention.md). `name` defaults to
the shared prefix. The screen uses the app's theme, and its own
`stylesheet=` if given, otherwise the app's default. Returns the
constructed `(view, viewmodel)` pair.

## `show`

**`show(name) -> Window`**

Shows the view registered under `name` in the app's window, detaching
the one shown before, which stays alive with its state. Returns the
window, the same one every time.

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

`hot_reload=True` reloads every screen registered with `load()` while
the app runs, whenever its view file -- or anything it was built from --
changes on disk. See [Hot Reload](../guide/hot-reload.md). Screens given
to `register()` directly aren't watched, since Tesserae doesn't know
their file. The theme files given to `App(...)` are watched too, and an
edit re-themes the running app (see
[Hot Reload](../guide/hot-reload.md#theme-and-stylesheet-files)). So are
stylesheet files: the default from `App(stylesheet=)`, and each screen's
own `load(stylesheet=)` file.

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
