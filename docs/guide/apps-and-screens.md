# Apps & Screens

```python
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=120, title="My App", search=["."])
app.bind(CounterViewModel)          # CounterViewModel serves the view named "Counter"
view = app.open_view("Counter")     # Counter_View.yaml, found by name
app.show("Counter")                 # registered under the view's name
app.run()
```

An `App` is the entry point every app has exactly one of: a registry of named screens, and one live window, themed with the app's theme. A screen is a view that has been opened with `app.open_view` and so registered. Screens are built straight into the
window. `App.show(name)` switches which registered screen that window shows: it attaches the screen's root to
the window and detaches the previous one, which stays alive, with its
state and its bindings, until it's shown again.

Neither a view nor its ViewModel is ever re-parsed, re-attached, or
otherwise re-bootstrapped by a later `show()`: each stays alive, its
own `Signal` subscriptions intact, for the whole life of the `App`.

## Opening screens

`app.bind(CounterViewModel)` says which ViewModel serves a view, by the names in its `views`. `app.open_view(view, name=None)`
opens a view against the ViewModel that serves its name and registers it. `view` is a path, or a name found in the
[project](projects.md) (`"Counter"` is `Views/Counter_View.yaml`, or any folder you gave `search=`); the views it calls are found
there too. The screen is registered under `name`, which defaults to the view's own `name:` and then to its file's name. It
returns the opened view, and `app.screen(name)` gives the view and its ViewModel afterwards (`None` for a view with no ViewModel).

```python
app.bind(HomeViewModel)
app.bind(SettingsViewModel)
app.open_view("Home")
app.open_view("Settings")
app.show("Home")
```

`app.bind(instance)` uses a ViewModel you made (to give it arguments), and `app.bind(factory=...)` makes one for each view that opens.
[Components & Embedding](components.md#one-viewmodel-several-views) says what one ViewModel serving several views means, and
[Naming Convention](naming-convention.md) how the names join up. `app.check()` lists every mismatch between the open views and their
ViewModels without a window, and an empty list is a clean bill.

A ViewModel reaches the app as `self.app` once it is attached, so a handler can switch screens:

```python
from tesserae import ViewModel

class HomeViewModel(ViewModel):
    views = "Home"

    def go_to_settings(self):
        self.app.show("Settings")  # switches screens from inside a real click handler
```

Switching screens from inside a handler works even *reentrantly*, from the very handler `App.show` itself is dispatching into. A
handler can also navigate without Python: `handlers: {on_click: navigate.Settings}`, or `navigate_to('Note', {'id': 3})` for a
screen held in a name, below.

`App.register(name, view, viewmodel)` is the lower-level path, for a view you built yourself (`app.build_view(...)`) and a
ViewModel you constructed. `App.load` opens a view written in the older syntax with its ViewModel (`ViewModel(view)`), by the
[older naming rule](naming-convention.md#views-in-the-older-syntax).

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
    views = "Note"

    def __init__(self):
        super().__init__()
        self.title = Signal("")

    def on_navigated(self, params):
        self.title.set(f"Note {params['id']}")
```

A view reads the params of the screen showing as `app.params` (`{{ app.params.get('id') }}`), and can go to a screen without Python:
`handlers: {on_click: "navigate_to('Note', {'id': 3})"}`, `navigate.Settings`, `navigate.back` and `navigate.forward`.

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
  `disabled: "{{ not app.can_go_back }}"` (see
  [Disabled](interaction.md#disabled)). `app.back()` itself does nothing,
  and returns `False`, with nowhere to go.
- **Alt+Left** and **Alt+Right** go back and forward, except in a text
  input, where Option+Left moves by word on macOS. So do the mouse's
  **back and forward side buttons**, wherever the pointer is; the other buttons don't.
- A `NavigationRailScreens` in a [window view](windows-and-docks.md) navigates, so `back()` returns from a
  rail choice, and the rail follows `back()` and `forward()`.
- `app.guard("Admin", check)` runs `check(params)` before the app goes to a screen: `True` lets it in, `False` keeps the app
  where it is, and a route (a string, read as `navigate_to` reads it; more than eight redirects in a row raise `ValueError`) sends it there instead. `navigate`, `navigate_to`, `back` and `forward` ask it; `show` is a
  jump and does not. A routed view of a window view can say the same in the view (`route: {guard: ..., redirect: ...}`:
  [Windows, Docks & Embedded Views](windows-and-docks.md#routed-views)).
- `app.transition` sets how a step between screens looks (`fade_through`, `shared_axis_x`, `container_transform`, ...);
  `navigate_with` picks one for a single step. See [The View Language](view-language.md#moving-between-screens).

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

A ViewModel reads and writes it as `self.state` once it is attached to a view on the app's window, and a view reads it through
`app`, in any view:

```yaml
text: "{{ app.state.user }}"        # a Signal reads as its value, and the text follows it
```

```python
class SettingsViewModel(ViewModel):
    views = "Settings"

    def sign_out(self):
        self.state.user.set("guest")  # every view that reads it updates
```

A view can read the state but not write through it: a property that the user edits (a text field) is two-way only when it is
given a bare name that is a Signal of the ViewModel. So a ViewModel that edits a shared value holds the Signal itself, and is made
with the state:

```python
class ProfileViewModel(ViewModel):
    views = "Profile"

    def __init__(self, state):
        super().__init__()
        self.name = state.user          # `text: "{{ name }}"` on a TextField now edits it

state = AppState()
app = App(state=state)
app.bind(ProfileViewModel(state))       # a ViewModel you made yourself
```

- **Nothing is global:** each `App` has its own `state`, and it can be
  set later (`app.state = AppState()`).
- **A ViewModel's own attribute wins:** one that sets `self.state` or
  `self.app` itself keeps its own, and its views' `state` names it.
- **In the constructor**, `self.app` and `self.state` are not there yet: a ViewModel `app.bind` makes takes no arguments, and
  gets its app when its first view is attached. Hand it what it needs with `app.bind(instance)`, as above, or read it in
  `on_attached(handle)`.
- Off an app's window (a `View` with its own window), there's no app:
  `self.app` and `self.state` raise `AttributeError` saying so. So does
  `self.state` on an app with none.

## The window

`App` owns the window, and its options are `App`'s. Each is also a property that can change while the app runs.

```python
app = App(width=960, height=640, title="Notes",
          borderless=True,     # no OS title bar or borders: the app draws its own
          min_width=480, min_height=320, icon=HERE / "icon.png")  # the file must exist
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
`"x11"`. The options for how the window is drawn (`dpi_scaling`, `present_mode`, `transparent`, `ripple`, `focus_ring`, ...) are in
[Window Options & the OS](window-options.md), and `reduced_motion` and `high_contrast`, which follow the OS, in [Themes](../themes/index.md#contrast-and-motion).

**The window's size** is a value a view can read: `app.window_width` and `app.window_height` in logical pixels, and the Material 3
size classes `app.width_class` (`compact`, `medium`, `expanded`, `large`, `extra_large`) and `app.height_class`, so a layout can
change as the window is resized:

```yaml
- {widget: NavigationRailScreens, name: rail, if: "app.width_class != 'compact'", items: [{label: Home, icon: home, screen: Home}]}
```

([The View Language](view-language.md#the-window-and-the-app) has the thresholds.)

A title bar the app draws calls the window's actions and follows its
state:

- **Actions:** `app.minimize()`, `app.maximize()`, `app.restore()`,
  `app.toggle_maximized()` (a maximize button) and `app.close()`. `close()`
  closes the window as the user's close would, so a "save changes?" check
  on `close_requested` still runs and can cancel it: `app.window.on("close_requested", handler)`, and `event.cancel()` in the handler keeps the window open.
- **State:** `app.maximized` and `app.active` are read-only
  [Computeds](reactivity.md) that follow the window: maximized or not, and
  whether it has the OS's focus. A binding follows them like any Signal:

  ```yaml
  text: "{{ 'Restore' if app.maximized else 'Maximize' }}"
  ```

### A title bar

With `borderless=True`, a view draws the title bar, most simply with
`widget: TitleBar` (an icon, a title, the app's own controls, and the
window buttons), or a node of its own marked `window_region: drag`. A
borderless window also gets a 1 px border. All of it, and macOS's
traffic lights, is in [Custom Title Bars](custom-title-bars.md).

## Several windows

`app.window` is the main window. `app.open_window("Prefs")` builds `Prefs_View.yaml` in a new OS window, with the ViewModel that
serves it, and returns its `AppWindow`; `app.windows`, `app.window_of(name)` and `app.close_window(name)` find and close them, and
`modal=True` blocks the window it was opened from until the new one closes. A second window has no screens or routes: those belong to
the main window. [Windows, Docks & Embedded Views](windows-and-docks.md#several-windows) has the rest.

## Running the app

```python
app.run(max_frames=None)  # the one blocking call
```

Opens the window and runs the render loop. `max_frames` caps the loop, for headless and CI runs that need an exit with no one to close the window; omit it for an interactive run that exits when the window closes. The environment variable `TESSERAE_MAX_FRAMES=n` does the same for a run that gives no `max_frames`, which is how `tesserae build --check` runs a built app and sees it exit.

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
| `hot_reload=True` | Reloads the app's theme and stylesheet files, the views opened with `app.open_view` or `app.open_window` (their ViewModel and state stay), and the screens that `app.load` made from a file in the older syntax, when they change on disk. See [Hot Reload](hot-reload.md). |
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
