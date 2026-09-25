# Hot Reload

Tesserae reloads a view when you edit any file it was built from: the
`*_View.yaml` itself, any file it `include:`s, any `*_Component.yaml`
fragment it uses, and any image it shows. The live view is updated in
place -- widgets that didn't change keep their identity, focus and any
running animation.

```python
from tesserae.spec import ViewWatcher, load_view

view = load_view("Home_View.yaml")
watcher = ViewWatcher(view, "Home_View.yaml")

while running:
    ...
    if watcher.poll():
        print("Home_View.yaml reloaded")
```

`poll()` checks each file's modification time and size. It's cheap,
needs nothing installed, and runs nothing in the background -- call it
as often as you like from your own loop. It returns `True` when it
reloaded and `False` when nothing changed.

## When an edit is broken

If a reload fails -- invalid YAML, an unknown component, a widget `tre`
rejects -- `poll()` raises with the file named in the message, and the
view stays as it was. The error is raised once per edit: polling again
returns `False` until you save another change, so a loop that logs and
carries on won't be flooded.

```python
try:
    watcher.poll()
except ValueError as exc:  # ComponentError is a ValueError too
    print(f"reload failed: {exc}")
```

## Limits

- **Call `poll()` on the thread that owns the view.** `tre` views are
  single-threaded, so a background thread can't reload them.
- **Not yet available inside `App.run()`.** `App.run()` hands control to
  `tre`'s event loop, and `tre` doesn't yet offer a way to run code
  periodically from inside it, so there's nowhere to call `poll()`
  from. For now, hot reload works in a loop your app controls
  ([`tre` issue #6](https://github.com/mindderivative/tre/issues/6)
  tracks adding that hook).
- **Don't use `tre`'s own `View.poll_reload()`.** Tesserae gives `tre`
  the finished view as data, never a file, so `tre` has nothing to
  watch.
