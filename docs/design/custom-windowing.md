# Custom windowing (0.3.0)

!!! note "Decided 2026-09-30"
    This is Tesserae 0.3.0's M1 design ([#30](https://github.com/mindderivative/tesserae/issues/30)).
    The user approved it: "approved, go with your recommendations and start
    M2". In each [question](#decisions), the option marked **(decided)**
    is the recommendation the user approved; M2 onwards follow it, starting
    with [#40](https://github.com/mindderivative/tesserae/issues/40).

## The goal

An app can drop the operating system's title bar and have Tesserae draw
one in its own theme: the app's icon and title, minimize, maximize and
close, and anything else the app puts up there (a search field, tabs,
buttons). The same app then looks the same on every platform.

`tre` 0.5.0 ([custom title bars](https://github.com/mindderivative/tre/blob/v0.5.0/docs/guide/custom-title-bars.md))
does what only the platform can: it turns the native decorations off,
moves and resizes the window, maximizes and restores it, and reports its
state. Tesserae does the look, in its usual way: declared in YAML, themed
from Material 3 roles, hot-reloadable.

## What `tre` 0.5.0 gives

- **The window:** `Window(decorations=False)` (or live, `set(decorations=...)`),
  and `minimize()`, `maximize()`, `restore()` and `close()`. `close()` fires
  `close_requested` first.
- **Its state:** `get("maximized")`, `"minimized"`, `"active"` and
  `"fullscreen"`, and the `maximized` and `active` events.
- **Window properties:** `fullscreen`, `min_width`/`min_height`,
  `icon=(rgba, w, h)` and `platform`.
- **The title bar:** `window_region="drag"` on a node. A press drags unless
  the node is interactive (focusable, a `click` listener, holding the
  pointer capture, or a text input); `"none"` and `"drag"` override that.
  A dragged press ends in **`pointer_cancel`**, not `pointer_up`.
  Double-clicking maximizes.
- **The borders:** `resize_border=N`. It's off when maximized or
  fullscreen, and on macOS.
- **The window menu:** `system_menu=True`, opt-in.
- **macOS:** the title bar stays as a transparent overlay with the traffic
  lights. `titlebar_inset` (height, width) and its event, and
  `native_controls`, say where to lay the bar out.

## Decisions

**Q1. How an app asks for it.**

- **(decided)** `App(decorations=False)`, with the rest as `App`
  options: `resize_border=6`, `min_width`/`min_height`, `system_menu=False`
  and `icon="icon.png"`. Tesserae decodes the PNG with Pillow, as
  `tesserae build` already does. `app.minimize()`, `maximize()`,
  `restore()`, `close()` and `toggle_maximized()`; `app.maximized` and
  `app.active` as read-only `Signal`s, so bindings can follow them.
- A per-screen setting. But decorations belong to the window, not a screen.

**Q2. How a title bar is written.** Two layers:

- **(decided)** Both of:
  - **The vocabulary:** `window_region: drag | none` becomes a node
    property in YAML views. The window actions become handlers any node
    can name without a ViewModel method: `on_click: window.minimize`,
    `window.toggle_maximized` and `window.close`.
  - **A `TitleBar` kind:** the app's icon and title, a slot for the app's
    own content, and the window buttons. It's a drag region already wired
    to the actions and the state: the maximize icon swaps, the bar dims
    when the window is inactive, and on macOS it lays itself out after the
    traffic lights.
- Only the vocabulary: every app builds its own bar.
- Only `TitleBar`: simple, but an unusual bar (tabs in it, say) couldn't be
  built.

**Q3. The app shell.**

- **(decided)** When the app is undecorated, the shell's `top_bar`
  *is* the title bar. `top_bar: {title, leading_icon, trailing_icons}`
  keeps its keys, and gains the drag region and the window buttons after
  the trailing icons. A shell app gets a custom title bar from one
  `App(decorations=False)`.
- Keep the top bar under a separate title bar: two bars, and a taller
  chrome.

**Q4. Pressed states and `pointer_cancel`.** A widget pressed and then
dragged would keep its pressed state layer, which today clears only on
`pointer_up` or `pointer_leave`.

- **(decided)** Every state layer and every pointer-driven widget
  (splitters, dock tabs, sliders) clears on `pointer_cancel`, as on
  `pointer_up`. That's also right for any other press the OS takes.
- Nothing: only nodes marked `drag` are affected. But a title bar is made
  of Tesserae's widgets.

**Q5. Theme.**

- **(decided)** The bar is a Material 3 top app bar: `surface`, or
  `surface_container` when the content scrolls under it; the title
  `on_surface`, dimmed to `on_surface_variant` when the window is
  inactive. Window buttons are icon buttons whose hover and pressed layers
  are the usual ones, except close, which uses `error_container`, as
  desktops colour close. Stylesheets can override each part, like any
  widget.
- Platform look-alikes (Windows' square buttons, GNOME's round ones): more
  code per platform, and against "the same app everywhere".

**Q6. Each platform.**

- **(decided)** On Windows and Linux, Tesserae's buttons sit at the
  right of the bar, as both desktops' defaults put them. On macOS, when
  `native_controls` is true, Tesserae's buttons hide, and the bar pads its
  start by `titlebar_inset`'s width (following the event, as it changes in
  fullscreen). `resize_border` defaults to 6 px wherever `tre` honours it.
- Mirror each platform's order (buttons at the left on macOS-like Linux
  themes): the desktop's setting isn't something `tre` reports.

**Q7. Scaffolding and examples.**

- **(decided)** `tesserae new --shell --custom-title-bar` makes an app
  with it on. A new `examples/custom_title_bar` shows the kind and the
  vocabulary, and the existing shell examples stay decorated.
- Turn it on for every new shell app. It's a real change in behaviour on
  some Linux desktops, so it should be asked for.

**Q8. Hot reload and tests.**

- **(decided)** The title bar reloads like any view or shell file.
  Tests drive it headless with `tre`'s `simulate` (a drag press, a
  double-click, `maximized`, `active`, `titlebar_inset`), and CI builds a
  custom-title-bar app with `tesserae build --check` on all three
  platforms. Moving and resizing the window is the OS's, so it's checked
  by hand, as `tre` does.

**Q9. A window border.** Added by the user (2026-09-30): "yes, add the
border to M4". An undecorated window otherwise has no visible edge on
Linux (Windows keeps its shadow; macOS keeps its frame).

- **(decided)** When the window is undecorated, a 1 px border around it
  in `outline_variant`, with a stylesheet class to restyle or remove it.
  It's hidden while maximized or fullscreen, and on macOS. It's an `App`
  option, on by default for undecorated windows, so apps without the
  shell get it too. Rounded corners and a drawn shadow are out of reach:
  they'd need transparent windows from `tre`.

## Milestones

Each is an issue in the GitHub project, under [#24](https://github.com/mindderivative/tesserae/issues/24):

- **M2 — The window on `App`** (Q1, Q4): `decorations` and the other
  window options, the actions, `maximized`/`active` as Signals, the PNG
  icon, and `pointer_cancel` clearing every pressed state.
- **M3 — Title bars in YAML** (Q2, Q5, Q6): `window_region`, the window
  handlers, the `TitleBar` kind, its theme, and macOS's inset.
- **M4 — The app shell and scaffolding** (Q3, Q7, Q8, Q9): the shell's top
  bar as the title bar, `tesserae new --custom-title-bar`, the example,
  hot reload, and the window border.
- **M5 — Docs and checks:** a "Custom Title Bars" guide, the changelog,
  CI building a custom-title-bar app on every platform, and the hand checks.
- **M6 — Release 0.3.0:** merge `0.3.0` into `main` when the user approves,
  then the pre-release and the PyPI check.
