# Apps & Screens

```python
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=120, title="My App")
view, viewmodel = app.load("Counter_View.yaml", CounterViewModel)
app.show("Counter")  # registered under the inferred prefix
```

`App` is the single real entry point every app owns exactly one of --
a registry of named `(View, ViewModel)` pairs, plus exactly one live
`tre.Window`. `App.show(name)` switches which registered pair that one
`Window` currently renders:

- The **first** call opens the real window (`tre.Window.from_view`).
- Every call **after** switches the same live window
  (`tre.Window.show_view`).

Neither a `View` nor its `ViewModel` is ever re-parsed, re-attached, or
otherwise re-bootstrapped by a later `show()` -- each stays alive, its
own `Signal` subscriptions intact, for the whole life of the `App`.

## `load` vs. `register`

`App.load(view_path, viewmodel_cls, name=None)` is the enforced-naming
path (see [Naming Convention](naming-convention.md)) -- most real
screens use this. `name` defaults to the shared prefix (`"Counter"`
for `Counter_View.yaml`/`Counter_ViewModel.py`); only needed explicitly
if two different pairs would otherwise collide on it.

`App.register(name, view, viewmodel)` is the lower-level path for a
`ViewModel` that needs a **live reference to `App` itself** at
construction time -- e.g. to call `app.show(...)` from its own
handler:

```python
from tesserae import App, ViewModel
from tesserae.spec import load_view

class HomeViewModel(ViewModel):
    def __init__(self, app, view):
        self.app = app
        super().__init__(view)

    def go_to_settings(self):
        self.app.show("Settings")  # switches screens from inside a real click handler

app = App(width=400, height=300, title="Multi-Screen")
home_view = load_view("Home_View.yaml")
home_vm = HomeViewModel(app, home_view)
app.register("Home", home_view, home_vm)
```

Switching screens from inside a handler works even *reentrantly* --
from the very handler `App.show` itself is dispatching into (see
`examples/multi_screen/` in the repository).

## Running the app

```python
app.run(max_frames=None)  # the one blocking call
```

Opens the real window `show()` already built and runs `tre`'s own real
render loop. `max_frames` caps the loop -- useful for headless/CI runs
that need a real exit condition with no interactive close; omit it for
a real, interactive run that exits only when the window closes.

`app.current` (a property) returns the name last passed to `show()`,
or `None` before the first real call.
