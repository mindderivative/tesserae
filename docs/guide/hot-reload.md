# Hot Reload

`App.run(hot_reload=True)` applies an edit to a running app, and keeps its state. What it watches depends on how a file was
opened:

| File | When you save it |
| --- | --- |
| a theme: `App(custom_theme=)`, `App(default_theme=)` | every view is re-themed in place ([below](#theme-and-stylesheet-files)) |
| a view the app opened with `app.load` (the older syntax), and the fragments and images it was built from | the screen is rebuilt in place, its ViewModel and bindings kept |
| a view the app opened with `app.open_view` or `app.open_window`, any view it calls, and the pictures it draws | the view is composed again in place: its ViewModel, the nodes that keep their name or position, and their `state:` stay ([below](#a-view-written-with-widget-nodes)) |
| the app's stylesheet of rules (`App(stylesheet=)`, `widget:` rules) | not applied while the app runs: run it again |

The log says what is watched when it starts, and names a screen it does not watch:
`hot reload: screen 'Tasks' isn't watched -- it was built from a spec, not a file`.

## A view written with `widget:` nodes

```python
app = App()
app.bind(CounterViewModel)
app.open_view("Counter")
app.show("Counter")
app.run(hot_reload=True)
```

Save `Counter_View.yaml`, a view it calls (and the views those call), or a picture it draws, and the window shows the change at once. The view is
composed again from the new files and drawn over the old: the ViewModel and its Signals are the same ones, so the counter keeps its count; a node
that keeps its place (its `name`, or its position, with the `key` of a row under `for:`) keeps its `state:`; a handler is wired again. A view
the file starts to call is watched from then on. The views Tesserae ships are not watched. A view opened while the app runs is watched too, and
so is every window `open_window` opens.

A mistake leaves the window as it was and is logged as an `ERROR` naming the file: invalid YAML, a call with a wrong parameter, a name that is
not defined, or a widget the engine rejects. Fix the file and save.

Not reloaded: the app's own stylesheet of rules (`App(stylesheet=)`), the Python files (a ViewModel's code is not reloaded), and a `widget: Window`
view's window options (its size, title and flags are read when it opens).

## In an app (the older syntax)

```python
app = App()
app.load("Home_View.yaml", HomeViewModel)    # a view in the older syntax
app.show("Home")
app.run(hot_reload=True)
```

Every screen built from a file by `App.load()` is watched while the app runs, and so is one built with `app.build_view(...)` and
given to `App.register()` (the view keeps the file it came from). Save a
change and it appears in the window straight away, the screen's
ViewModel and bindings kept. A screen with no file isn't watched, and the log says so when hot reload starts.

An edit reaches a window left alone: the watcher runs on its own thread,
and other Python threads run while a window sits idle. See the
[Python API](../api/python.md) for `App.run`.

Behind the scenes each screen gets a `ViewWatcher` on a background
thread. It listens for file-change events (using
[`watchfiles`](https://watchfiles.helpmanual.io/)), rebuilds the view
there -- so file reading and component expansion never slow the UI --
and hands only the final update to the event loop through
`App.thread_handle()` ([Python API](../api/python.md)).

## When an edit is broken

If a reload fails -- invalid YAML, an unknown component, a widget `tre`
rejects -- Tesserae logs one `ERROR` line naming the file and the error
(the traceback is at `DEBUG`), and the screen stays as it was. The app
and the watcher keep running: fix the file, save, and it reloads. Each
reload that works is logged at `INFO`. See [Logging](logging.md).

## Using `ViewWatcher` directly

For a view in the older syntax that you load yourself:

```python
from tesserae.spec import ViewWatcher, load_view

view = load_view("Home_View.yaml")
watcher = ViewWatcher(view, "Home_View.yaml")
```

Then either:

- **Inside a running app** -- start it with the app's thread handle,
  and stop it when you're done:

  ```python
  watcher.start(app.thread_handle())
  ...
  watcher.stop()
  ```

- **In a loop you control yourself** -- call `poll()` regularly. It
  checks each file's modification time and size, reloads if anything
  changed, and returns `True` when it did. A failed reload raises (once
  per edit) and leaves the view as it was.

  ```python
  while running:
      if watcher.poll():
          print("reloaded")
  ```

`watcher.files` lists every file being watched. It's recomputed on every
reload, so a newly added include, fragment or image is picked up.

## Components added at run time

In the older syntax, a component built with `tesserae.instantiate` (a `Repeater`'s rows, say)
comes from its own `*_View.yaml`, and that file is watched too.
Editing it reloads every live instance in place. Each keeps its nodes,
its own ViewModel and its bound values, and a list of rows keeps its
order. One watcher per file serves all its instances, so ten rows cost
one rebuild, not ten. Files a component `include:`s, and `component:`
fragments it uses, are watched with it.

A component added while the app runs is watched as well, including the
first one of a new file. It's found in any view on the app's window,
even one the app doesn't otherwise know, since `instantiate`
registers it with the app. A row removed before the edit is left alone. A
broken edit leaves every instance as it was and is logged once for the
file:

```text
hot reload: watching component TodoItem_View.yaml (3 instance(s))
reloaded /path/to/TodoItem_View.yaml (3 instance(s))
```

## The window view

A `kind: Window` view loaded with `app.load("Window")` is watched like any view, and so is each view it embeds (`view:`). An edit is
applied in place. (A `widget: Window` view opened with `app.open_view` is not watched.)

| Edit | What happens |
| --- | --- |
| the window's `title`, `min_width`, `min_height` or `borderless` | the OS window is set again |
| the `title_bar:` | the bar is rebuilt where it is, and still the [title bar](custom-title-bars.md) |
| a `view:` with a `route:` added or removed | the screen is registered or dropped; the current screen stays showing |
| a `DockPanel` added, removed, renamed or moved to another zone | docked there; a panel the file didn't move stays where the user dragged it |
| a zone's size | set, and a zone the file didn't change keeps the size the user dragged it to |
| an embedded view's file | that view is rebuilt in place, with its ViewModel; editing the host keeps an embedded view whose `view:` and `with:` didn't change, with its state |

A change that can't be applied is logged as an error and the app keeps running.

## Theme and stylesheet files

`App.run(hot_reload=True)` also watches the theme files given to
`App(default_theme=..., custom_theme=)`. When you save one, Tesserae
re-reads both on the watcher thread, then re-themes every view the app opened
through `app.set_theme_specs(...)`: a different `seed:`, `colors:` or
`typography:` shows at once, and bound values stay live. A theme given as a
`*_spec=` dict has no file, so it isn't watched. A broken edit is logged
at `ERROR` like a failed view reload, and the app keeps its previous theme.

Stylesheet files are watched for screens of the older syntax:

- **The default stylesheet** from `App(stylesheet=)`: saving it
  re-styles every screen that uses the default, through
  `app.set_stylesheet_spec(...)`. Screens loaded with their own
  stylesheet are left alone.
- **A screen's own stylesheet** from `app.load(..., stylesheet=)`:
  saving it re-styles only the screens loaded with that file.

A stylesheet of `widget:` rules, which views opened with `app.open_view` use, is not applied by a reload: the edit is logged as
an error naming the file, the views keep their old rules, and the new ones are read when the app starts again.
A stylesheet `tre` rejects is reported naming the file, and every
screen keeps its old stylesheet.

### Handlers fire when bindings are re-applied

After a theme or stylesheet change, `tre` re-applies every binding so
bound nodes keep their live values. It does this by setting each bound
value again, so a declared `on_change` handler on a bound node (a
`Checkbox` with `checked:` bound, a `TextField` with `text:` bound)
runs once per reload, even though the value didn't change. The same
thing happens when a view is first attached and on a view-file reload.
Write `on_change` handlers so that running one again with the same value
is harmless: set a `Signal` to the node's current value, don't toggle
it or append to a list. This is a known behaviour of `tre`.

## Limits

- **Don't use `tre`'s own `View.poll_reload()`.** Tesserae gives `tre`
  the finished view as data, never a file, so `tre` has nothing to
  watch.
