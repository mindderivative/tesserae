# Hot Reload

Tesserae reloads a screen when you edit any file it was built from: the
`*_View.yaml` itself, any file it `include:`s, any `*_Component.yaml`
fragment it uses, and any image it shows. The live view is updated in
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
rejects -- the error names the file, is logged the same way as an
exception in an event handler, and the screen stays as it was. The app
and the watcher keep running: fix the file, save, and it reloads.

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

## Theme files

`App.run(hot_reload=True)` also watches the theme files given to
`App(default_theme=..., custom_theme=...)`. When you save one, Tesserae
re-reads both on the watcher thread, then re-themes every screen built
by `app.load()` or `app.build_view()`, and the window, through
`app.set_theme_specs(...)`. Bound values stay live. A theme given as a
`*_spec=` dict has no file, so it isn't watched. A broken edit is logged
like a failed view reload, and the app keeps its previous theme.

## Limits

- **Stylesheet files aren't watched yet** (M31 Phase 2). After editing
  one, call `view.set_stylesheet(stylesheet_spec=load_stylesheet(...))`.
- **Don't use `tre`'s own `View.poll_reload()`.** Tesserae gives `tre`
  the finished view as data, never a file, so `tre` has nothing to
  watch.
