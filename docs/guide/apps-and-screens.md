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

## Navigation and history

`show(name)` is a jump. `navigate` is a step the user can come back from
(M66):

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
  button binds its `disabled` to one (M70), and is greyed out, skipped by
  Tab and deaf to clicks while there's nowhere to go:
  `bindings: {disabled: "{{ not app.can_go_back.get() }}"}` (see
  [Disabled](interaction.md#disabled)). `app.back()` itself does nothing,
  and returns `False`, with nowhere to go.
- **Alt+Left** and **Alt+Right** go back and forward, except in a text
  input, where Option+Left moves by word on macOS. So do the mouse's
  **back and forward side buttons**, wherever the pointer is (M72, on
  `tre` 0.4.1); the other buttons don't.
- A shell file's navigation rail navigates, so `back()` returns from a
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

## The window

`App` owns the window, and its options are `App`'s (0.3.0, on `tre`
0.5.0). Each is also a property that can change while the app runs.

```python
app = App(width=960, height=640, title="Notes",
          decorations=False,   # no OS title bar or borders: the app draws its own
          min_width=480, min_height=320, icon="icon.png")
```

| Option | What it does |
|---|---|
| `decorations` | Whether the OS draws the title bar and borders (default `True`). Without them the app draws its own title bar; on macOS the title bar stays, transparent, with the traffic lights. |
| `resize_border` | How many pixels along each edge resize an undecorated window. Unless given, 6 while undecorated and 0 otherwise. `tre` turns it off while maximized or fullscreen, and on macOS, where the OS resizes the window. |
| `min_width`, `min_height` | The smallest the user can resize the window to (0 for no limit), so a title bar's buttons never crush. |
| `fullscreen` | Borderless, filling the monitor. |
| `system_menu` | Whether a right-click on the title bar opens the OS's window menu (Windows, and Wayland compositors that have one). Off by default, so the right-click is the app's. |
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

With `decorations=False`, a view draws the title bar, most simply with
`kind: TitleBar`:

```yaml
children:
  - id: bar
    kind: TitleBar
    title: Notes
    icon: home                              # optional: an icon name
    buttons: [minimize, maximize, close]    # the default; any of them
    children:                               # the app's own, between the
      - {id: search, kind: TextField, ...}  # title and the buttons
  - id: body
    ...
```

It's a 40 px bar that moves the window when it's dragged (from anywhere
but its buttons and the app's own controls) and maximizes on a
double-click; the icon and title at its start; the app's children in
the middle; and minimize, maximize and close at the right. Maximize
shows the restore glyph while the window is maximized. Its colours are
Material 3 roles (`surface`, `on_surface`), so it needs a themed app;
the title, icon and buttons fade while the window isn't the focused
one, and close's hover is red. Each part has a class, so a stylesheet
or theme restyles it: `title_bar`, `title_bar_icon`, `title_bar_title`,
`title_bar_content`, `title_bar_buttons`, `title_bar_button`,
`title_bar_close` and `title_bar_glyph` (and its ids are `bar.title`,
`bar.close` and so on, after the bar's).

On macOS the OS keeps its title bar, transparent, with the traffic
lights: the bar leaves room for them at its start and hides its own
buttons. `app.titlebar_inset` (the `(height, width)` they take, `(0, 0)`
elsewhere and in fullscreen) and `app.native_controls` (whether they
show) are there for a bar of your own.

A bar of your own is any node marked as the window's drag region, with
buttons whose handlers are the window's actions -- no ViewModel method
needed:

```yaml
- id: my_bar
  kind: Container
  window_region: drag          # a press here moves the window
  style: {height: 36, background: surface_container}
  children:
    - {id: tabs, kind: Container, window_region: none, ...}   # not a handle
    - id: close
      kind: Rect
      handlers: {on_click: window.close}
      ...
```

`window_region: drag` covers the node and everything in it that isn't
interactive (a node with a click handler, a focusable one or a text
field is pressed as usual); `none` keeps a node, and what's in it, from
moving the window. The handlers are `window.minimize`,
`window.maximize`, `window.restore`, `window.toggle_maximized` and
`window.close`; they need the view to be on an `App`'s window.

When the OS takes a press -- moving the window from its title bar,
maximizing it on a double-click -- the pressed node gets
`pointer_cancel` instead of `pointer_up`, and no click. Every Tesserae
widget releases its press on it; a widget of your own that tracks a
press should listen for both.

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
