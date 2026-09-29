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
`tre.Window`, created with the `App` and themed with the app's theme.
Screens are built straight into it. `App.show(name)` switches which
registered screen that window shows: it attaches the screen's root to
the window and detaches the previous one, which stays alive, with its
state and its bindings, until it's shown again.

A view you build yourself -- `app.build_view(...)`, or `tesserae.View(path)`
-- can be given to `register()`. One built outside the app (`View(path)`)
is rebuilt in the app's window when registered, keeping its ViewModel;
look nodes up with `view.node(...)` after registering it.

Neither a `View` nor its `ViewModel` is ever re-parsed, re-attached, or
otherwise re-bootstrapped by a later `show()` -- each stays alive, its
own `Signal` subscriptions intact, for the whole life of the `App`.

## `load` vs. `register`

`App.load(view_path, viewmodel_cls, name=None)` is the enforced-naming
path (see [Naming Convention](naming-convention.md)) -- most real
screens use this. `name` defaults to the shared prefix (`"Counter"`
for `Counter_View.yaml`/`Counter_ViewModel.py`); only needed explicitly
if two different pairs would otherwise collide on it.

`App.register(name, view, viewmodel)` is the lower-level path, for a view
you built yourself (`app.build_view(...)`, or `tesserae.View(path)`) and
a ViewModel you constructed.

A ViewModel doesn't need to be handed the app: on the app's window,
`self.app` is the `App` (M65), so a handler can switch screens with
`load()`'s plain `viewmodel_cls(view)` construction:

```python
from tesserae import ViewModel

class HomeViewModel(ViewModel):
    def go_to_settings(self):
        self.app.show("Settings")  # switches screens from inside a real click handler
```

Switching screens from inside a handler works even *reentrantly* --
from the very handler `App.show` itself is dispatching into (see
`examples/multi_screen/` in the repository).

## Shared state

State several screens use -- the signed-in user, settings, an open
document -- belongs to the app, not to one screen (M65). Give the app
any object as `state=`, typically a class of `Signal`s:

```python
from tesserae import App, Signal

class AppState:
    def __init__(self):
        self.user = Signal("Ada")
        self.came_from = Signal("nowhere")

app = App(width=400, height=300, state=AppState())
```

A ViewModel on the app's window reads and writes it as `self.state`, and
a binding reads it by name, in any view:

```yaml
bindings: {text: "{{ state.user.get() }}"}  # a whole {{ }} expression
```

```python
class SettingsViewModel(ViewModel):
    def sign_out(self):
        self.state.user.set("guest")  # every screen bound to it updates
```

- **Nothing is global:** each `App` has its own `state`, and it can be
  set later (`app.state = AppState()`).
- **A ViewModel's own attribute wins:** one that sets `self.state` or
  `self.app` itself (as the shell examples pass `app` in) keeps its own,
  and its views' `state` names it.
- **In a constructor**, before `super().__init__(view)`, `self.state`
  isn't there yet; `App.of(view).state` is:

    ```python
    from tesserae import App, Computed, ViewModel

    class HomeViewModel(ViewModel):
        def __init__(self, view):
            state = App.of(view).state
            self.greeting = Computed(lambda: f"Hello, {state.user.get()}")
            super().__init__(view)
    ```

- Off an app's window (a `View` with its own window), there's no app:
  `self.app` and `self.state` raise `AttributeError` saying so. So does
  `self.state` on an app with none.

A component made with `tesserae.instantiate` on the app's window reaches
it the same way.

## Running the app

```python
app.run(max_frames=None)  # the one blocking call
```

Opens the real window `show()` already built and runs `tre`'s own real
render loop. `max_frames` caps the loop -- useful for headless/CI runs
that need a real exit condition with no interactive close; omit it for
a real, interactive run that exits only when the window closes.

With no display reachable, `run()` returns without opening anything. If
the window's GPU can't be set up (no adapter, device or supported
surface), it raises `RuntimeError` (since `tre` 0.4.0; before, the
process exited with status 0). Each window repaints only what changed
(`tre` 0.4.0's partial redraw, pixel-identical to a full redraw);
`app.window.set(partial_redraw=False)` turns it off.

`app.current` (a property) returns the name last passed to `show()`,
or `None` before the first real call.
