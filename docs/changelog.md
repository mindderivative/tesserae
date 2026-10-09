# Changelog

## 0.5.0 (unreleased)

The YAML language redesign ([#209](https://github.com/mindderivative/tesserae/issues/209)), then the components and the windows work.
The language is specified in `design/yaml-language.md`; the phases land one at a time.

### Changed

- **Bindings are a Python subset** (phase 2). `tesserae.expr` is a sandboxed evaluator (an `ast` node whitelist, name resolution
  through a scope, limits on source size, depth, nodes, steps, ranges, sequences, exponents, integers and text) that replaces the port
  of `tre`'s binding grammar. Python's arithmetic and comparison rules apply (`1 == 1.0` is `True`, unary minus, `None`, `if`/`else`,
  comprehensions, f-strings, whitelisted functions and methods), and a Signal reads as its value (`count` and `count.get()` agree).
  Operators, truth tests, subscripts, formatting and built-ins touch only plain values, built-in containers, mappings, dates, decimals
  and enums, so an application's own object can be read by attribute but none of its methods run from a view. `tesserae.binding`
  keeps `parse_binding`, `evaluate`, `evaluate_value`, `Handle` and `BindingError` over it, and errors now carry the position and a hint.
  See [Binding Expressions](guide/bindings.md).

- **The node model** (phase 3). `tesserae.spec.widgets` is the widget registry (`Property` with type, default, choices, required and model;
  `@widget`, `declare`, `register_widget`, `decl_from_params` for a view's `params:`, and a JSON schema per widget in
  `schema/tesserae-widget-schema.json`). `tesserae.spec.nodes.parse_view` reads a view in the 0.5.0 syntax (`widget:`, optional `name:`,
  properties, `if`, `for`, `key`, `slot`, `state`, `style`, `classes`, `handlers`, `a11y`, `interaction`, `window_region`, `route`, `children`):
  every key and property is checked, every expression compiled, every node given an id from its path, and an error names the file, line and
  column with a suggestion. `tesserae.spec.translate` turns 0.4.x YAML into it; 128 of the 131 files in the repository translate and load, and
  the other three are reported (a dynamic widget name, and a property a call binds that its fragment does not declare). Nothing builds from the
  new syntax yet: that is phases 4 and 5.

- **Composition** (phase 4). `tesserae.spec.compose.Composer` turns parsed views into a live tree of `Instance`s: a view call is replaced by the
  callee's root, its arguments are evaluated in the caller's scope and stay reactive inside the callee, `Slot` holds the call's children (built in
  the caller's scope, with errors for a view that takes none or a slot it lacks), `for:` expands a node per element and a reactive one is
  reconciled by `key:` (kept, added, removed, reordered), `if:` builds and disposes as its expression changes, and `state:` is a per-instance
  `Signal` that survives a recomposition for the same ids. Disposing a composition releases every subscription. Nothing builds `tre` nodes from it
  yet (phase 5).

- **ViewModel binding and a renderer** (phase 5). A `ViewModel` lists the named views it serves in `views`; one instance serves every view with
  one of those names, wherever they are, so a pie chart and a list of the same rows follow one `Signal`. `app.bind(DataViewModel)` makes it once,
  when its first view opens; `app.bind(instance)` uses yours; `app.bind(factory=DataViewModel)` makes one per view instance; a view without a
  `name:` is not bound. `app.open_view("Main")` composes a view written in the new syntax and shows it with the existing builder, keeping it in
  step with its Signals (`for:` and `if:` add and remove real nodes, handlers run in the scope they were written in, a `model` property given a
  bare reference writes the user's edit back). `ViewModel.views[name]` is a handle (`.node`, `.state`, `.show`, `.hide`), `self.show(new, old)` swaps views, and `app.check()` / `check_view` compare every name, action and `expects:` entry of a view with its ViewModel
  without a window. `ViewModel(view)` still works.

- **Style rules** (phase 6). A stylesheet may hold rules by `widget`, `variant`, `size`, `shape`, `classes`, `name`, `part` and `state`
  (`tesserae.spec.rules`). The most specific rule wins (a name, then the number of properties matched, then a state, then the widget alone),
  a later rule wins a tie, an app's stylesheet beats the looks a widget ships, and a node's inline `style:` beats every rule for the fields it
  sets. `hovered`, `focused` and `pressed` are Signals a rule can select on and an expression can read; `disabled`, `selected`, `checked` and
  `expanded` read the widget's own property. `foreground` is no longer valid on every widget: the widgets that draw text or glyphs declare it, and
  the error names them. `self.show(new, old)` swaps one of a ViewModel's views for another.

- **Migration** (phase 7). `tesserae migrate-yaml [PATH] [--write] [--force]` (`tesserae.migrate`) moves a project to the new syntax: views and
  fragments are translated (a fragment becomes a `*_View.yaml`), stylesheets become rules (a component's by `part`, an app's by `widget` and
  `name`), a view with a `*_ViewModel.py` is named after it, header comments are kept, every result is checked with the app's loader and nothing
  is written unless all of it loads (`--force` writes what did). Python is not rewritten: the report lists what each ViewModel needs. A view in
  the old syntax still loads and says once per file how to move on. New: the guide [The View Language](guide/view-language.md), whose YAML
  examples are tested, and the migration table in [Migrating](migration.md#to-050).

- **The text field component** ([#184](https://github.com/mindderivative/tesserae/issues/184), the first of the components). `widget: TextField` is
  the Material text field, a view Tesserae ships with its look as rules: filled and outlined, a label that rises with focus or text, placeholder,
  leading and trailing icons, prefix and suffix, supporting text, a character counter, an error state with its message, disabled, read-only,
  multiline, and a password field with a button that shows the text. `text` is two-way; `on_change`, `on_key` and `on_submit` are events. The bare
  input is the new widget `TextInput` (`placeholder`, `multiline`, `obscured`, `max_length`, `read_only`); the old builder's `kind: TextField` takes
  `placeholder`, `multiline` and `obscured` in its `text:` as well, and `tesserae migrate-yaml` writes the old kind as `widget: TextInput`.
  New with it: shipped views (`tesserae/views/`, found after the project's, replaceable by a view of the same name), `focused`, `focus_visible`,
  `error` and `read_only` as states a rule can select, a widget's state read by its parts' rules, and the icons `visibility`, `visibility_off` and
  `error`.

- **More accessibility states** ([#210](https://github.com/mindderivative/tesserae/issues/210)). `a11y:` takes `expanded`, `selected`, `checked`, `value`,
  `value_min`, `value_max` and `value_step`, in both syntaxes and in `tesserae.a11y`; every field but `role` and `live` can be bound, and `null`
  clears a state tre holds unset. A control still sets its own `checked`, `selected` and `value`.

- **Text extras** ([#211](https://github.com/mindderivative/tesserae/issues/211)). `max_lines`, `letter_spacing` (and `selectable` on `Text`) are properties of
  `Text` and `Link` in the new syntax and keys of `text:` in the old; `max_lines` cuts a long text to that many lines, `letter_spacing` is tracking in pixels, and
  a `Text` with a fixed `width` and no `height` is as tall as the lines it wraps to.

- **Alpha on colours, and the `full` shape** ([#212](https://github.com/mindderivative/tesserae/issues/212)). A colour may end in `@N%` to scale its alpha: `primary@12%`,
  `on_surface@38%`, `"#6750A4@50%"`, wherever a style, a rule, a bound `background`/`foreground`/`border_color` or a `color` property takes one.
  `corner_radius: full` is a pill or a circle.

- **Focus control and keyboard navigation** ([#213](https://github.com/mindderivative/tesserae/issues/213)). `focus('name')` in a handler gives the focus to a named node in the view; `on_press`
  is a handler for the pointer pressing a node (it does not make the node a button), so a container can focus the input inside it; `focus_group: horizontal | vertical | both`
  gives the focusable nodes under a node one tab stop, arrow-key, `Home`/`End` and type-ahead movement. The text field's box focuses its input when pressed.

- **Transitions** ([#214](https://github.com/mindderivative/tesserae/issues/214)). `style: {transition: {background: 150, scale: {duration: 300, easing: spring}}}` makes a change to those
  properties ease instead of jump (opacity, colours, border, corner radius, elevation, blur and the new `scale`, `translate_x`, `translate_y`, `rotation_deg`), with Material's easings, cubic
  beziers or a spring; the first draw does not ease, an app that reduces motion gets the value at once, and a stylesheet rule can carry the transition.
- **Canvas** ([#215](https://github.com/mindderivative/tesserae/issues/215)). `widget: Canvas` with `draw:`, a list of `{rect: [x, y, w, h]}`, `{circle: [cx, cy, r]}` and
  `{path: [points], width: N}` commands, each with a `color` (a role, a CSS colour or `role@N%`). `draw:` may be one `{{ }}` expression, so a canvas
  repaints when the Signals it reads change. It is how a widget draws wavy progress, ticks and graph edges.
- **Icons from a path** ([#216](https://github.com/mindderivative/tesserae/issues/216)). `widget: Icon` takes `path:` (SVG path data) and `view_box:` instead of a name, so any
  glyph can be drawn and tinted like the built-in ones. `tools/import_material_symbols.py DIR` turns a folder of Material Symbols SVGs into
  `src/tesserae/icon_data/material_symbols.json`, which `tesserae.icons` merges under the icons built in. The 18 built-in names are unchanged; no Symbols are bundled yet (see the issue).
- **Timers** ([#217](https://github.com/mindderivative/tesserae/issues/217)). Handlers can call `after(ms, action[, name])`, `every(ms, action[, name])` and `cancel(name)`; `action` is an
  action name or statements run in the handler's scope, and a name restarts a timer of that name (a debounce). `tesserae.timers.Timers(window)` is the same for Python.
  They run on the frame loop until tre has timers (#235) and stop with the view.
- **Scroll state** ([#218](https://github.com/mindderivative/tesserae/issues/218)). `ScrollView.scroll_offset` is drawn (a literal or a Signal; a bound Signal follows the user's scrolling, and
  setting it scrolls), and `at_top`, `at_end` and `scroll_direction` write the position to the Signals or state names they are bound to, for collapse-on-scroll and hide-on-scroll.
- **Pointer capture, cursor and drag events** ([#219](https://github.com/mindderivative/tesserae/issues/219)). New events `on_move` and `on_release`, and handler actions `capture()`,
  `release()` and `cursor(name)` that act on the widget whose handler is running, so a drag keeps following the pointer outside the node.
- **Per-corner `corner_radius`** ([#220](https://github.com/mindderivative/tesserae/issues/220)). `style.corner_radius` takes a list of four (`top_left`, `top_right`, `bottom_right`,
  `bottom_left`) or a mapping of corners and edges (`{top: 12}`, `{left: full, top_right: 4}`), with tokens or pixels; one value is unchanged.

### Removed

- `tests/test_binding_parity.py` and its recording: they asserted `tre`'s quirks (`1 == 1.0` false, 64-bit wraparound, no unary minus).

### Added

- `tests/test_expr.py`: the grammar table row by row, every limit, an escape corpus of about 190 inputs run as expressions and as
  handlers, grammar-based and mutation fuzzers, and a manual mutation check of the sandbox rules (each rule switched off fails a test).

## 0.4.6

The removal stubs are removed ([#113](https://github.com/mindderivative/tesserae/issues/113)).

### Removed

- **The messages for the names 0.4.5 removed**: `tesserae._removed` (`RemovedError`), `tesserae.shell`, and the `use_shell`, `load_shell`
  and `decorations` members of `App` that only raised them, the `--shell` argument of `tesserae new`, and the `_Shell.yaml` check in
  `App.load`. An old name now fails as any unknown name does (`TypeError`, `AttributeError`, `ModuleNotFoundError`, "unrecognized
  arguments"); [Migrating](migration.md#to-045) says what replaced each. Nothing that works changes.

### Added

- `tests/test_no_shell_left.py` keeps the shell file, `AppShell` and `decorations` out of the code, the examples, the tools and the
  workflows.

## 0.4.5

One way to describe a window ([#103](https://github.com/mindderivative/tesserae/issues/103)). The shell file, `AppShell` and
`decorations=` are removed in the phases below; this release is breaking, and [Migrating](migration.md) says how to move.

### Documentation

- **Windows, Docks & Embedded Views** is the guide for the window frame; **App Shell & Docking** is now **Docking from Python**
  (`guide/docking.md`), about `tesserae.docking.Dock` alone. The tutorials, the CLI, hot reload, editor support, projects and
  custom title bar pages, the README and `ARCHITECTURE.md` describe the window view. [Migrating](migration.md) has the
  step-by-step for a shell file, `AppShell` and `decorations`.
- CI and the release workflow run `examples/window_dock` and build `tesserae new --window` apps in place of the shell ones.

### Removed

- **The shell file**: `*_Shell.yaml`, `App.load_shell`, its hot reload, its schema (`tesserae-shell-schema.json`, in the package, the
  site and `tesserae schema`), its project folder kind, the `tesserae new --shell` template and flag, and the
  `examples/app_shell_file` example. Each says what replaces it (a `kind: Window` view) when it is used.

- **The Python app shell**: `tesserae.shell.AppShell` and `App.use_shell`, and the `examples/app_shell` example. `tesserae.docking.Dock`
  stays, for docking panels from Python. Using either removed name says what replaces it.

- **`decorations`**: `App(decorations=)` and `app.decorations` (the opposite of `borderless`, which is the one name now:
  `App(borderless=True)`, `app.borderless`, `borderless: true` on a `kind: Window`). `app.decorations` and `App(decorations=)` raise
  an error saying so. `tre`'s own `Window(decorations=)` is the engine's and is unchanged.

### Changed

- **A removed name says what replaces it.** `decorations=`, `app.decorations`, `App.load_shell`, `App.use_shell`,
  `AppShell`, a `*_Shell.yaml` and `tesserae new --shell` raise a `RemovedError` (a `ValueError`) naming the replacement and the
  migration page, instead of an `AttributeError` that says nothing. The messages are in `tesserae._removed`.

## 0.4.4

A window, a dock and embedded views in the same YAML as every other view ([#95](https://github.com/mindderivative/tesserae/issues/95)).

### Added

- **`kind: Dock` and `kind: DockPanel`**: panels docked around the middle of a view. A `Dock` holds `DockPanel`s, each in the zone
  its `style: {zone: left|right|top|bottom|center}` names (`zone` is a style field, and an error anywhere but on a `DockPanel` in
  a `Dock`); a left or right zone is its panel's `width` wide, a top or bottom one its `height` high. Panels sharing a zone are its
  tabs, titled by `title:`, which the user drags to another zone; a handle between a zone and the middle resizes it (drag, or the
  arrow keys, Home and End). A `DockPanel` inside a `DockPanel` is a split of it, side by side or top and bottom
  (`flex_direction`), with a handle between the halves, which can be split again. A reload leaves a panel the user moved, and the
  sizes they set, where they are, and adds, removes, renames and moves panels the file changes. `view.dock_host("dock")` has
  `layout()` and `restore(layout)` (zones, tabs, sizes and splits as plain data), `size(side)` and `set_size(side, size)`. One
  dock per window; it doesn't depend on the app shell or the shell file. Not yet: dropping a dragged panel onto a split half
  (a drag docks into the five zones).
- **Routed views**: `- {id: settings, view: Settings_View.yaml, route: settings}` in a window view makes the view a screen of the app:
  registered under its name (`Settings`) and the route, shown in its node while it is current, and hidden (out of the layout, with
  its state) when it isn't. `app.navigate`, `show`, `navigate_to`, `back` and the history work as before. New handlers
  `navigate.<Screen>`, `navigate.back` and `navigate.forward` do them from YAML, `app.current_screen` is a value bindings can
  read, and a colour binding can name a theme role. **`NavigationRailScreens`** (and `NavigationRailScreen`) is a navigation rail
  whose destinations go to screens and show which is current. A window view and an app shell can't both be the frame.
- **`kind: Window`**: the root of a `*_View.yaml` that is the whole OS window, with `title:`, `borderless:`, `min_width:`,
  `min_height:`, a `title_bar:` (a `TitleBar`'s keys; the window's own when `borderless`), `children:` for the content, and
  `style:` `width`/`height` for the window's size and `background` for its colour. `app.load("Window")` (or
  `App(window_view="Window")`) loads it, sets the OS window from it, and mounts it for good; it needs no ViewModel. There is one per
  app, and it can't be nested or embedded. Editing it while the app runs sets the window again. **`borderless`** is the new name for an OS
  window without its title bar and borders: `App(borderless=True)` and `app.borderless` (`decorations` still works).
- **A `TitleBar` in a dialog or a sheet**: `buttons: [dismiss]` makes a bar with no window buttons, no OS-controls room and no drag
  region, whose button closes the surface it is in (`surface.dismiss`, a new handler next to `window.*`; `dismiss_surface(node)` from
  Python). **`ViewDialog(window, "Settings_View.yaml")`** is a dialog whose content is a view, with or without a ViewModel
  (`.content`, `.viewmodel`). A view with no ViewModel now has its `window.*` and `surface.*` handlers wired, so a title bar's buttons
  work in a static view. An embedded view takes the colours when its host is re-coloured.
- **`tesserae new --window`** makes a project whose app is one `Window_View.yaml`: a title bar, a `NavigationRailScreens` and two
  routed screens, Main and Settings (`--custom-title-bar` makes it `borderless`). `tesserae add screen` in such a project says
  which `view:` node to add to the window instead of editing `app.py`.
- **Style fields in sections**: the YAML reference's style table, and the schema (an `x-group` on each field, and the group in its
  description, so autocomplete shows it), put each field in one of Size and spacing, Flex, Alignment, Grid, Position, Docking, and
  Paint and effects. Files stay flat. `tesserae.spec.cascade.STYLE_GROUPS` lists them, and a test keeps every field in one.
- **`examples/window_dock/`**: the studio of `examples/app_shell_file/` written as one `Window_View.yaml` (title bar, rail, a dock of
  `view:` panels, routed screens, status bar), with no widgets made in Python. It checks itself, and the tests read what it
  draws back from the window's snapshot.
- A guide page, [Windows, Docks & Embedded Views](guide/windows-and-docks.md), and component pages for Window, Title bar, Dock,
  Dock panel and Routed views.
- **`view:`** shows another `*_View.yaml` where it is: `- {id: left, view: Left_View.yaml, with: {size: 3}, style: {width: 220}}`
  (or by name in a project). It is a view of its own, with its own ids and its own ViewModel when there is one
  (`Left_ViewModel.py`), and it needs none: a view with no ViewModel is static. `view.embedded(id)` and `view.viewmodel` read
  them from Python; `tesserae.component.embed` is the function. See [Components & Embedding](guide/components.md#in-yaml-view).

## 0.4.3.3

tre 0.5.5 ([#94](https://github.com/mindderivative/tesserae/issues/94)).

### Requirements

- **`tre` 0.5.5 or newer, below 0.6** (0.4.3.2 needed 0.5.4). On KDE Wayland, tre 0.5.4 presented every frame with a vsync
  barrier, and while a window was being resized the compositor then held back the next resize for up to a second, so the
  window trailed the mouse and kept catching up after the button was released: undecorated and native windows both. 0.5.5 presents
  without the barrier while a window is being resized and goes back to vsync after it. Tesserae's code is unchanged.

## 0.4.3.2

A TextField in dark mode ([#93](https://github.com/mindderivative/tesserae/issues/93)).

### Fixed

- **A `TextField`'s text was dark in a dark scheme**, dark ink on a dark field. What is typed is the theme's
  `on_surface` now (or the style's `foreground`, if it has one), and the caret is the theme's `primary`, and both follow
  the app between light and dark.
- A sweep of every component for the same fault found no other: in both schemes no component's text or icon is
  unreadable against what is behind it, and a component built in one scheme and switched to the other by the app
  looks as one built in it (`tests/test_component_colours.py`).

### Added

- **Text fields** has a component page (it was missing): the `TextField` node kind, how its colours come from the
  theme, binding it two ways, and its limits. The Components index names a node kind (`kind: TextField`, `kind: Svg`)
  where it used to say "Python only".

## 0.4.3.1

Style files ([#92](https://github.com/mindderivative/tesserae/issues/92)).

### Changed

- **A `*_Style.yaml` says what it is.** Its fields go under a `style:` key, with an optional `id:` naming the style,
  like the style in a view: `{id: row_style, style: {flex_direction: horizontal, gap: 8}}`. A file that is only the
  fields still works, so nothing has to change.

### Added

- **`tesserae-style-schema.json`**, a schema for `*_Style.yaml` (`tesserae schema` lists it, `--settings` maps it), so
  an editor checks a style file and says what each field is. The tutorials' `row_Style.yaml` use the new form.

## 0.4.3

Documentation ([#91](https://github.com/mindderivative/tesserae/issues/91)).

### Added

- **[Tutorial: The Same App as a Project](tutorial-project.md)** builds the Tutorial's Tasks app as the project
  `tesserae new` makes, in six steps (`examples/tutorial_project/`, run by the tests): files in `Views/`, `ViewModels/`,
  `Components/`, `Themes/` and `Styles/` found by name, `Repeater` rows by name, a theme and stylesheet by name,
  `tesserae add screen`, a shell by name, with a table comparing a flat folder with a project. The flat
  [Tutorial](tutorial.md) and the Getting Started, Overview and Projects pages point to each other.

### Fixed

- The Projects guide listed the `Repeater` and `instantiate` row twice.

## 0.4.2

Names for lists and embedded components ([#89](https://github.com/mindderivative/tesserae/issues/89)), SVG
([#88](https://github.com/mindderivative/tesserae/issues/88)), and what the engine's 0.5.4 adds
([#90](https://github.com/mindderivative/tesserae/issues/90)): gradients and effects, rich text, touch and files,
window options, the OS's preferences for less motion and more contrast.

### Requirements

- **`tre` 0.5.4 or newer, below 0.6** (0.4.1 needed 0.5.1). 0.5.4 adds the `svg` node, and lays a text node's width out
  rounded up so a width from `measure_text` fits its text.

### Added

- **`kind: Svg`**: the engine draws a whole SVG document (shapes, gradients, patterns, clips, masks, text, a blur or
  drop-shadow filter), scaled to fit its box. `svg: {src: logo.svg}` is a `.svg` or `.svgz` file next to the view,
  `svg: {content: "<svg ...>"}` the document itself, and `style.foreground` is what `currentColor` means, so a
  monochrome icon follows the theme. Tesserae decodes the raster pictures in a document (`<image href="...">`: PNG,
  JPEG, GIF, WebP) for the engine, which decodes no image format: found next to the SVG file and inside the view's
  folder, at most 8192 pixels on a side, a `data:` URL's picture too (its `href` is rewritten to a key of its own). A
  picture that can't be found or decoded is an error naming it. Hot reload watches the file and its pictures.
  `tesserae.widgets.svg(window, source, width, height, color=)` is the Python form.
- **`Repeater` and `instantiate` find views and ViewModels by name**, as `app.load` does: `Repeater(view, items,
  "Row", into=node)` and `instantiate(view, "Row", into=node)` use `Views/Row_View.yaml` and `RowViewModel`, found in the
  app's project. `viewmodel_cls` and `into` are now optional in the signature (`into` is still needed: it is an error
  without it), and a path and a class still work. A name with no app is an error that says there is no project.
  One function in `tesserae.project` (`resolve_view`) does the resolving for `app.load`, `instantiate` and `Repeater`.
- **Gradients** in a style's `background`, `foreground` and `border_color`: a CSS-like string
  (`linear-gradient(90deg, primary, tertiary)`, `radial-gradient(at 30% 30%, ...)`, `conic-gradient(from 90deg, ...)`,
  stops that are theme roles or colours, with optional places) or a mapping (`{gradient: linear, angle: 90, stops: [...]}`).
  See [Gradients & Effects](guide/effects.md).
- **Effects as style keys**: `blur`, `backdrop_blur` (with a translucent `background`, a frosted surface), `blend_mode`
  (CSS's sixteen), `filter` (`saturate`, `brightness`, `contrast`, `grayscale`, `hue_rotate`, `invert`, `sepia`),
  `sticky` (a sticky header in a scroll view) and `cursor` (a name, or `{src: file.png, hotspot: [x, y]}` read with the view).
- **Rich text**: `text.runs` makes a `Text` of styled pieces (`color`, `weight`, `italic`, `underline`, `strikethrough`,
  `font_size`, `font_family`, `link`), measured run by run; a run with a `link` is `primary` and underlined and calls the
  node's `on_link` handler with `event.href`. `text.selectable: true` lets the user select and copy a `Text`.
  See [Rich Text & Links](guide/rich-text.md).
- **Touch, gestures and files as handlers**: `on_tap`, `on_long_press`, `on_pan`, `on_pinch`, `on_touch_start`,
  `on_touch_move`, `on_touch_end`, `on_touch_cancel`, `on_file_hover`, `on_file_hover_cancel`, `on_file_drop` and `on_link`,
  and `app.on_file_drop(handler)` for a drop anywhere on the window. See [Touch, Gestures & Files](guide/gestures.md).
- **Window options** on `App`: `dpi_scaling` (on by default), `present_mode`, `transparent`, `blur_behind`,
  `click_through`, `glyph_cache` and `system_fonts` (also `tesserae.set_system_fonts()`), with `app.scale_factor` and
  `app.transparent_active`. See [Window Options & the OS](guide/window-options.md).
- **The OS's wishes**: `reduced_motion` and `high_contrast` follow the OS (or are fixed) and can be set with
  `app.set_reduced_motion()` and `app.set_high_contrast()`. Reduced motion makes every animation take no time and stops
  the indeterminate indicators; high contrast re-themes at the highest contrast level (`Theme.contrast`,
  `tokens.color_scheme(contrast=)`). `tesserae.motion.duration(window, ms)` is for your own animations.
- **A spring easing**: `Theme.easing("spring")` and `Theme.spring(bounce)`.
- **Frame statistics**: `app.frame_stats()`, `app.profile_nodes`, `app.start_trace(path)` / `stop_trace()`,
  `app.stats_handle()`, and `app.stats_overlay = True` (or `TESSERAE_STATS=1`) for a readout of the frame rate in the window.

### Changed

- A window is scaled to its screen by default (`App(dpi_scaling=False)` is the old way), and colours are drawn exactly
  as written. See [Migrating](migration.md#to-042).

## 0.4.1

Projects ([#87](https://github.com/mindderivative/tesserae/issues/87)).

### Added

- **A project's files are found by name.** `Views/`, `ViewModels/`, `Components/`, `Themes/` and `Styles/` under
  the app's root are the standard places: `app.load("Main")` finds `Views/Main_View.yaml` and
  `ViewModels/Main_ViewModel.py` (class `MainViewModel`), `component: Name`, `App(custom_theme="Name")`,
  `stylesheet="Name"`, `app.load_shell("Name")`, a shell panel's view and a `style: x_Style.yaml` find theirs.
  `App(root=)` is the root (the script's folder by default), `search=[...]` adds folders, `recursive=True` looks
  through the whole project, and a name in two places is an error naming both. Paths still work. `app.project` is
  the `tesserae.project.Project`.
- `app.load(view)` takes the ViewModel class from the view's name when it isn't given.

### Changed

- **`tesserae new <name>` makes a project**: a `.venv` with Tesserae installed in it (`--no-venv` skips it),
  the five folders, `app.py`, and a `Main` screen in `Views/` and `ViewModels/`. `tesserae add screen` writes
  into those folders and loads the screen by name. An app laid out the old way still works, and `add screen`
  follows its layout.

## 0.4.0

A simpler layout vocabulary ([#86](https://github.com/mindderivative/tesserae/issues/86)). Breaking: see
[Migrating](migration.md#to-040).

### Changed

- **`align_content` places a node's children** as one of nine positions (`top_left` to `bottom_right`),
  replacing `align_items` and `justify_content`; **`spread`** (`between`, `around`, `evenly`) shares out the
  room along the layout; **`flex`** (`none`, `expand_horizontal`, `expand_vertical`, `fill`) is a node's own
  sizing, replacing `flex_grow`, `flex_shrink` and `flex_basis`; `align_self` takes the nine positions.
  `align_wrapped` (a wrapping node's lines), and `align_tracks` and `align_cells` (a grid's tracks, and where
  items sit in their cells) are for the nodes that have them; they replace the old `align_content`,
  `justify_content` and `justify_items` there. The engine's names are refused, with what replaces each.
- **A node is never squeezed unless it says so** (`flex: none` is the default). Every hand-made
  `flex_shrink: 0` is gone from the built-in components, bars and widgets. Two built-in components that
  were being squeezed look right now: a selected filter chip's check mark is 18 px, not 14, and a dialog's
  headline has its height.
- The 77 built-in components, the title bar, the tutorial, the examples and the guide use the new names.
  `tesserae.spec.layout` turns them into the engine's in one place.

## 0.3.6

`text_align` on the built-in labels ([#85](https://github.com/mindderivative/tesserae/issues/85)).

### Fixed

- **`text_align: center` and `end` work on a `Text` with no width.** The engine aligns text within the
  width it is laid out in, and a `Text` sized to its text has no room to move in, so a centred label was
  drawn at the left of its button. A `Text` that is `center` or `end` aligned and has no `width` of its
  own now fills its parent's width, with its text's width as the least. The built-in centred labels
  (buttons, chips, split buttons, badges, date and period cells) are plain `text_align: center` again, with
  no `wrap: none` (0.3.5 gave them it, which stopped the alignment).

## 0.3.5

Text that wrapped when it shouldn't ([#84](https://github.com/mindderivative/tesserae/issues/84)).

### Fixed

- **A label no longer wraps onto a second line when it fits.** A `Text` or `Link` with no `width` is
  measured to fit its text, and the engine rounds an explicit width down to a whole pixel, so a label a
  fraction of a pixel wider than its box wrapped: `ButtonFilled` with `label: Add a task` showed
  "Add a / task" at any button width. Measured sizes are rounded up now, for every `kind: Text`, `Link`,
  `tesserae.widgets.text` and dock tab.

### Added

- **`text: {wrap: word | none, overflow: clip | ellipsis}`** on `Text` and `Link`. `wrap: none` keeps one
  line, `overflow: ellipsis` ends a line that doesn't fit with an ellipsis. In the schema, the YAML
  reference and the layout guide. The `Text` and `Link` components take them as parameters.

### Changed

- **The labels of the built-in components are single lines.** Buttons, chips, split buttons, badges,
  tooltips, list, menu, tree and drawer items, date and period cells, and the accordion, top and status bars
  end a label that doesn't fit with an ellipsis; extended FABs, rail items and tabs keep one line without
  one. A dialog's words and a snackbar's message still wrap. A test lays every component out with short and
  long labels and fails if one wraps.
- A button's or chip's stylesheet has 12 px of padding either side of the label.

## 0.3.4

The documentation, rebuilt ([#83](https://github.com/mindderivative/tesserae/issues/83)), and the
stylesheets of the built-in components.

### Added

- **A stylesheet for each built-in component.** Every `<Name>_Component.yaml` now holds a component's
  structure, and its look is in `<Name>_Stylesheet.yaml`: a list of `{id: <part>, style: {...}}` rules whose
  values may be the component's `{{ parameters }}`. What a component expands to is unchanged. A
  `<Name>_Stylesheet.yaml` next to your views goes over the built-in one, field by field.
- **Your own fragments are found next to the view.** A `*_Component.yaml` (and its stylesheet) in a view's
  folder is used by `component:` with no `component_dirs=`.
- **Documentation:** a generated [Python API](api/python.md) and [YAML reference](api/yaml.md); a page for
  each of 43 MD3 [components](components/index.md) and 76 [stylesheets](stylesheets/index.md); a
  [Themes](themes/index.md) page; a [Tutorial](tutorial.md); [Migrating](migration.md); and a guide to the
  [`tesserae` command](guide/cli.md). Tests keep the generated pages current and run every example on them.
- The theme schema also covers `*_Stylesheet.yaml` (including a component's) and `*_Theme.yaml` in
  `tesserae schema --settings`.

### Changed

- Getting Started is shorter; the Guide, Installation and Architecture pages describe what Tesserae is,
  with no release or milestone history (that is here and in Migrating).
- Docstrings that appear on the API page are free of history.

## 0.3.3

Three things a user found testing: the shell's bars, theme roles without a
theme, and styling the shell's parts.

### Added

- **Every part of a shell takes a `style:`**
  ([#81](https://github.com/mindderivative/tesserae/issues/81)): the shell
  itself, `top_bar`, `navigation`, `status_bar`, `content` and each zone
  (`{size, style}`), in a `*_Shell.yaml` and in code (`style=` on
  `top_app_bar`, `status_bar` and `navigation_rail`; `AppShell(styles=)`;
  `shell.set_style`). The top bar's height was impossible to set before.
  Hot reload applies a changed style and puts back the shell's own values
  when one is removed. The shell schema knows them.

### Fixed

- **A shell's top bar and status bar no longer shrink when the window is
  short** ([#80](https://github.com/mindderivative/tesserae/issues/80)). They
  kept `tre`'s default `flex_shrink` of 1, so a short window squeezed the top
  bar from 64 px down to its title's height (28) and the status bar from 24
  to 16. They are fixed-height bars now, wherever they are placed. (The
  navigation rail never shrank.)

### Changed

- **Theme roles work in an app with no `theme_seed`**
  ([#82](https://github.com/mindderivative/tesserae/issues/82)).
  `background: surface`, and the built-in `kind: TitleBar`, failed there with
  "unknown color identifier". A view with no theme resolves roles from MD3's
  baseline palette (the light one), as an unthemed widget already did; a
  `theme_seed=` still themes the app and lets it follow light and dark. A
  misspelt role now says what was meant (`did you mean 'surface'?`); a name
  that is no role keeps `tre`'s wording.

## 0.3.2

YAML schemas for editors ([#79](https://github.com/mindderivative/tesserae/issues/79)),
`tre` 0.5.1, and the work-around for the bug it fixed off by default
([#78](https://github.com/mindderivative/tesserae/issues/78)).

### Requirements

- **`tre` 0.5.1 or newer, below 0.6** (0.3.1 needed 0.5.0.1). 0.5.1 lets
  other Python threads run while a window sits idle (`tre`
  [#92](https://github.com/mindderivative/tre/issues/92)), the cause of the
  hot-reload stall 0.3.1 worked around. It also adds `tre.Shader` and
  paints `fill`, borders and `corner_radius` on more node kinds than before;
  Tesserae sets none of those on a kind that used to ignore them, so
  nothing in its views changes.

### Added

- **YAML schemas for Red Hat's YAML language server** ([#79](https://github.com/mindderivative/tesserae/issues/79)):
  `tesserae-yaml-schema.json` (a view), and
  `tesserae-shell-schema.json`, `tesserae-component-schema.json` and
  `tesserae-theme-schema.json`, JSON Schema draft-07. An editor suggests
  node kinds, style fields, colour roles, layout values and a built-in
  fragment's parameters, shows what each means, and flags a typo. They come
  with the package, are published at
  `https://mindderivative.github.io/tesserae/schema/`, and are written by
  `tools/generate_yaml_schema.py` from Tesserae's own code. New command:
  `tesserae schema` says where they are, and `tesserae schema --settings`
  prints the `yaml.schemas` setting. See
  [Editor Support](guide/editor-support.md).

### Changed

- **`run(keepalive=)` is off by default**, where 0.3.1 turned it on with
  `hot_reload=True`. A hot-reload watcher, or any thread calling
  `thread_handle().call_soon`, now reaches an idle window without a tick.
  `True` and a number still tick, for code that wants the loop woken
  regularly; `None` is accepted as `False`. A thread busy running Python
  can delay a wake-up by up to about 5 ms (the GIL's switch interval).

### Tests

- The two tests that held an idle window with no keepalive, written to
  fail once `tre` was fixed, are gone; `test_keepalive_idle.py` now checks
  that threads and hot reload reach an idle window with the default.

## 0.3.1

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

- **`run(keepalive=)`, on by default with `hot_reload=True`** ([#77](https://github.com/mindderivative/tesserae/issues/77)).
  `tre`'s window, left idle, stops other Python threads from running, so a
  hot-reload watcher couldn't hand a reload over until something else woke
  the window: an edit to a view could sit unseen while the window was
  dragged, resized and clicked. `keepalive` keeps the window ticking (every
  0.02 s, or the seconds you give). `None`, the default, follows
  `hot_reload`; `True` and `False` choose, so anything else that needs
  threads to run in an idle window (an IDE, say) can use it without hot
  reload. A work-around for `tre`: once `tre` is fixed the default becomes
  off. Found by a user trying Getting Started.
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
Following the custom-windowing design.

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
