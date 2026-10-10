# Changelog

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
