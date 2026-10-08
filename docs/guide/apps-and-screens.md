# Apps & Screens

```python
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=120, title="My App")
view, viewmodel = app.load("Counter_View.yaml", CounterViewModel)
app.show("Counter")  # registered under the inferred prefix
```

An `App` is the entry point every app has exactly one of: a registry of named `(View, ViewModel)` pairs, and one live window, themed with the app's theme. Screens are built straight into it. `App.show(name)` switches which
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
`self.app` is the `App`, so a handler can switch screens with
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

## Navigation and history

`show(name)` is a jump. `navigate` is a step the user can come back from:

```python
app.navigate("Note", id=42)  # pushes a history entry; forward entries are dropped
app.back()                   # the entry before (returns False if there's none)
app.forward()                # the entry back() left
```

The screen's ViewModel gets the params before the screen shows, through
an optional `on_navigated` method, each time its entry is reached --
by `navigate`, `back` or `forward`:

```python
class NoteViewModel(ViewModel):
    def __init__(self, view):
        self.title = Signal("")
        super().__init__(view)

    def on_navigated(self, params):
        self.title.set(f"Note {params['id']}")
```

- If `on_navigated` raises, nothing changes: the screen showing and the
  history stay as they were.
- Navigating to the entry already showing (same screen, same params)
  does nothing. The screen name is positional-only, so a param can be
  called `name`.
- `show(name)` pushes nothing and calls no hook; it replaces the current
  entry, so `back()` leaves it for the entry before.
- `app.can_go_back` and `app.can_go_forward` are `Signal`s. A back
  button binds its `disabled` to one, and is greyed out, skipped by
  Tab and deaf to clicks while there's nowhere to go:
  `bindings: {disabled: "{{ not app.can_go_back.get() }}"}` (see
  [Disabled](interaction.md#disabled)). `app.back()` itself does nothing,
  and returns `False`, with nowhere to go.
- **Alt+Left** and **Alt+Right** go back and forward, except in a text
  input, where Option+Left moves by word on macOS. So do the mouse's
  **back and forward side buttons**, wherever the pointer is; the other buttons don't.
- A `NavigationRailScreens` in a [window view](windows-and-docks.md) navigates, so `back()` returns from a
  rail choice, and the rail follows `back()` and `forward()`.

### Routes and deep links

Routes name screens with strings, in both directions:

```python
app.route("", "Home")
app.route("notes", "Notes")
app.route("notes/{id:int}", "Note")   # {id} is a string; {id:int} an int

app.navigate_to("notes/42")           # Note, with {"id": 42}
app.location                          # "notes/42": save it, reopen there next time
```

- Routes are tried in the order they're added; `navigate_to` raises
  `KeyError` when none matches.
- `location` is the showing screen as a route string: the first route
  of that screen that reads its params back exactly, or `None`.
- A deep link from the command line is `app.navigate_to(sys.argv[1])`
  (`examples/multi_screen/` does this).

## Shared state

State several screens use -- the signed-in user, settings, an open
document -- belongs to the app, not to one screen. Give the app
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
  `self.app` itself (as a ViewModel built by hand may pass `app` in) keeps its own,
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

## The window

`App` owns the window, and its options are `App`'s. Each is also a property that can change while the app runs.

```python
app = App(width=960, height=640, title="Notes",
          borderless=True,     # no OS title bar or borders: the app draws its own
          min_width=480, min_height=320, icon="icon.png")
```

| Option | What it does |
|---|---|
| `borderless` | Whether the OS window has no title bar or borders (default `False`). Then the app draws its own title bar; on macOS the title bar stays, transparent, with the traffic lights. A [window view](windows-and-docks.md) sets it with `borderless: true`. |
| `resize_border` | How many pixels along each edge resize a borderless window. Unless given, 6 while borderless and 0 otherwise. It is off while maximized or fullscreen, and on macOS, where the OS resizes the window. |
| `min_width`, `min_height` | The smallest the user can resize the window to (0 for no limit), so a title bar's buttons never crush. |
| `fullscreen` | Borderless, filling the monitor. |
| `system_menu` | Whether a right-click on the title bar opens the OS's window menu (Windows, and Wayland compositors that have one). Off by default, so the right-click is the app's. |
| `window_border` | Whether a borderless window gets a 1 px border (default `True`; see [The window border](custom-title-bars.md#the-window-border)). |
| `icon` | An image file (a square PNG is best), shown on Windows and X11; `app.set_icon(path)` changes it. Wayland and macOS take the icon from the app's desktop entry or bundle, which `tesserae build --installer` makes. |

`app.platform` says which it is: `"windows"`, `"macos"`, `"wayland"` or
`"x11"`.

A title bar the app draws calls the window's actions and follows its
state:

- **Actions:** `app.minimize()`, `app.maximize()`, `app.restore()`,
  `app.toggle_maximized()` (a maximize button) and `app.close()`. `close()`
  closes the window as the user's close would, so a "save changes?" check
  on `close_requested` still runs and can cancel it.
- **State:** `app.maximized` and `app.active` are read-only
  [Computeds](reactivity.md) that follow the window: maximized or not, and
  whether it has the OS's focus. A binding follows them like any Signal:

  ```yaml
  bindings:
    text: "{{ app.maximized.get() and 'Restore' or 'Maximize' }}"
  ```

### A title bar

With `borderless=True`, a view draws the title bar, most simply with
`kind: TitleBar` (an icon, a title, the app's own controls, and the
window buttons), or a node of its own marked `window_region: drag`. A
borderless window also gets a 1 px border. All of it, and macOS's
traffic lights, is in [Custom Title Bars](custom-title-bars.md).

## Running the app

```python
app.run(max_frames=None)  # the one blocking call
```

Opens the window and runs the render loop. `max_frames` caps the loop, for headless and CI runs that need an exit with no one to close the window; omit it for an interactive run that exits when the window closes.

With no display reachable, `run()` returns without opening anything. If
the window's GPU can't be set up (no adapter, device or supported
surface), it raises `RuntimeError`. Each window repaints only what changed, with the same result as a full redraw; `app.window.set(partial_redraw=False)` turns that off.

`app.current` (a property) returns the name last passed to `show()`,
or `None` before the first real call.

An app needs no screen: an empty window runs, for an app built in Python. Registering screens and showing
none raises `RuntimeError`.

### Options of `run`

| Option | What it does |
| --- | --- |
| `max_frames` | Stops after that many frames; for headless and CI runs. |
| `hot_reload=True` | Reloads every screen built from a file, and the app's theme, stylesheet and component files, when they change on disk. A screen built from a spec dict has no file, so it isn't watched. See [Hot Reload](hot-reload.md). |
| `keepalive` | `False` (the default) does not tick. `True` wakes the loop every 0.02 s; a number is the interval in seconds. Each tick sleeps on the loop thread, so input can wait up to a tick, and an idle window costs about half a percent of one core. It is for code that wants the loop woken regularly; hot reload and threads don't need it. |

### From another thread

Views, windows and the app may only be used from the thread that created them. A background thread
hands work over with `app.thread_handle()`: `handle.call_soon(fn)` runs `fn()` on the event-loop thread
at the next frame, waking the loop if it is idle. Callables run in the order they were queued, and one
queued before `run()` runs on the first frame.

```python
handle = app.thread_handle()

def on_download_done(result):          # called on a worker thread
    handle.call_soon(lambda: viewmodel.status.set(result))
```
