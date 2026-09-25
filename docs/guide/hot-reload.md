# Hot Reload

Tesserae reloads a screen when you edit any file it was built from: the
`*_View.yaml` itself, any file it `include:`s, any `*_Component.yaml`
fragment it uses, and any image it shows. Inside an `App`, it also
re-styles the running app when a theme or stylesheet file changes (see
[below](#theme-and-stylesheet-files)). The live view is updated in
place -- widgets that didn't change keep their identity, focus and any
running animation.

## In an app

```python
app = App()
app.load("Home_View.yaml", HomeViewModel)
app.show("Home")
app.run(hot_reload=True)
```

Every screen registered with `App.load()` is watched while the app runs.
Save a change and it appears in the window straight away.

Behind the scenes each screen gets a `ViewWatcher` on a background
thread. It listens for file-change events (using
[`watchfiles`](https://watchfiles.helpmanual.io/)), rebuilds the view
there -- so file reading and component expansion never slow the UI --
and hands only the final update to the event loop through
[`App.thread_handle()`](../api/app.md#thread_handle).

## When an edit is broken

If a reload fails -- invalid YAML, an unknown component, a widget `tre`
rejects -- Tesserae logs one `ERROR` line naming the file and the error
(the traceback is at `DEBUG`), and the screen stays as it was. The app
and the watcher keep running: fix the file, save, and it reloads. Each
reload that works is logged at `INFO`. See [Logging](logging.md).

## Using `ViewWatcher` directly

For a view you load yourself:

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

## Theme and stylesheet files

`App.run(hot_reload=True)` also watches the theme files given to
`App(default_theme=..., custom_theme=...)`. When you save one, Tesserae
re-reads both on the watcher thread, then re-themes every screen built
by `app.load()` or `app.build_view()`, and the window, through
`app.set_theme_specs(...)`. Bound values stay live. A theme given as a
`*_spec=` dict has no file, so it isn't watched. A broken edit is logged
at `ERROR` like a failed view reload, and the app keeps its previous theme.

Stylesheet files are watched the same way:

- **The default stylesheet** from `App(stylesheet=...)`: saving it
  re-styles every screen that uses the default, through
  `app.set_stylesheet_spec(...)`. Screens loaded with their own
  stylesheet are left alone.
- **A screen's own stylesheet** from `app.load(..., stylesheet=...)`:
  saving it re-styles only the screens loaded with that file.

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
it or append to a list. This is [`tre` issue #12](https://github.com/mindderivative/tre/issues/12).

## Limits

- **Embedded components don't get the app's theme or stylesheet.** A
  component added with [`tesserae.instantiate`](components.md) is built
  by `tre` without the host view's theme and stylesheet `styles:`, so it
  isn't styled by them when created or when either is reloaded. Style
  it with its own inline `style:`.
- **Don't use `tre`'s own `View.poll_reload()`.** Tesserae gives `tre`
  the finished view as data, never a file, so `tre` has nothing to
  watch.
