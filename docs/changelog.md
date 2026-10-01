# Changelog

## 0.3.1 (unreleased)

Things the new [Getting Started](getting-started.md) walk-through ran
into ([#72](https://github.com/mindderivative/tesserae/issues/72)).

### Added

- **`App.run()` needs no screen** ([#73](https://github.com/mindderivative/tesserae/issues/73)).
  It starts when the window has something to show: a screen `show()` made
  current, or nodes added to `app.window.root` by calls. An app built
  entirely in Python no longer has to make an empty `View` first, and an
  empty window runs. Registering screens and showing none is still a
  `RuntimeError`, now saying both ways out (an undecorated window's border
  doesn't count as content).
- **`text_align` in a YAML `text:` block** ([#74](https://github.com/mindderivative/tesserae/issues/74)):
  `start` (the default), `center` or `end`, on a `Text` and a `Link`, as
  `tre` names it. Before, the key was silently ignored. A wrong value is
  an error naming the widget, and a `TextField` doesn't take it.

- **A closest-match hint on a misspelt name** (#76): a misspelt style
  field, node field, `kind` or `a11y` field now says what was probably
  meant, as in `unknown style field(s) ['foregorund'] -- did you mean
  'foreground'?`. A name that resembles nothing is not guessed at. Hot
  reload logs it the same way.

### Documentation

- The Getting Started page walks from a fresh Linux install to a first
  window and node, declaratively and imperatively, with runnable programs
  in `examples/getting_started/`; the API page lists `App`'s window
  options, routing members and `App.of`; the index, README and
  installation pages are brought up to 0.3.

## 0.3.0

Custom windowing on `tre` 0.5.0.1: Tesserae draws the window's title bar and
borders ([#24](https://github.com/mindderivative/tesserae/issues/24)).
Following the [design](design/custom-windowing.md).

### Requirements

- **`tre` 0.5.0.1 or newer, below 0.6** (0.2.x needed 0.4.4 or newer, below
  0.5). 0.5.0.1 rather than 0.5.0: a real click in a text field panicked
  (`RefCell already borrowed`) in `tre` 0.4.4 and 0.5.0, and 0.5.0.1 fixes
  it ([#63](https://github.com/mindderivative/tesserae/issues/63), `tre` #51).

### Checked by hand

Moving, resizing, maximizing, the buttons and the window border were tried
by hand on Linux, under X11 (it found the text-field panic above and an
example's overlapping text, [#62](https://github.com/mindderivative/tesserae/issues/62)).
Wayland, Windows and macOS were checked by the headless tests and by CI,
which builds and runs a custom-title-bar app on each, but not by hand:
tell us if a title bar misbehaves on one of them.

### Added

- **The window on `App`** ([#40](https://github.com/mindderivative/tesserae/issues/40)):
  `decorations` (a window with no OS title bar or borders, for a title bar
  the app draws), `resize_border` (6 px by default when undecorated),
  `min_width`/`min_height`, `fullscreen`, `system_menu` and `icon` (an
  image file), as `App` options and live properties, and `app.platform`.
  The actions `minimize()`, `maximize()`, `restore()`,
  `toggle_maximized()` and `close()`, and `app.maximized` and
  `app.active` as read-only Computeds for bindings.
- **Title bars in YAML** ([#41](https://github.com/mindderivative/tesserae/issues/41)):
  `kind: TitleBar` (icon, title, the app's own content, and minimize,
  maximize/restore and close buttons; Material 3 colours by class, faded
  while the window isn't focused; on macOS, room for the traffic lights);
  `window_region: drag | none` on any node; the handlers
  `window.minimize`, `window.maximize`, `window.restore`,
  `window.toggle_maximized` and `window.close`; `app.titlebar_inset` and
  `app.native_controls`. Three window glyphs in the icon set, and
  `visible` can be bound.
  A TitleBar hot-reloads.
- **Undecorated app shells** ([#42](https://github.com/mindderivative/tesserae/issues/42)):
  in an undecorated app the shell's top bar is the title bar
  (`top_app_bar(..., window_controls=)`, from code or a shell file, which
  hot-reloads as one); a 1 px window border in `outline_variant`, hidden
  while maximized or fullscreen and on macOS (`window_border`, and the
  `window_border` class); `tesserae new --shell --custom-title-bar`; and
  `examples/custom_title_bar`.
- **A "Custom Title Bars" guide** ([#59](https://github.com/mindderivative/tesserae/issues/59)),
  bringing the title bar, the border and each platform's differences
  together.

### Changed

- Every pressed widget (state layers, the split button, splitters, dock
  tabs, sliders and other drags) releases on `pointer_cancel`, which
  `tre` 0.5.0 sends when the OS takes a press, as on `pointer_up`.

## 0.2.1

Releasing an app (M77, M78) and `tre` 0.4.3 and 0.4.4 (M79, M80), tracked
from here on in the [GitHub project](https://github.com/users/mindderivative/projects/2)
(release [#23](https://github.com/mindderivative/tesserae/issues/23)).

### Requirements

- **`tre` 0.4.4 or newer, below 0.5** (was 0.4.2 or newer). `tre` 0.5, with
  custom windowing, comes with Tesserae 0.3.0.

### Added

- **`tesserae build`**: an app as one executable, which its users run with
  nothing else installed. `pip install "tesserae-ui[build]"` adds
  PyInstaller; `--check` runs the result and checks it draws frames. Built
  and checked in CI on Linux, macOS and Windows. See
  [Releasing Your App](guide/releasing.md).
- **`tesserae build --installer`**: the platform's installer, from a
  one-folder build. On macOS, a `.app` (its version, identifier and
  publisher in `Info.plist`) in a `.dmg`. On Windows, an Inno Setup
  installer that needs no admin rights, with a Start-menu entry and an
  uninstaller; Tesserae fetches a pinned Inno Setup if there's none.
  On Linux, an AppImage, a `.deb`, a pacman package, an `.rpm` and a
  Flatpak (the `.deb` and pacman package written by Tesserae,
  `appimagetool` fetched and pinned, the `.rpm` and Flatpak made when
  `rpmbuild` and `flatpak-builder` are installed, and reported otherwise).
  A PNG `--icon` works on every platform.
- The [Releasing Your App](guide/releasing.md) guide: building, what goes
  in, each installer and how its users install and uninstall it, and
  signing and notarizing with your own certificates.
- `TESSERAE_MAX_FRAMES=n` stops `app.run()` after `n` frames, and
  `TESSERAE_FRAMES_REPORT=<file>` writes how many it drew, for automated
  runs.

### Changed

- A built (frozen) app runs without hot reload, which has no source files
  to watch.
- On macOS, `tesserae build` without `--installer` makes only the single
  executable, which runs from a terminal; PyInstaller 7 won't make a `.app`
  from one file, so the `.app` comes with `--installer`.
- A bare number as a grid track list (`grid_auto_rows: 96`) is passed to
  `tre`, which takes it since 0.4.3; Tesserae no longer converts it.
- On `tre` 0.4.4, scrolling chains as in a browser: a wheel or scroll key
  an inner `ScrollView` can't use (at its end, or its content fits) goes
  to the one outside it.
- On `tre` 0.4.3, a `scroll_offset` set past the end is held at the end at
  once (and written back through `two_way`), and scroll keys held with
  Ctrl, Alt or Meta no longer scroll.

### Fixed

- Hot reload no longer reads a file in the middle of a save. On macOS a
  save could arrive as one event while the file was still empty, so a
  reload failed ("'NoneType' object has no attribute 'get'") and missed
  the edit; the watchers now wait for a change to settle
  ([#39](https://github.com/mindderivative/tesserae/issues/39)).

## 0.2.0

Everything since 0.1.0 (M53-M76).

### Requirements

- **Python 3.12 or newer** (0.1.0 said 3.9).
- **`tre` 0.4.2 or newer** (`tesserae-engine` on PyPI; 0.1.0 needed 0.3.5.2),
  installed with Tesserae.
- One `pip install tesserae-ui` installs everything, as prebuilt wheels, on
  Linux x86-64, macOS on Apple silicon and Windows x64 -- checked in CI on all
  three, on Python 3.12 and 3.14, where the full test suite also runs.

### Added

- **App structure**
    - Shared state: `App(state=...)`, reached as `self.state` (and the app as
      `self.app`) from any ViewModel on the app's window, and as
      `{{ state.x.get() }}` in any binding; `App.of(view)`.
    - Routing: `app.navigate(name, **params)`, `back()`, `forward()`,
      `on_navigated(params)` on the screen's ViewModel, `can_go_back` /
      `can_go_forward`; routes and deep links with `app.route("notes/{id:int}",
      "Note")`, `navigate_to("notes/42")` and `location`. Alt+Left/Right and the
      mouse's side buttons go back and forward.
    - `tesserae new <name> [--shell]` makes a runnable app, and `tesserae add
      screen <Name>` adds a screen to it.
- **Layout**
    - The rest of flexbox in a view's style and stylesheets: `flex_wrap`,
      `align_self`, min/max sizes, `aspect_ratio`, `position` with `x`/`y`,
      `z_index`, `clip_children`.
    - CSS Grid: `display: grid`, track templates (`fr`, `repeat()`,
      `minmax()`), auto tracks and flow, `grid_column`/`grid_row` placement,
      row and column gaps, grid alignment.
    - `kind: ScrollView`, with keyboard scrolling, focus reveal and
      `two_way: scroll_offset`.
- **Components and styles**
    - A `component:` call takes `handlers:`, `bindings:`, `two_way:`, `a11y:`,
      `interaction:` and `classes:` for its root, so a button fragment can be
      clicked.
    - `disabled:` as a key or a binding on any node (announced, not focusable,
      no feedback, handlers off, faded).
    - A node's `style:` can name a `*_Style.yaml` file; `*_Stylesheet.yaml` and
      `*_Theme.yaml` name the other kinds.
    - Fragment params with defaults, `when:` and `{if:, then:, else:}`;
      per-item styling for `repeat:`; a theme's `components:` in the cascade.
    - YAML kinds for `SpinBox`, video (a `frame` binding on `Image`) and node
      graphs (`NodeGraph`, `GraphNode`).
    - `tesserae.widgets.text`, and every widget follows its theme's
      `typography:`.
    - `pagination` windows long runs with an ellipsis.
    - CSS wide-gamut colours: `oklch()`, `oklab()`, `lch()`, `lab()`, `hwb()`
      and `color()`.
- **Development**
    - Hot reload for components in any view, and for components first used
      while the app runs.
    - A shell file's removed panel is undocked while the app runs;
      `App(dark="system")` starts in the OS's appearance.
    - An open overlay follows a window resize.

### Changed

- A shell file's navigation rail now `navigate`s (with history) instead of
  jumping with `show`.
- `load_theme` and `load_stylesheet` refuse a file named for another kind
  (`*_Style.yaml`, `*_Stylesheet.yaml`, `*_Theme.yaml`); other names load as
  before.
- A long `pagination` run's buttons are slots (`slot0`, ...), not one per page.
- `App.run()` raises `RuntimeError` when a window's GPU can't be set up (from
  `tre` 0.4.0; before, the process exited with status 0).

### Fixed

- On macOS, a hot-reload watcher could reload files that hadn't changed
  (writes from just before the watch began); it now skips an event that
  changed nothing.
- Windows: Tesserae's own file reads name UTF-8, rather than the system code
  page.

## 0.1.0

The first release on PyPI, as `tesserae-ui` (2026-09-28).
