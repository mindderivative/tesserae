# Changelog

## 0.5.0.28

### Fixed

- **A node anchored to a hidden node is hidden with it** ([#282](https://github.com/mindderivative/tesserae/issues/282)). With `style: {anchor: target}`, hiding the target with `visible: false` (its own, or a container's it is in) left the anchored node at the window's top left corner, drawn and pressable, because tre puts a node whose anchor is hidden there. The node is now hidden while its anchor, or anything it is inside, is hidden, in the same step, and shown when the anchor is back (its own `visible: false` still wins). It already followed an anchor removed by an `if:`. The guide no longer says to hide both.

### Known

- `transition:` still does not ease an anchored placement.

## 0.5.0.27

### Changed

- **A handler's assignment to a name it cannot write is found when the view loads** ([#277](https://github.com/mindderivative/tesserae/issues/277)). `r = 1` on a loop variable, a write to a plain param, a Computed, a ViewModel attribute that is not a Signal, `hovered`, or a misspelt name was an error only when the handler ran. It is now a load error with file, line and column and, for a typo, the names that can be written (`'cuont' is not writable here (did you mean 'count'?)`). It is the same check a call to an unknown action already had. No shipped view or example was affected. A handler written as the text of an `after(...)` or `every(...)` call is still checked only when it runs.

### Documentation

- [Two-way properties](guide/view-language.md#two-way-properties) is now the one place that says what a view may write back, answered by running the code: which names a handler may assign; that a property given anything but one bare reference to a writable Signal is one-way, and the user's edit stays on screen until the value next changes; what a `model: true` param does with a Signal, an expression, a literal and nothing; and that a `state:` keeps its value over an edited starting value when a view is reloaded. The bindings and component pages say the same and point to it. `tests/test_two_way_state.py` pins each answer.

## 0.5.0.26

### Fixed

- **A labelled control is placed as a whole** ([#281](https://github.com/mindderivative/tesserae/issues/281)). A `Checkbox`, `RadioButton` or `Switch` with a `label:` is a row of the box and its text, but `position`, `x`, `y`, the insets, `margin`, `flex`, `align_self`, `z_index`, the grid fields and the transforms were applied to the box inside it, so `right: 8` put the box outside its parent. They now go to the row: it is the node the view places, and the one an `anchor:` sits against (or is) and a `transition:` eases. A control without a label is as it was. `visible` hides the label with the box.

## 0.5.0.25

### Added

- **Place a node against another node** ([#280](https://github.com/mindderivative/tesserae/issues/280)). With tre 0.5.7, `style: {anchor: target, placement: top_end, offset: [6, -6]}` sits a node on the corner of a named node, wherever either is written, and keeps it there as the target moves, with no lag. The node stays in the tree: a parent's `clip_children` cuts it and `z_index` orders it. `placement` is a side (`below`, `above`, `start`, `end`) or a corner (`top_start`, `top_end`, `bottom_start`, `bottom_end`, `center`); `anchor: parent` is the node it is written inside; the nearest node of the name wins (a `for:` row's own node first). The fields come from rules and expressions, a mistake is found at load with its position, an unknown anchor name is an error naming the nearest name, and the editor schemas know them. If the anchor goes (an `if:`) the node is hidden until it is back. `Overlay` takes the corners too, with `offset` and `flip` (`false` keeps a side where it is put instead of flipping it), and `Tooltip` accepts corner placements. `design/tre-requests/anchored-layout.md` is marked done.

### Known

- If the anchor is hidden with `visible: false`, tre leaves the anchored node at the window's corner; hide both. `transition:` does not ease a placement.

## 0.5.0.24

### Added

- **Insets, and sums as sizes** ([#279](https://github.com/mindderivative/tesserae/issues/279)). With tre 0.5.7, `left`, `top`, `right`, `bottom` and `inset` are style fields: `left: 8, right: 16` stretches an absolute node across its parent less 8 and 16 pixels, `inset: 4` fills the parent less 4 each side, and on a node in the flow an inset moves it from its place. An inset is a number (negative is allowed), a percentage or `auto`; `x` and `y` are `left` and `top` and say the same thing (giving `x` with `left` or `inset` in one `style:` is an error, found at the line). A rule's `inset` gives way to an edge the node, or a more specific rule, says itself. A size may be a sum, `calc(100% - 16)` or `100% - 16` (numbers, percentages and `16px`, joined by `+` and `-` with a space each side), and `width`/`height` take `fit-content`. These already reached tre untouched; what is new is that they are part of the language: a size or inset tre would refuse (`40px`, `10vw`, `stretch`, `100%-16`, a negative size, `calc` in a limit or an inset) is refused where it is written, with file, line and column and what to write instead (it was tre's message with no position, when the view was built), the same for a stylesheet rule, and the editor schemas know them (the language-server check was not re-run). An inset cannot ease (tre does not animate it): `transition:` takes `x` and `y`. The check agrees with tre on a corpus of values (`tests/test_sizes.py`), so it fails if tre's grammar moves.

### Fixed

- **A ListItem's divider was never drawn.** It was placed at `y: 100%` with no width, so it was 0 wide. It now takes `left: 16, right: 0, bottom: 0`: 16 pixels in from the left edge to the right edge, on the item's bottom edge. The Carousel's caption and the VideoPlayer's controls bar used `y: 100%` and a negative `translate_y` for the same thing; they take `bottom: 0` now, and draw where they did.

### Known

- A control with a `label:` (`Checkbox`, `RadioButton`, `Switch`) takes `position`, `x`, `y` and now the insets on its inner box, not on the row that holds the box and its label, so an inset on one lands in the wrong place ([#281](https://github.com/mindderivative/tesserae/issues/281)). The layout guide says so.

## 0.5.0.23

### Changed

- **Requires tre 0.5.7** ([#278](https://github.com/mindderivative/tesserae/issues/278)). `tesserae-engine>=0.5.7,<0.6`. 0.5.7 adds what Tesserae asked of it on 2026-10-11 (tre#178, tre#179) and more: sizes that take `calc(100% - 16)` and mixed units, and `fit-content` for text; `left`, `top`, `right`, `bottom` and `inset` on an absolute node, so one can be stretched between two edges; `anchor`, `placement` and `offset` on an ordinary node, which stays in the tree and follows its anchor with no lag, and the corner and centre placements (`top_start`, `top_end`, `bottom_start`, `bottom_end`, `center`) for a layer; bitmap colour emoji; and a larger minimum window size that no longer reports repeated resizes. Nothing in Tesserae broke: the suite passes (7853). Four tests that recorded what tre could not do (a size other than a number, `auto` or a percentage; an inset; a corner placement) failed because it can now, and say what it does. Tesserae's own `calc()`, insets and `anchor` in the view language are the next issues ([#261](https://github.com/mindderivative/tesserae/issues/261) and [#262](https://github.com/mindderivative/tesserae/issues/262) were built as far as 0.5.6 allowed).

## 0.5.0.22

### Added

- **Styled spans inside one `Text`: `runs`** ([#265](https://github.com/mindderivative/tesserae/issues/265)). `Text` had lost `runs` when views moved to the `widget:` language (a `Text` was one piece, and mixed styles meant a row of nodes). It has it again: a list of pieces of one text, each a string or a mapping with `text` and any of `color`, `weight`, `italic`, `underline`, `strikethrough`, `font_size`, `font_family` and `link`, drawn as one text that wraps as one (tre's `spans`, from byte ranges Tesserae works out). A string in a run may be an expression, so the pieces follow your data; a `link` run is the theme's `primary` and underlined, and `handlers: {on_link: "open_terms(event.href)"}` runs with its `link` in `event.href`. `runs` and `text` together are refused where they are written, and a bad run (an empty list, no `text`, an unknown key, a weight that is not a number) names the node. `tesserae migrate-yaml` carries a `text: {runs: ...}` over (it failed on it before). The row-of-nodes layout stays for pieces that need their own handlers or alignment.

## 0.5.0.21

### Changed

- **A view's stylesheet is read when the application uses the view** ([#274](https://github.com/mindderivative/tesserae/issues/274)). A project's `<Name>_Stylesheet.yaml` next to `<Name>_View.yaml` (or in `Styles/`) was never loaded, and all 40 shipped stylesheets were read and compiled for every app, used or not. Each opened view now works out the widgets it uses (its own and, through every view it calls, theirs) and reads only those widgets' stylesheets: the shipped ones, then the project's, then the app's own over both. A small app that uses a button, a checkbox and some text reads 6 of the 40. A project view that replaces a shipped one has its own sheet and not the shipped look; a sheet for a view nothing calls is not even parsed (so a mistake in it is not reported); one that is used and wrong is an error naming the file, line and column. The app's own stylesheet is not read again as a view's when a view has its name. A hot reload re-works out what is used, so a view the file starts to call gets its sheet, and editing a used project stylesheet reloads the view.

## 0.5.0.20

### Fixed

- **`ViewDialog` given a view in the current language says what to do instead** ([#268](https://github.com/mindderivative/tesserae/issues/268)). It reads its view with the older loader, so a `widget:` view failed inside it with `every widget needs an id`, which says nothing useful. It is refused up front, by path or by name, naming the file and pointing to a modal `widget: Overlay` bound to `open` and closed by `surface.dismiss` (which works in a view since 0.5.0.17). `ViewDialog` itself is unchanged for views in the older syntax. Porting it was not done: a dialog in the current language is that Overlay, and a called view has no ViewModel of its own, which is what `ViewDialog`'s `arguments` and `.viewmodel` are for.

## 0.5.0.19

### Changed

- **The vertical-slice examples are in the current view language** ([#276](https://github.com/mindderivative/tesserae/issues/276)). `examples/counter`, `multi_screen`, `todo_list` and `custom_title_bar` were written with `kind:`, `component:`, `app.load` and, for the to-do list, a `Repeater` and a ViewModel for each row. They are now `widget:` views and ViewModels that serve a named view, opened with `bind` and `open_view`; the buttons are `Button` and `IconButton` instead of drawn `Rect`s, and the to-do list is one list `Signal` that the view turns into rows by `for:` and `key:`. `tests/test_examples_run.py` runs each example's own checks in its own process (and the multi-screen deep link), and checks that none uses the older syntax and that `tesserae migrate-yaml` has nothing to translate in it.

## 0.5.0.18

### Fixed

- **Editor support for the current language** ([#275](https://github.com/mindderivative/tesserae/issues/275)). `tesserae schema --settings` mapped every `*_View.yaml` to the schema of the older syntax, which flagged every view of the current one, and the widget schema knew only the 30 built-in widgets, so a `Button` or a view of your own was an error too, and a node's `style:` was just "an object". The widget schema now has a branch for each view Tesserae ships (with its params, types, choices and bounds) and describes `style:` field by field (expressions accepted); there is a new `tesserae-stylesheet-schema.json` for a stylesheet of rules (the theme schema knew only the older keys). `--settings` maps views, stylesheets and themes to those. `tesserae schema --project [DIR]` writes `DIR/.tesserae/tesserae-widget-schema.json`, the widget schema with every view the project has of its own, and maps the views to it, so an editor completes a call of your view and flags a misspelt or missing param. The schemas are written by `tools/generate_yaml_schema.py` (`generate_widget_schema.py` runs it) and the site copies are in `docs/schema/`.

  The schemas were run through Red Hat's real language server (`tools/check_schema_in_language_server.py`): every view and stylesheet of rules in the repository comes back clean, and completions and flagged mistakes behave.
  `schema --project` refuses a symbolic link at `.tesserae/` or at the schema file instead of writing through it, and replaces the file whole.

## 0.5.0.17

### Fixed

- **`surface.dismiss` closes a `widget: Overlay` in a view** ([#266](https://github.com/mindderivative/tesserae/issues/266)). A button in an Overlay with `handlers: {on_click: surface.dismiss}` did nothing: the handler only looked for overlays made by `tesserae.overlays`, and a view's Overlay closes another way. It now closes the nearest Overlay the widget is in, as a press outside it would: the layer hides, a bound `open` goes false, and `on_dismiss` runs. It works from a view the Overlay calls, and in nested Overlays it closes the inner one. With no Overlay around, it falls back to the `tesserae.overlays` surface the view is in, as before. A `TitleBar` with `buttons: [dismiss]` in an Overlay now closes it.

## 0.5.0.16

### Fixed

- **`style: row_Style.yaml` in a view of the 0.5.0 language is refused, not silently ignored** ([#273](https://github.com/mindderivative/tesserae/issues/273)). The loader stored the file name and nothing read it, so the node laid out at 0 by 0 with no message. It is an error at the line and column, saying a style file is not part of the language and what to write instead (the fields inline, or `classes:` and a rule in a stylesheet). `tesserae migrate-yaml` now writes a style file's fields into each node that names it (the file beside the view, else the only one of that name in the project; the fields may be the file's own or under a `style:` key), says so in its report, and fails with the file named when it cannot read one. The older loader still expands a style file for a view in the older syntax.

## 0.5.0.15

### Changed

- **`tesserae new` and `tesserae add screen` write the current view language** ([#270](https://github.com/mindderivative/tesserae/issues/270)). The templates were still `kind:` / `component: ButtonFilled` views and `app.load(...)`. A new app is now `Main_View.yaml` (a tree of `widget:` nodes), a `Main_ViewModel.py` that says which view it serves (`views = "Main"`), and an `app.py` that binds the ViewModel and opens the view. `--window` makes a `widget: Window` view whose Main and Settings screens are called with a `route:`; they have no ViewModel of their own, so one `Window_ViewModel.py` serves the window and them (the tutorial's shape). `add screen` writes the view and ViewModel and adds `bind`, `open_view` and the route above the marker; in a window project it writes only the view and prints the node and rail item to add. New projects check clean (`app.check()`) and `tesserae migrate-yaml` has nothing to move in them.
- **`examples/window_dock` is in the current language**, moved with `tesserae migrate-yaml` and by hand: one `Window_ViewModel.py` serves the window and the Console panel and Notes screen it calls; the example addresses nodes and panels by their path from the root (`root.body.dock.outline`).

### Fixed

- **`app.run(hot_reload=True)` failed in an app whose window has routed screens.** A routed call is registered as a screen of its window's view, and hot reload asked it for the older view's components (`'_Screen' object has no attribute '_prune_components'`). It is skipped, as it is part of the window's view, and the log no longer says such a screen "isn't watched".

## 0.5.0.14

### Fixed

- **The app's stylesheet of `widget:` rules is applied again when it changes while the app runs** ([#272](https://github.com/mindderivative/tesserae/issues/272)). `set_stylesheet_spec` (which `run(hot_reload=True)` calls when the stylesheet file is saved) handed the sheet to each view's older stylesheet check, which refused a `widget:` rule with `unknown field(s) ['widget', 'variant']` and kept the old rules, so editing the stylesheet never reached a running window. Every view opened with `open_view` is now composed again under the new rules (`ComposedView.restyle`), with its ViewModel and `state:` kept; a sheet the engine rejects leaves every view as it was. An older-shape sheet works as before, and a view opened later uses the new rules.

## 0.5.0.13

### Added

- **Hot reload for views written with `widget:` nodes** ([#269](https://github.com/mindderivative/tesserae/issues/269)). `app.run(hot_reload=True)` watches a view opened with `open_view` or `open_window`, every view it calls (and the views those call) and the pictures it draws, and composes the view again when one changes: the ViewModel and its Signals are the same ones, a node that keeps its place keeps its `state:`, and handlers are wired again. A mistake (invalid YAML, a call with a wrong parameter, a name nothing defines, a widget the engine rejects) leaves the window as it was and is logged as one `ERROR` naming the file. A view opened while the app runs is watched too, and a view the file starts to call is watched from then on. The views Tesserae ships are not. Not reloaded: Python code, and a `widget: Window` view's window options (the app's stylesheet of rules is reloaded from 0.5.0.14). Until now the log said such a screen "isn't watched" and a saved edit did nothing.

## 0.5.0.12

### Fixed

- **`track: surface_variant` on a progress indicator was a bare `KeyError`, and a mistyped role was no better** ([#267](https://github.com/mindderivative/tesserae/issues/267)). Two faults. An indicator (or any control) with no theme looked a role up in `tokens.BASELINE`, which holds only some of MD3's roles, so a real role such as `surface_variant` raised `KeyError` while painting; it now falls back to the whole baseline scheme. And a name that is no role at all raised the same `KeyError` at the first frame; `track` is now checked when the indicator is made, and the error names the property, the role, the widget, and the nearest role when one is a slip away (`'surface_container_hihgest' is not a colour role -- did you mean 'surface_container_highest'?`). The same lookup in every control gives that message instead of a `KeyError`.

## 0.5.0.11

### Fixed

- **A borderless window no longer crashes when the app's stylesheet is a sheet of `widget:` rules** ([#271](https://github.com/mindderivative/tesserae/issues/271)). The window's 1 px border is a plain `Rect` in a small view of its own, and the app's stylesheet was handed to it even when it was in the rule shape that view cannot read, so `App(borderless=True, stylesheet=...)` raised `unknown field(s) ['widget']` (and `tesserae build --check` with it). A rule sheet is no longer passed to the border, which no `widget:` rule could reach anyway; a sheet in the older shape still restyles it by class. The Tasks tutorial's last step no longer needs `window_border=False`.

## 0.5.0.10

### Changed

- **Every docs page brought up to date and checked against the code** ([#263](https://github.com/mindderivative/tesserae/issues/263)). The component and stylesheet pages (about ninety) described the fragment system that 0.5.0 replaced, and nothing tested that they still matched. `tools/generate_component_docs.py` now reads the shipped views, their parameters, slots, named parts and stylesheet rules, and the built-in widgets, so the "How it is built" tables and the stylesheet pages cannot drift; it refuses to run when a shipped view or built-in widget sits under no component. The hand-written prose of each component was checked against the code and tests, and the claims that had become false were corrected (for example that an engine cannot ease a width, that a window is one per app, that a panel alone has a tab strip, and which looks are "Not built"). The guides, the tutorials, Getting Started, the install, architecture, theme, editor, CLI, release and reactivity pages were rewritten to the `widget:` language, with the examples run. The Getting Started and Tasks tutorial programs under `examples/` are now in the 0.5.0 language, with `tests/test_tutorials_current.py` running every step.
- `docs/migration.md` lists what each merged fragment became (Button variants, Fab, Badge, Card, Chip, Tabs, Tooltip and the rest) and no longer says the shipped components cannot be migrated.
- A view parameter's `min` and `max` are documented.
- The README is rewritten for the current language (it still described 0.3.0, `component:` fragments and `Repeater`), and `ARCHITECTURE.md` points to the architecture page instead of keeping a second, older copy.

### Added

- `tests/test_docs_examples.py` loads every view and stylesheet example on every docs page against the shipped views. An example that shows the old form on purpose is marked `<!-- old-syntax -->`, and the test fails if a marked one has become valid.
- `tests/test_component_docs.py` fails when a generated page is out of date, when a shipped view is on no page, or on two.

### Fixed

- `tesserae migrate-yaml` ([#264](https://github.com/mindderivative/tesserae/issues/264)) checks a view that calls a view Tesserae ships (`NavigationRailScreens`, `StatusBar`, ...) against the shipped one, and no longer fails with "no widget named" for it.
- Comments in the shipped views that said what the code does not (a modal drawer that slides, a top bar with the role banner, a side sheet with an edge line, a text-field label that jumps, a project stylesheet that is picked up beside its view) were corrected, as was the `anchor` description of `Overlay`.

## 0.5.0.9

### Added

- **Typing effects on a text field** ([#248](https://github.com/mindderivative/tesserae/issues/248)). `typing_effect: flash` tints the characters just typed with the primary colour and lets the tint fade; `typing_effect: fade_in` covers them in the
  background colour and lets that fade, so they seem to appear. `caret_effect: glide` hides the engine's caret and draws one of Tesserae's own that eases to each new place, stays solid while typing and blinks after a moment. Each is drawn from the geometry
  tre 0.5.6 reports for an edit (`caret_move`, `text_rects`; tre#165), so it sits exactly on what was inserted, line by line for a paste. They are properties of `TextField` and of the bare `TextInput`, `none` by default; with reduced motion asked for there is no flash and no
  fade, and the caret jumps and does not blink. The issue's first plan, a pulse or glow on the whole input, is dropped: the geometry makes it unnecessary. Each look is the field's own to set: `typing_duration` (milliseconds; `0` leaves the effect out),
  `flash_color` (a theme role or colour), `flash_opacity` (0 to 1), `glide_duration` and `caret_blink` (milliseconds; `0` makes the caret jump, or stay solid). Not built: a shader on the typed characters (tre did not add per-character shader inputs), and the easing, which is fixed.
  `examples/typing_effects` has them on one page (`--interactive` to type in them).
- **A number can have a range** (#248). A widget property or a view parameter may say `min` and `max`; a value outside is an error that names the property and the range, with the file and line, and the schema tells an editor.

## 0.5.0.8

### Added

- **`overflow: hidden | visible`** ([#260](https://github.com/mindderivative/tesserae/issues/260), part of [#257](https://github.com/mindderivative/tesserae/issues/257)). A style field that is another way to write `clip_children` (`hidden` is `true`, `visible` is `false`),
  added because it is what people reach for. It does not scroll: a `ScrollView` does. A node that gives both with different meanings is an error naming both (a stylesheet rule's `overflow` and a node's own `clip_children` are
  merged first, so they count as the same node); anything but `hidden` or `visible` is an error naming the node. It is not the `overflow` property of a `Text` (`clip` or `ellipsis`), which is unchanged.

### Documented

- **A size that is the parent minus something** ([#261](https://github.com/mindderivative/tesserae/issues/261), part of [#257](https://github.com/mindderivative/tesserae/issues/257)). There is no `calc()`: the engine takes only a number, `auto` or a percentage for a size, and has no
  node-level event for a change of size, so Tesserae cannot follow a parent's size itself without trailing it by a frame and shrinking inside an `auto`-sized parent. In the flow `flex: fill` with margins or a `gap` is exact, and the layout guide
  shows it (tested). An absolute node stretched between two edges cannot be said; it is asked of tre in `design/tre-requests/absolute-insets.md` (sent as tre#178).
- **Placing a node against another node** ([#262](https://github.com/mindderivative/tesserae/issues/262), part of [#257](https://github.com/mindderivative/tesserae/issues/257)). There is no `anchor:` style: an `Overlay` already sits against a named node on one of four sides and follows it with no lag, and the layout
  guide says so, with what a layer is (above the window, not clipped by a parent, its own Tab scope, flipped to fit) and is not (a corner, or in the tree). That is asked of tre in `design/tre-requests/anchored-layout.md` (sent as tre#179).

## 0.5.0.7

### Added

- **`visible:` on any node** ([#259](https://github.com/mindderivative/tesserae/issues/259), part of [#257](https://github.com/mindderivative/tesserae/issues/257)). `visible: false` hides a node and takes it out of layout; `true` shows it; an expression
  is allowed, so a Signal can show and hide it. Unlike `if:` the node stays in the tree with its `state:`, timers and listeners. On a view call it hides the whole view; on the root of a view file it is an error. A widget
  or view that declares a property called `visible` keeps it. Only a node that says `visible:` is touched, because overlays, a view's handle and bindings hide nodes too; a node that stops saying it is shown again.

### Fixed

- **`pointer_events` (0.5.0.6) did nothing on a control or a Link**, which place only some keys: a `Slider`, `Checkbox`, `RadioButton`, `Switch`, `SpinBox`, `RangeSlider` or `Link` with `pointer_events: none` was still hit. It reaches them now,
  and `visible` the same way.

## 0.5.0.6

### Added

- **`pointer_events: none`** ([#258](https://github.com/mindderivative/tesserae/issues/258), part of [#257](https://github.com/mindderivative/tesserae/issues/257)). A style field that lets the pointer through the node itself: a click goes to whatever
  is under it, and it is not hovered or pressed. `auto` is the usual. It is about the node alone (as in CSS): what is inside a `pointer_events: none` node still takes the pointer, and its focus and its place in the
  accessibility tree are unchanged. Value may be an expression; anything but `auto` or `none` is an error naming the node. It sets the engine's `hit_testable`, and only when a style gives it: a node that does not say it
  keeps what it was built with, and a node whose style drops it is hit-testable again. Before, a decorative layer laid over a button in YAML swallowed the click.

## 0.5.0.5

### Added

- **Halves of a split are mini zones, and a panel can be dropped on one (phases 2 and 3 of 4)** ([#106](https://github.com/mindderivative/tesserae/issues/106), part of [#114](https://github.com/mindderivative/tesserae/issues/114)).
  Every `DockPanel` half of a split now has a tab strip over it, with a tab for its own content (titled by the `DockPanel`; a half with no `title:` shows its `id`), so a split looks different
  from 0.5.0.4: each half is 49 px shorter. While a tab is dragged over a half, the outer quarter of each side is an **edge** and the rest is the **middle**, and the highlight shows which. Dropping on the
  middle (or the strip) adds the panel to the half as a tab; dropping on an edge splits the half there, the panel taking the new half beside it with a resize handle of its own. A tab in a half is
  dragged to a zone, another half or an edge (Tesserae holds the pointer itself, since tre does not know that panel), switches by click or arrow keys, closes with its close button, and is in the
  "Move to ..." menu, which lists the halves. A half a drop made that loses its last panel collapses into its neighbour. Tesserae finds the half from the window's pointer events, which keep arriving
  during a tre drag (checked in a real window on KDE Wayland), so tre needs no change. In Python: `DockHost.halves()`, `show_in_half()`, `half_of()`, `move()`; `Dock.add_half()`,
  `on_half_drop()`, `on_half_empty()`. A hot reload leaves the strips, the dropped panels and the splits the user made where they are, and a half the file removes sends its panels back to their zones.
  `layout()` records the halves (`halves`: the titles of the panels in each and the tab it shows) and the splits the user made (`made`: a tree per half of the YAML), and `restore()` takes the current splits apart and
  makes the saved ones, so the arrangement survives a restart; `DockHost.move(panel_id, half)` puts a panel in a half from code. `examples/window_dock` has a `Compare` panel of two halves that its self-checks drop a panel on, save and restore, and a `--interactive` flag that keeps its window open to try by hand.
  **Fixed on the way:** a handle between two parts of a split stopped resizing the right node once its first part had been split again (it kept the half's old column, now inside a container); it asks each time now, and
  the YAML's own split handle does the same.
  A half's own content cannot be dragged to another place, and tabs are not reordered (a restored layout puts a panel in the right zone or half, not at the right place in its tab strip).

## 0.5.0.4

### Added

- **Progress: thicker sizes, the circular gap, the two-bar sweep, the contained loading indicator and wavy shapes** ([#249](https://github.com/mindderivative/tesserae/issues/249)).
  `thickness` sets a bar's height or a ring's width (4 is the standard; a thicker ring keeps the standard ring's outer edge). With a `track`, a determinate ring and its
  track are a 4 px gap apart. `two_bar: true` sweeps a wait as a long bar and a shorter one behind it. `contained: true` puts the loading indicator's shape in a
  `primary_container` circle. `wavy: true` draws a bar as a sine wave flowing along a straight track (the control is taller by the wave) and a ring's arc as a wave whose
  crests flow round it. All are opt-in: the default look is unchanged. The widths of the two bars are fixed (the engine cannot animate a width), and the wave's size, its speed
  and the thicker sizes are written from memory of the spec and have not been checked against it. Not done: making MD3's current look (a track and a stop dot) the default.

## 0.5.0.3

### Added

- **RangeSlider: two handles** ([#250](https://github.com/mindderivative/tesserae/issues/250), part 2 of 2). `widget: RangeSlider` picks a least and a most value
  with `low` and `high` (two-way, `low <= high`: the handles never cross). Each handle is its own Tab stop with its own state layer and focus ring, and a slider of
  its own for a screen reader ("Price, minimum", "Price, maximum", reaching up to or down from the other handle); the arrow, Page and Home/End keys move the handle
  that has the focus. A press on the track moves the nearer handle, a drag keeps the handle it began on. It takes the slider's `min`, `max`, `step`, `ticks`,
  `value_indicator`, `vertical`, `size` and `icon`; with a `size` the track is three pieces, a gap from each handle. `controls.RangeSlider` is the Python class;
  `on_input` and `on_change` hear `(low, high)`.
- **Slider: Expressive sizes, vertical and an inset icon** ([#250](https://github.com/mindderivative/tesserae/issues/250), part 1 of 2).
  `size: xs | s | m | l | xl` draws MD3 Expressive's slider: a track 16, 24, 40, 56 or 96 px thick in two pieces with a 6 px gap on each side of a thin
  4 px handle (44 to 108 px across it); the touch target grows to hold the handle. `vertical: true` stands it up: the bottom is `min`, `style.height` is
  its length, the up and down arrows step it, and the ticks and the value bubble go beside the track. `icon: name` insets a glyph at the start of the
  track (from size `s` up), in the on-colour while the active piece covers it and in the track's colour when it does not. The standard slider is unchanged.
  The sizes are written from memory of the spec and have not been checked against it.

## 0.5.0.2

### Changed

- **A function name that does not exist is found when the view loads** ([#251](https://github.com/mindderivative/tesserae/issues/251)).
  `{{ nosuch(1) }}` in a template, an `if:`, a `for:` or a stylesheet rule, and `x = nosuch(1)` or `nosuch(1)` in a handler, used to load
  without a word and fail when the expression ran (a traceback on stderr when a handler was pressed, an expression that raised at render).
  Now the view does not load: the error names the file and line and offers the near names (`did you mean 'clamp'`). In an expression the
  only functions are the built-in ones, so it is found as the text is compiled. In a handler a call may also be a built-in action
  (`copy`, `focus`, `after`, `navigate_to`, ...), a method of the ViewModel or a handler parameter, so it is found as the view is composed.
  A handler whose names cannot be judged (a scope with no app to list the built-in actions) loads as before.
  A ViewModel method added to the object after its view loaded is now a load error: define it on the class.

## 0.5.0.1

Point releases between 0.5.0 and 0.5.1: one issue each, in the order the backlog was recommended (#252, #251, #250, #249, #248).

### Fixed

- **A flex-expanded Slider maps the pointer with the width it was laid out at** ([#252](https://github.com/mindderivative/tesserae/issues/252)).
  The slider fixed its span at the width it was built with (200 by default), so in a row with `flex: expand_horizontal` (or a percentage)
  its track and handle were drawn at that width and a press in the middle gave the wrong value (a 280 px slider read 62 as 90). It now takes
  the width the engine laid it out at when it paints, when a pointer is mapped, on a drawn frame and on a window resize, and moves the
  track, the tick marks and the handle with it. A slider with an explicit width is untouched.

## 0.5.0

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
- **Material Design Icons** (#216). 147 icons from Pictogrammers' MDI (Apache-2.0) are in the icon set beside the built-in ones (names in `snake_case`: `account_check`,
  `format_bold`; a built-in name keeps its own drawing), each drawn in its own 24 x 24 box. `tools/import_mdi.py mdi.json [--names ...|--all]` adds more from the Iconify `mdi` JSON.
- **Timers** ([#217](https://github.com/mindderivative/tesserae/issues/217)). Handlers can call `after(ms, action[, name])`, `every(ms, action[, name])` and `cancel(name)`; `action` is an
  action name or statements run in the handler's scope, and a name restarts a timer of that name (a debounce). `tesserae.timers.Timers(window)` is the same for Python.
  They run on the frame loop until tre has timers (#235) and stop with the view.
- **Scroll state** ([#218](https://github.com/mindderivative/tesserae/issues/218)). `ScrollView.scroll_offset` is drawn (a literal or a Signal; a bound Signal follows the user's scrolling, and
  setting it scrolls), and `at_top`, `at_end` and `scroll_direction` write the position to the Signals or state names they are bound to, for collapse-on-scroll and hide-on-scroll.
- **Pointer capture, cursor and drag events** ([#219](https://github.com/mindderivative/tesserae/issues/219)). New events `on_move` and `on_release`, and handler actions `capture()`,
  `release()` and `cursor(name)` that act on the widget whose handler is running, so a drag keeps following the pointer outside the node.
- **Per-corner `corner_radius`** ([#220](https://github.com/mindderivative/tesserae/issues/220)). `style.corner_radius` takes a list of four (`top_left`, `top_right`, `bottom_right`,
  `bottom_left`) or a mapping of corners and edges (`{top: 12}`, `{left: full, top_right: 4}`), with tokens or pixels; one value is unchanged.
- **Windows, title bars and docks in composed views** ([#221](https://github.com/mindderivative/tesserae/issues/221)). A `widget: Window` root opened with `app.open_view` sets the OS
  window (it becomes the app's window view, as `kind: Window` is for `app.load`), and the bindings a `TitleBar` expands to (inactive dimming, the maximize/restore glyph, the OS's inset and
  buttons) are wired without a ViewModel. Docks already worked and are now covered by tests.
- **Input masks** ([#222](https://github.com/mindderivative/tesserae/issues/222)). `mask: "(###) ###-####"` on a `TextInput` or `TextField` formats what is typed or pasted (`#` digit, `A` letter,
  `*` either, `\\` a literal); `tesserae.spec.mask.Mask` is the same for Python.
- **Clipboard actions** ([#223](https://github.com/mindderivative/tesserae/issues/223)). Handlers can call `copy(text)` (true if it reached the OS clipboard) and `paste()` (the text on it, or `''`).
- **`open_url`** ([#224](https://github.com/mindderivative/tesserae/issues/224)). Handlers can call `open_url(url)` to open a link in the OS's browser or mail program; only `http`, `https`,
  `mailto` and `tel` links are opened. `tesserae.urls.open_url` is the same for Python.
- **Divider** ([#152](https://github.com/mindderivative/tesserae/issues/152)). `widget: Divider` with `variant: full | inset | middle`, `orientation: horizontal | vertical` and `thickness`,
  a shipped view with a shipped look (a line in `outline_variant`, hidden from a screen reader). The 0.4.x `component: Divider` fragment still works.
- **Image** ([#196](https://github.com/mindderivative/tesserae/issues/196)). `widget: Image` takes `alt` (a screen reader's description; without it the picture is decorative and hidden from one,
  unless it handles clicks) and checks `fit`; its shape is `style.corner_radius`, per corner too, which the engine clips the picture to. A `src` that follows a Signal now changes the picture
  shown (a changed picture was missed by the reconcile).
- **Svg** ([#197](https://github.com/mindderivative/tesserae/issues/197)). `widget: Svg` takes `alt` as `Image` does, and needs one of `src` and `content` (a load error otherwise); `currentColor` is the
  `foreground`, so a monochrome icon follows the theme.
- **Elevation that moves** ([#226](https://github.com/mindderivative/tesserae/issues/226)). No new language: `elevation` in `hovered` and `pressed` rules with `transition: {elevation: ms}` eases the
  shadows (also from a level a view computes, for a drag). Documented in Gradients & Effects and tested.
- **Overlay** ([#227](https://github.com/mindderivative/tesserae/issues/227)). `widget: Overlay` with `open` (two-way), `anchor`, `placement`, `modal` and `dismissible` shows its children in a
  layer over the window: anchored with flipping, or a modal scrim; Escape or a press outside closes it and writes `open` back; focus returns.
- **VirtualList** ([#228](https://github.com/mindderivative/tesserae/issues/228)). `widget: VirtualList` with `item_height` and `overscan` and a single `for:` child builds only the rows in view and
  builds more as it scrolls (a list of 10 000 opens with about a dozen rows). It has a ScrollView's `scroll_offset`, `at_top`, `at_end` and `scroll_direction`.
- **Window size classes** ([#230](https://github.com/mindderivative/tesserae/issues/230)). `app.window_width`, `app.window_height`, `app.width_class` (`compact` to `extra_large`) and `app.height_class` follow the
  window's size and can be read in any expression. `app` itself is now readable in views whose ViewModel is the new kind (it had only worked for a 0.4.x ViewModel).
- **Screen transitions** ([#231](https://github.com/mindderivative/tesserae/issues/231)). `app.transition` (or `App(transition=...)`) is `none`, `fade_through`, `shared_axis_x`, `shared_axis_y`,
  `shared_axis_z` or `container_transform`, played by `navigate`, `back` and `forward` (reversed going back); `app.navigate_with(name, transition=..., origin=node)` picks one for a single navigation.
- **Text** ([#195](https://github.com/mindderivative/tesserae/issues/195)). `widget: Text` takes `heading: 1` to `6` (a heading of that level for a screen reader). Type roles have a `tracking`
  field: `tokens.MD3_TRACKING` is Material 3's per role, off unless a theme's `typography:` sets it (`tokens.MD3_TRACKING_TYPOGRAPHY` for all). Every role's size and line height is tested against the MD3 scale.
- **Splitter** ([#203](https://github.com/mindderivative/tesserae/issues/203)). `widget: Splitter` with two child panes, `orientation`, a two-way `position`, `min_first`, `min_second` and `collapsible`: a handle you drag
  (the pointer is captured), move with the arrow keys, Home and End, a screen reader can set, and double click to collapse.
- **Image masks** ([#236](https://github.com/mindderivative/tesserae/issues/236)). A picture's rounded, circular and pill shapes are `style.corner_radius` (also from a rule); no new code was needed, and they are tested.
- **The accessibility vocabulary** ([#237](https://github.com/mindderivative/tesserae/issues/237)). `a11y:` takes `pressed`, `invalid`, `description`, `describedby`, `controls`, `current`, `value_now`, `value_text`
  and `busy`, checked and bindable; the engine has no property for them yet (requested: tre#160), so they are sent one at a time as far as it takes them, with one warning naming each it lacks.
- **`tooltip:` on every node** ([#238](https://github.com/mindderivative/tesserae/issues/238)). Text, or `{text, title, delay}` for a rich one: shown after a hover delay (500 ms) or at once on keyboard
  focus, gone on leave, press, blur or Escape; the text is the node's accessibility `description` where it has none.
- **`transition:` for layout** ([#239](https://github.com/mindderivative/tesserae/issues/239)). `width`, `height`, `x`, `y`, `gap`, `padding` and `margin` ease like the rest. tre cannot animate them yet
  (requested: tre#161), so they are set frame by frame along the curve; when tre can, its own animation is used without a change.
- **Badge** ([#141](https://github.com/mindderivative/tesserae/issues/141), [#142](https://github.com/mindderivative/tesserae/issues/142)). `widget: Badge`: a dot, or a pill with a `value` capped at `limit` (`999+`), `show`, and `anchored: true` to
  sit over the top right corner of its host (the children). One view replaces `BadgeDot` and `BadgeLabeled`, which still work.
- **Link** ([#174](https://github.com/mindderivative/tesserae/issues/174)). `widget: Link` is primary text in `body_medium` by default with `href` (opened by `open_url`, so only web and mail links), a two-way
  `visited` (and `state: visited` in rules), `disabled`, and `underline` (`hover` by default: under the pointer or the keyboard focus, `always`, `never`).
- **Progress indicators** ([#143](https://github.com/mindderivative/tesserae/issues/143), [#144](https://github.com/mindderivative/tesserae/issues/144), [#145](https://github.com/mindderivative/tesserae/issues/145)). `LinearProgress` and `CircularProgress` with no `value` (or an expression
  that gives nothing) are a wait with no end (the builder had always made them a bar at 0); new `track`, linear `buffer` and `stop_indicator`, and `label`; a screen reader hears busy, or the value as a percentage.
- **Checkbox, RadioButton, Switch** ([#175](https://github.com/mindderivative/tesserae/issues/175), [#176](https://github.com/mindderivative/tesserae/issues/176), [#177](https://github.com/mindderivative/tesserae/issues/177)). `label` (beside the control, part of what you
  press), `error` (checkbox and radio), a Checkbox that is neither on nor off (`checked: null`), Switch `icons`, and the colour is `style.foreground`. A patch no longer reset a control's own
  accessibility states (`checked`, `value`) to nothing.
- **Slider** ([#178](https://github.com/mindderivative/tesserae/issues/178)). `min`, `max` and `step` (the builder ignored them), `ticks`, `value_indicator`, `label`, and `on_input` for every step of a drag;
  a bound `value` now follows the drag instead of waiting for its end. A bound value is written before the node's handlers run, so a handler reads what the user just did.
- **SegmentedButton** ([#193](https://github.com/mindderivative/tesserae/issues/193)). `widget: SegmentedButton` with `options`, a two-way `selected` and `multiple`, written in the view language (the first shipped
  component that is built from the language's own parts: per-corner pill, `focus_group`, icons, handlers that set a Signal). An `a11y: role` may be worked out from a param (never from a Signal), and a roving focus group starts on its checked item.
- **Tabs** ([#166](https://github.com/mindderivative/tesserae/issues/166), [#167](https://github.com/mindderivative/tesserae/issues/167)). `widget: Tabs` with `tabs`, a two-way `selected`, `variant` (primary, secondary) and `tab_width`: a shipped view with icons, badges,
  an indicator that slides, and arrows/Home/End that move and choose. A bar that scrolls waits for the engine to scroll sideways.
- **Several windows** ([#105](https://github.com/mindderivative/tesserae/issues/105)). `app.open_window(view, modal=, parent=)` opens a view in a window of its own (tre 0.5.6 opens windows while the app runs), with `app.windows`, `app.window_of`, `app.close_window`, and the handler `open_window(view[, modal])`. Window handlers act on their own window; a modal window dims and blocks its parent; closing the main window closes them all.
- **Animated gradient focus borders (step 81).** `App(focus_ring="gradient")` turns the keyboard focus ring into a sweep gradient through the theme's secondary, primary and tertiary, one turn in three seconds (`tesserae.focusring`). Still when motion is reduced. A `TextField`'s focused border is a style rule and stays solid.
- **Frosted navigation, search and menus (step 72).** `frosted: true` on `NavigationRail`, `NavigationDrawer`, `NavigationDrawerModal`, `Menu`, `SearchBar`, `SearchView` and `TopAppBar` makes the surface 72% of its colour with a 20 pixel `backdrop_blur`, so what is behind shows through softly. Off by default (Material 3 has solid surfaces).
- **Icon toggles that morph (step 55).** `transition: {icon: ms}` on an `Icon` eases a changed glyph into the next (tre morphs a path's `data`); `IconButton` uses it for `selected_icon`. Glyphs from different sets switch at once.
- **Ripple as a shader (step 48).** `App(ripple="shader")` draws the press ripple with one anti-aliased fill shader per node (three presses at once, Material Web's timing) instead of a circle node per press (`tesserae.ripple`). The default stays `nodes`.
- **Routed views: nested routes, guards and lazy screens.** A routed call inside a routed view is a nested screen under its parent's path; `route:` may be a mapping with `path`, `guard`, `redirect` and `lazy`; `app.guard(screen, check)` is the same from Python. A lazy screen's view is built when first reached.
- **Window: `remember`.** `remember: true` (or a name) keeps the window's size, place and maximized state in the user's config directory and puts them back next run (`tesserae.windowstate`; `TESSERAE_STATE_DIR` moves it). Position is saved only where the platform reports one.
- **Toolbar: `fit`.** Items that do not fit the width move into the overflow menu. It needed a way to know a size, so a `Container` gains `measured_width` and `measured_height`: outputs, written after layout and when the window resizes, bound like a scroll view's `at_top`.
- **SplitButton: the keyboard.** Arrow-down on either part opens the menu and moves the focus to its first row. `Overlay` gains `focus_first` (and `Menu` passes it on) for any layer that should take the focus when it opens.
- **Routed views** ([#208](https://github.com/mindderivative/tesserae/issues/208)). A view call with a `route:` is a screen in a window view written in the current language (it was only wired for the old syntax); `app.params` gives the screen the params it was reached with (a route like `notes/{id:int}`, back and forward restoring them), and the handlers `navigate_to(screen, params)` and `navigate_route(path)` go there.
- **Dialog: the full-screen form.** `fullscreen: true` on `Dialog` fills the window on `surface` with a close button, the headline and the actions along the top and the content scrolling under them; it follows `app.width_class` when written so.
- **Window** ([#204](https://github.com/mindderivative/tesserae/issues/204)). `kind: Window` and `widget: Window` take `fullscreen`, `maximized`, `transparent`, `blur_behind` and `click_through`, applied when the view loads and only when written (the size classes were #230).
- **Video** ([#198](https://github.com/mindderivative/tesserae/issues/198)). An `Image` now shows its `frame` in a view (it was refused as "not drawn yet"), and `widget: VideoPlayer` puts a play/pause button, the time, a seek slider, a mute button, a buffering ring and a caption band under it. The app decodes and supplies frames; the player owns none of the playing.
- **Toolbar** ([#172](https://github.com/mindderivative/tesserae/issues/172), [#173](https://github.com/mindderivative/tesserae/issues/173)). `widget: Toolbar`: docked (64 tall, full width) or floating (a pill with a shadow, a row or a column), standard or vibrant, with `IconButton` items, an overflow `Menu`, an end action button, your own content in a slot, and `hidden` to fade it out of the tab order. `IconButton` gains `tint`, a colour role for a standard button's icon.
- **SplitButton** ([#124](https://github.com/mindderivative/tesserae/issues/124) to [#128](https://github.com/mindderivative/tesserae/issues/128)). `widget: SplitButton`: a main action and a menu button joined, in all five Button types and sizes, with a `Menu` under the trailing part whose chevron turns over while it is open.
- **NodeGraph** ([#202](https://github.com/mindderivative/tesserae/issues/202)). `snap` (to a grid), `arrows`, `fit` (show every node), choosing a node, and a fit-to-view method.
- **DatePicker** ([#186](https://github.com/mindderivative/tesserae/issues/186), [#187](https://github.com/mindderivative/tesserae/issues/187), [#188](https://github.com/mindderivative/tesserae/issues/188), [#189](https://github.com/mindderivative/tesserae/issues/189)). `DatePicker` (the modal dialog: a month grid, a typed date, Cancel and OK) and `DatePickerDay` (one day, in all its states). The expression language gains `date_add_days`, `date_weekday`, `days_in_month`, `format_date` and `current_date`.
- **TopAppBar** ([#165](https://github.com/mindderivative/tesserae/issues/165)). `TopAppBar` in four sizes (small, centre, medium, large) with a navigation icon, up to three labelled actions, a collapse to the small form and the on-scroll colour.
- **TextField, what was left** ([#244](https://github.com/mindderivative/tesserae/issues/244)). The label glides, a filled field has 4 pixel top corners and a square bottom, the input is described by the help line, and `suggestions` offers autocomplete in a `Menu` under the field.
- **Dock** ([#206](https://github.com/mindderivative/tesserae/issues/206), [#207](https://github.com/mindderivative/tesserae/issues/207)). A `DockPanel` can be `closable` (a close button on its tab) and a `Dock` takes a two-way `closed` list of the names of the shut panels: closing adds a name, removing one opens the panel again.
- **Tree** ([#157](https://github.com/mindderivative/tesserae/issues/157), [#158](https://github.com/mindderivative/tesserae/issues/158)). `Tree` (branches that open to show their children, from nested data, with `expanded` and `selected` two-way and the tree keyboard), `TreeNode` (a branch or a leaf row) and `TreeLevel`.
- **Carousel** ([#199](https://github.com/mindderivative/tesserae/issues/199)). `Carousel` (uncontained, multi-browse, hero and centre hero rows of rounded items that scroll sideways and settle on one). A `ScrollView` takes `snap` and any node a `snap_align` style (tre 0.5.6's scroll snap).
- **Accordion** ([#156](https://github.com/mindderivative/tesserae/issues/156)). `Accordion` (a header button with a chevron that turns, and content while it is open) and `AccordionGroup` (single or multiple open, dividers, arrows between headers).
- **Search** ([#170](https://github.com/mindderivative/tesserae/issues/170), [#171](https://github.com/mindderivative/tesserae/issues/171)). `SearchBar` (a pill with a leading icon or menu button, a clear button, a trailing icon, an avatar, a two-way `query` and `active`) and `SearchView` (the docked panel of rows under it, with an empty state and the result count announced).
- **NavigationDrawer** ([#163](https://github.com/mindderivative/tesserae/issues/163), [#164](https://github.com/mindderivative/tesserae/issues/164)). `NavigationDrawer` (standard, collapses by easing its width), `NavigationDrawerModal`, `NavigationDrawerScreens` (the app's screens) and `NavigationDrawerItem`, with sections, dividers, badges, header and footer slots and a list that scrolls.
- **Menu** ([#168](https://github.com/mindderivative/tesserae/issues/168), [#169](https://github.com/mindderivative/tesserae/issues/169)). `Menu` (an anchored `Overlay` of rows with icons, shortcuts, checks, dividers, headings and submenus) and `MenuItem`. An `Overlay`'s `anchor` is looked up in the view that called it when it is not found in its own (a menu names its button in the calling view), and `anchor: parent` sits against the node the overlay is written inside.
- **TimePicker** ([#190](https://github.com/mindderivative/tesserae/issues/190), [#191](https://github.com/mindderivative/tesserae/issues/191), [#192](https://github.com/mindderivative/tesserae/issues/192), [#194](https://github.com/mindderivative/tesserae/issues/194)). `TimePicker` (the dialog), `TimeInput` (typed hour and minute), `PeriodSelector` (AM / PM, one view for both states), and the dial gains a two-way `mode`. A view's `state:` may be seeded from the view's params; a `TextField` takes an `on_edit` handler; reconcile now notices a changed SpinBox option or dial mode.
- **SpinBox** ([#185](https://github.com/mindderivative/tesserae/issues/185)). Holding a button repeats the step, Page Up and Page Down step ten at a time, `wrap` goes round the ends, `decimals`, `prefix` and `suffix` format the number, and `SpinBoxField` adds a visible label and supporting or error text.
- **Snackbar** ([#146](https://github.com/mindderivative/tesserae/issues/146)). `Snackbar` (a message near the bottom that goes by itself, with an action and a close) and `SnackbarHost` (several, one after another). An `Overlay` takes a `timeout` (it closes itself, held off while the pointer is over it) and an `on_dismiss` handler.
- **SideSheet** ([#154](https://github.com/mindderivative/tesserae/issues/154), [#155](https://github.com/mindderivative/tesserae/issues/155)). `SideSheet` (standard, inline, its width eases), `SideSheetModal` (over a scrim, from either side) and the shared `SideSheetPanel`: a title, a back and a close button, scrolling content and actions.
- **Chip** ([#179](https://github.com/mindderivative/tesserae/issues/179) to [#183](https://github.com/mindderivative/tesserae/issues/183)). `widget: Chip` (assist, filter, input, suggestion; icon, avatar, elevated, a close button) and `widget: ChipGroup` (`none`, `single`, `multiple` and `input` modes, wrapping, arrows). A view can take a `handler` parameter: the caller's action or statements, which the view runs by calling the parameter by name (`on_remove()`).
- **Pagination** ([#200](https://github.com/mindderivative/tesserae/issues/200)). `widget: Pagination` with a two-way `page`, `pages`, `compact` and `dots`: the numbers with an ellipsis, the current page filled, previous and next disabled at the ends.
- **Title bar** ([#205](https://github.com/mindderivative/tesserae/issues/205)). The window buttons show a tooltip (Minimize, Maximize, Close); a `widget: Tabs`, `TextField` or `IconButton` in the bar's children works. A node's spec may carry a `tooltip`, which the composed view shows.
- **Card** ([#148](https://github.com/mindderivative/tesserae/issues/148), [#149](https://github.com/mindderivative/tesserae/issues/149), [#150](https://github.com/mindderivative/tesserae/issues/150)). `widget: Card` with `variant` (elevated, filled, outlined), `headline`, `subhead`, `text`, `media`, an `actions` slot, `actionable` and `selected`. `interaction:` may now be an expression worked out from the view's params when the view is composed (never from a Signal).
- **NavigationRail** ([#159](https://github.com/mindderivative/tesserae/issues/159), [#160](https://github.com/mindderivative/tesserae/issues/160), [#161](https://github.com/mindderivative/tesserae/issues/161), [#162](https://github.com/mindderivative/tesserae/issues/162)). `NavigationRail` with `items`, `selected`, `expanded`, `alignment` and `header`/`footer` slots; `NavigationRailItem` with a badge; `NavigationRailScreens` and `NavigationRailScreen` for the app's screens (`app.current_screen`, `navigate_to`). A focus group starts on the item that is current.
- **ListItem** ([#153](https://github.com/mindderivative/tesserae/issues/153)). `widget: ListItem` with a headline, supporting text and overline (56, 72 or 88 pixels), a leading icon, avatar or picture, trailing text or icon, `leading` and `trailing` slots, `selectable`/`selected`, `disabled` and a `divider`.
- **StatusBar** ([#201](https://github.com/mindderivative/tesserae/issues/201)). `widget: StatusBar` with `items` at the start, centre and end (text, icon, tooltip, pressable ones that set `clicked`), a `progress` or `busy` edge, announced politely.
- **Fab** ([#133](https://github.com/mindderivative/tesserae/issues/133) to [#140](https://github.com/mindderivative/tesserae/issues/140)). `widget: Fab` with `icon`, `label` (the extended form), `variant` (primary, secondary, tertiary, surface), `size` (small, medium, large), `collapsed` and `disabled`; it rests at elevation 3, lifts to 4 on hover and settles on press.
- **Model parameters of a view** may be written by the view even when the call gave an expression: the view holds its own copy, which follows the expression whenever it changes. `Button` gains `flip` (off, a toggle leaves flipping to the caller).
- **IconButton** ([#129](https://github.com/mindderivative/tesserae/issues/129), [#130](https://github.com/mindderivative/tesserae/issues/130), [#131](https://github.com/mindderivative/tesserae/issues/131), [#132](https://github.com/mindderivative/tesserae/issues/132)). `widget: IconButton` with `variant` (standard, filled, tonal, outlined), five sizes, three widths, `shape`, `toggle`/`selected` with a `selected_icon`, `disabled`; its `label` is its accessible name and tooltip. A handler a call gives for an event the called view's root handles itself now runs after the view's own (a toggle flips, then your `on_click` runs).
- **ButtonGroup** ([#123](https://github.com/mindderivative/tesserae/issues/123)). `widget: ButtonGroup` with `items`, `mode` (none, single, multiple), `selected`, `chosen`, `variant`, `size`, `connected` and `orientation`. A model parameter nobody binds now holds its own value (a view's handlers may write it), a style given as an expression that works out to nothing leaves the field to the stylesheet, and a focus group starts on the item that is pressed.
- **Dialog** ([#151](https://github.com/mindderivative/tesserae/issues/151)). `widget: Dialog` with `open`, `headline`, `text`, `icon`, `actions`, a two-way `result`, `dismissible` and your own content as children; a shipped view on a modal `Overlay`. A `ScrollView` with a `max_height` (or `max_width`) and no size of its own is now as long as its content up to that limit.
- **Tooltip** ([#147](https://github.com/mindderivative/tesserae/issues/147)). A rich `tooltip:` takes `placement` and up to two `actions`; it stays while the pointer moves onto it, closes when an action is pressed, and a long press shows it.
- **Button** ([#118](https://github.com/mindderivative/tesserae/issues/118), [#119](https://github.com/mindderivative/tesserae/issues/119), [#120](https://github.com/mindderivative/tesserae/issues/120), [#121](https://github.com/mindderivative/tesserae/issues/121), [#122](https://github.com/mindderivative/tesserae/issues/122)). `widget: Button` with `variant` (filled, tonal, elevated, outlined, text), five sizes, `shape`, icons, `toggle`/`selected`, `loading` and `disabled`; as wide as its label; lifts on hover; a pressed pill squares off. A shipped view with a stylesheet. `Container` and `Rect` take `disabled`.
- **ScrollView `orientation: horizontal`.** A strip that scrolls sideways: children in a row, the offset along x, `scroll_direction` `right` or `left`, `at_top`/`at_end` for the start and end of the strip.
- **Requires tre 0.5.6.** Timers run on the window's own `after` and `every`; layout `transition:` is the engine's own animation (a change to or from `auto` or a percentage is made at once); the accessibility states (`pressed`, `invalid`, `description`, `current`, `busy`, `value_text`, relations) are set on the node, and a `Divider` is a `separator`. The hand-stepped layout transitions and the dropped-state tolerance are gone. Scroll snap points are asked of tre (mindderivative/tre#166); a `scroll_view` with `orientation="horizontal"` already scrolls sideways.

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
  them from Python; `tesserae.component.embed` is the function. See [Components & Embedding](guide/components.md).

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
