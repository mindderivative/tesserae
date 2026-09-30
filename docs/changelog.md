# Changelog

## Unreleased

### Requirements

- **`tre` 0.4.3 or newer** (was 0.4.2).

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
  Linux follows. A PNG `--icon` works on every platform.
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
- On `tre` 0.4.3, a `scroll_offset` set past the end is held at the end at
  once (and written back through `two_way`), and scroll keys held with
  Ctrl, Alt or Meta no longer scroll.

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
