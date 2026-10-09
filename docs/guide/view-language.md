# The View Language

A view is a YAML file that says what is on the screen and how it reacts. One shape does everything: a **node** with a `widget:`
and the properties of that widget, a list of `children:`, and a few keys every node has. This page is the whole language; the rest of the
guide pages are about the widgets and the app around it.

```yaml
name: counter
widget: Container
style: {flex_direction: vertical, width: 240, height: 120, gap: 12, padding: 16}
children:
  - widget: Text
    typography_role: title_large
    text: "Count: {{ count }}"
    style: {width: 200, height: 32, foreground: on_surface}
  - widget: Rect
    name: add
    style: {width: 120, height: 40, background: primary, corner_radius: 8}
    handlers: {on_click: increment}
    a11y: {label: Add one}
```

Files are named `<Name>_View.yaml`, wherever they are in the project. A view with `params:` is a component: another view calls it by
its name, with the params as plain keys. There is no other difference.

## Nodes

| Key | Meaning |
|---|---|
| `widget` | which widget: a built-in, one the app registered, or a view found by name |
| `name` | an optional handle, unique in the view (a letter or `_`, then letters, digits and `_`) |
| `if`, `for`, `key` | include the node while an expression is true; repeat it for each element (`key` is its identity) |
| `slot` | which slot of the view being called a child goes into |
| `state` | local state: names with starting values |
| `style` | layout and paint, and the extras the widget declares |
| `classes` | extra names a stylesheet rule can select |
| `handlers` | events to actions |
| `a11y` | accessibility: `label`, `role`, `hidden`, `live`, `level`, `expanded`, `selected`, `checked`, `value`, `value_min`, `value_max`, `value_step` |
| `interaction` | the hover, focus and press feedback: `true`, `false` or a colour role |
| `window_region` | `drag` or `none`, for a custom title bar |
| `route` | on a view call inside a window: makes it a screen |
| `focus_group` | `horizontal`, `vertical` or `both`: the focusable nodes under it share one tab stop and the arrow keys move among them |
| `children` | child nodes |
| anything else | a **property** of the widget |

An unknown key or property is an error that names the file, line and column and suggests the nearest one:

```
Main_View.yaml:11:5: error: Slider: no property 'valu' (did you mean 'value'; properties: value, disabled)
    11 |     valu: 3
       |     ^
```

Nodes have **ids**, assigned by the loader and never written: the path from the root, using a node's `name` where it has one
(`root.add`) and its place where it does not (`root.children[0]`), with `[key]` added under a `for:`. Give a node a `name` when something has to
find it again: a ViewModel, a stylesheet rule, a test, or a hot reload that should keep its state.

## Widgets and properties

Every widget declares its properties: a type, a default, the values it allows, whether it is required and whether the user edits it (a
**model** property). A value is a literal or an expression, and an expression's result is checked against the type.

| Widget | Properties |
|---|---|
| `Container`, `Rect` | none; they hold children (a `Rect` is the usual clickable box) |
| `Text`, `Link` | `text`, `typography_role`, `font_family`, `font_size`, `font_weight`, `wrap`, `overflow`, `text_align` |
| `TextInput` | `text` (model), `placeholder`, `multiline`, `obscured`, `max_length`, `read_only`, `typography_role`, `font_family`, `font_size`, `font_weight`, `disabled` |
| `TextField` | the Material text field, a view Tesserae ships: see [Text fields](../components/text-fields.md) |
| `Icon` | `icon` (a built-in icon name, or `path` and `view_box`: one of them) |
| `Image`, `Svg` | `src`, `fit`; `src`, `content` |
| `Checkbox`, `Switch`, `RadioButton` | `checked` or `selected` (model), `group`, `disabled` |
| `Slider`, `SpinBox` | `value` (model), `min`, `max`, `step`, `disabled` |
| `CircularProgress`, `LinearProgress`, `LoadingIndicator` | `value` |
| `TimePickerDial` | `hour`, `minute` (model) |
| `ScrollView`, `NodeGraph`, `GraphNode` | a scrolling box; a canvas of linked nodes; a node of it |
| `Window`, `TitleBar`, `Dock`, `DockPanel` | see [Windows, Docks & Embedded Views](windows-and-docks.md); written with `widget:` in a view opened with `app.open_view`, a `Window` root sets the OS window (title, borderless, minimum sizes) and a title bar's buttons, dimming and glyphs follow the app |
| `Slot` | where a calling view's children go |

State is a property (`checked`, `selected`, `value`, `disabled`), never a style. `foreground` is a style extra of the widgets that draw text or
glyphs (`Text`, `Link`, `TextInput`, `Icon`, `Svg`, `LoadingIndicator`); anywhere else it is an error that names who accepts it.

## Expressions

Everything inside `{{ }}` is one expression in a safe subset of Python: arithmetic, comparisons, `and`/`or`/`not`, `x if c else y`, f-strings,
lists, dicts, comprehensions, indexing, and a short list of functions and methods (`len`, `min`, `max`, `sum`, `round`, `sorted`, `str`,
`format_number`, `pluralize`, `clamp`, the usual text and list methods). Nothing else runs: no imports, no attribute that starts with `_`, no
calling an object's own methods, and every expression has limits on size, steps and the numbers it may make. See
[Binding Expressions](bindings.md) for the full list.

A **Signal reads as its value**: `{{ count }}` and `{{ count.get() }}` are the same, and the property follows the Signal. A value that cannot
change (only literals, params with fixed values, loop variables over a fixed list) is worked out once when the view is built.

Names are looked up in the loop variables, then the local state, then the params of the view the expression is written in, then the
ViewModel, then the app (`app.current_screen`), then the built-in functions. `hovered`, `focused` and `pressed` are the interaction state of the
nearest widget with `interaction`.

## Views calling views

```yaml
params:
  title: {type: str, required: true}
  variant: {type: enum, choices: [elevated, outlined], default: elevated}
widget: Container
children:
  - widget: Text
    name: heading
    text: "{{ title }}"
    typography_role: title_medium
    style: {foreground: on_surface}
  - widget: Slot
  - widget: Slot
    name: actions
```

`params:` is a list of names (`[title, icon]`, each required unless written `{icon: null}`) or a mapping of names to a type or to
`{type, default, choices, required, model, doc}`. The types are `str int float bool color length icon enum list dict node nodes handler any`.

A call gives the params as keys, and its `children:` are the slot content. An expression written at the call is read **where it is written**,
in the caller's names, and it stays reactive inside the view. The view cannot see the caller's names. Children go in the default `Slot`, or in
the one named by their `slot:`; a view with no slot takes no children.

A call's own `style`, `classes`, `a11y`, `interaction` and `handlers` lie over the called view's root, and a handler written at the call runs in
the caller's names. A view may call itself (a tree), to a depth of 64.

A param that is `model: true` and is given a bare Signal (`on: "{{ dark }}"`) passes the Signal itself, so the view's own `Switch` edits the
caller's value.

## Repeating, choosing and remembering

```yaml
widget: Container
state: {open: false}
children:
  - for: row in rows
    key: row.id
    widget: Text
    name: row
    text: "{{ row.title }}"
    handlers: {on_click: "open_row(row.id)"}
  - widget: Text
    if: len(rows) == 0
    text: Nothing here
  - widget: Rect
    name: toggle
    style: {width: 40, height: 40, background: primary}
    handlers: {on_click: "open = not open"}
```

- `for:` takes `item in items`, or `i, item in enumerate(items)`. The loop variable is in scope for the node, its children and its handlers.
  If the iterable reads something that can change, the loop is **reactive and needs a `key:`**: when the list is replaced, nodes whose key
  stays are kept, new keys are built, removed keys are gone, and the order follows the list. A list changed in place is not noticed; replace it.
- `if:` builds the node only while its expression is true, and a node under a false `if:` runs nothing. With both on one node, the `if:` is
  tested for each element.
- `state:` makes a Signal for each name, for this node and everything under it. It belongs to the node (to each row under a `for:`), is written
  by handlers, and survives a hot reload for a node that keeps its name or key. Use it for presentation (open, on); what the app cares about belongs
  in the ViewModel.
- `for:`, `if:` and `slot:` are not allowed on the root of a view.

## Handlers

```yaml
widget: Rect
handlers:
  on_click: save                                  # a ViewModel method
  on_hover_enter: "hint = 'Save'"                 # an assignment
  on_change: "query = event.value; page = 0"      # several, separated by ;
  on_tap: window.close                            # a built-in action
```

An event is one of `on_click`, `on_hover_enter`, `on_hover_exit`, `on_change`, `on_focus_enter`, `on_focus_exit`, `on_tap`, `on_long_press`,
`on_pan`, `on_pinch`, `on_touch_start`, `on_touch_move`, `on_touch_end`, `on_touch_cancel`, `on_file_hover`, `on_file_hover_cancel`,
`on_file_drop`, `on_link`, `on_key` (a key pressed), `on_submit` (Enter in a field that is not multiline), `on_press` (the pointer pressed on the node or
anything in it; unlike `on_click` it does not make the node a button), `on_move` (the pointer moved over it, or anywhere while it holds the pointer) and `on_release` (the button let go); a misspelt one is an error.
A handler is a dotted name (`save`, `window.close`, `surface.dismiss`,
`navigate.back`, `navigate.Settings`), or statements, which may call `focus('name')` to give the focus to the node of that name in the view the handler
is written in: an assignment (`=`, `+=`, `-=`, `*=`, `/=`) to local state or a ViewModel Signal, or a call
of a ViewModel method (`navigate_to(screen)` goes to a screen held in a name). `event` is in scope. Assigning to a param, a loop variable or
anything else is an error; so is `if`, `for` or any other statement. A disabled node's handlers do not run.

### Timers

`after(ms, action)` runs `action` once after `ms` milliseconds; `every(ms, action)` runs it every `ms` until cancelled. `action` is text, run in the
scope the handler was written in: an action name (`'bump'`) or statements (`'shown = False'`). A third argument names the timer so `cancel('name')`
can stop it, and starting one of the same name again restarts it (a hover delay, a debounce). A name belongs to the scope that wrote it, as a local
name does: two items of a `for:` each have their own. A timer stops when its view closes or the widget that started it is gone. Times are
frame-quantized: a timer fires on the first frame after its time is up. A mistake in a literal action text is found when the view loads.

```yaml
widget: Container
handlers:
  on_click: "shown = True; after(2000, 'shown = False', 'dismiss')"
  on_hover_exit: "cancel('dismiss')"
```

For Python, `tesserae.timers.Timers(window)` has the same `after`, `every`, `cancel` and `cancel_all`.

## Scrolling

A `ScrollView` draws its `scroll_offset` (pixels, 0 or more; tre clamps it to the content once the content has a size) and reports where it is to
whatever you bind to it, so other widgets can react. Each of these is bound the way a two-way property is, to a ViewModel Signal or a `state:` name:

| Property | Meaning |
| --- | --- |
| `scroll_offset` | Two-way: setting the Signal scrolls, and scrolling writes the Signal. |
| `at_top`, `at_end` | Scrolled to the start, or as far as it goes. `at_end` is false until the content has been laid out. |
| `scroll_direction` | `'down'` or `'up'` for the last scroll, `'none'` before the first. |

```yaml
widget: Container
state: {top: true, way: none}
children:
  - widget: ScrollView
    at_top: "{{ top }}"
    scroll_direction: "{{ way }}"
    children: []
  - widget: Container
    if: top or way == 'up'              # a bar that hides while the list scrolls down
```

A view scrolls vertically; a `ScrollView` that nothing is bound to keeps its own position.

## Input masks

`mask:` on a `TextInput` (or a `TextField`) puts what the user types or pastes in a pattern: `#` is a digit, `A` a letter, `*` a letter or digit, `\`
makes the next character a literal, and any other character is a literal that comes by itself.

```yaml
widget: TextField
label: Phone
text: "{{ phone }}"
mask: "(###) ###-####"          # 5551234567 becomes (555) 123-4567; so does 555-123-4567
```

The text is read left to right and each slot takes the next character it accepts, so a paste in any format is fitted. A literal is added only
when more input follows it (`123` is `(123`, the `) ` comes with the fourth digit), so backspace is never stuck on one; one the user typed is kept; what
does not fit is dropped. The bound Signal holds the formatted text. The mask is applied to edits, not to a value a ViewModel sets, and tre's input
has no caret control yet, so an edit in the middle of the text moves the caret to the end.

## Drawing

`widget: Canvas` is a surface you draw on with data. `draw:` lists commands painted in order: `{rect: [x, y, width, height]}`,
`{circle: [cx, cy, radius]}` and `{path: [point, ...], width: 2}`, each with a `color` (a theme role, a CSS colour or `role@N%`). In a path the
first point is `[x, y]` and each later one is a line `[x, y]`, a quadratic `[cx, cy, x, y]` or a cubic `[c1x, c1y, c2x, c2y, x, y]`. Numbers are
logical pixels from the canvas's top-left; size the canvas with `style`. Write `draw: "{{ [...] }}"` and it repaints when a Signal it reads changes.

```yaml
widget: Canvas
style: {width: 120, height: 24}
draw: "{{ [{'rect': [0, 10, 120, 4], 'color': 'surface_variant'}, {'rect': [0, 10, 120 * progress, 4], 'color': 'primary'}] }}"
```

### Dragging

`capture()` makes the node whose handler is running receive every pointer event until the button is let go or `release()` is called, so a drag
keeps following the pointer outside the node. `cursor('grabbing')` sets that node's pointer shape (any of tre's names: `default`, `pointer`, `text`, `grab`,
`grabbing`, `move`, `not_allowed`, `col_resize`, ...; `cursor(None)` puts back the one its style gives). Position and distance are in `event`
(`event.x`, `event.y`; a pan's `event.delta_x`). They act on the widget the handler is written on, so a timer's action cannot call them.

```yaml
widget: Container
handlers:
  on_press: "dragging = True; capture(); cursor('grabbing')"
  on_move: "x = event.x if dragging else x"
  on_release: "dragging = False; release(); cursor(None)"
```

### The clipboard

`copy(text)` puts text on the OS clipboard (a number is copied as text) and says whether it could; `paste()` is the text on it, or `''` when it holds none or
cannot be reached. Both work in a handler, and `paste()` can be used where a value is wanted:

```yaml
widget: Container
handlers:
  on_click: "ok = copy(name)"
  on_long_press: "name = paste()"
```

### Opening a link

`open_url(url)` hands a link to the OS (the default browser or mail program) and says whether it could. Only `http`, `https`, `mailto` and `tel` links
are opened: a view's text can come from anywhere, and `file:`, `javascript:` or an application's own scheme would run something rather than show a page, so
those are an error naming the call. For Python, `tesserae.urls.open_url(url)` is the same.

```yaml
widget: Link
text: Read the docs
handlers: {on_click: "open_url('https://example.com/docs')"}
```

## Long lists

A `for:` builds every row it makes, which is fine for a screenful and not for ten thousand. `widget: VirtualList` is a scrolling list of equal-height
rows that builds only the rows in view, and more as it scrolls. Its one child is the `for:`; write the row once.

```yaml
widget: VirtualList
item_height: 48
overscan: 3                           # rows built past each edge (the default)
scroll_offset: "{{ y }}"              # as for a ScrollView, with at_top, at_end and scroll_direction
children:
  - widget: Container
    for: row in rows
    key: row.id
    handlers: {on_click: "picked = row.id"}
    children:
      - {widget: Text, text: "{{ row.name }}", typography_role: body_large, style: {foreground: on_surface}}
```

The list is as tall as all its rows, and each row built sits at its place in it, so a row's own `style` sets its width, background and so on but not its
height or position. Rows leave and come as the list scrolls: a row's local `state:` is not kept across that. Rows must all be `item_height` tall. Opening a
list of 10 000 builds about a dozen rows.

## Overlays

`widget: Overlay` shows its children in a layer over the window while `open` is true: a menu, a popover, a dialog. It takes no room where it is written.

```yaml
widget: Overlay
open: "{{ menu_open }}"
anchor: trigger            # the name of a node in this view; the layer sits against it
placement: below           # or above, start, end; it flips or shifts to fit
style: {width: 160, background: surface_container}
children:
  - {widget: Text, text: Rename, typography_role: label_large, style: {foreground: on_surface}}
```

Escape and a press outside close it, and write `false` to the Signal `open` is bound to; with an `open` that is not a Signal it stays closed until `open`
goes false. Focus goes back to where it was. `dismissible: false` turns both off.

`modal: true` makes the layer a scrim (the `scrim` colour at 32%) over the whole window, blocking input to what is under it and keeping Tab inside; it
follows the window's size and centres its children unless the style places them (`align_content`). Put the dialog itself in a child, with its own size
and background. A press on the scrim closes a dismissible modal; a press on its content does not. Without an `anchor` and not modal, the layer sits at its own `x` and `y`.

## Focus

`focus('input')` in a handler gives the focus to the node named `input` in the same view (names are unique in a view, and a view never reaches into
the one it calls). `on_press: "focus('input')"` on a container makes a click anywhere in it, padding included, land in the field inside it.

A `focus_group` makes a toolbar, a tab strip, a menu or a radio set behave as one control: Tab visits **one** of its items (the one that last had
the focus), the arrow keys of its axis move the focus to the next and the previous item (wrapping), `Home` and `End` go to the first and last, and typing
the start of an item's name jumps to it (the same letter again goes on to the next item that starts with it; a pause of a second starts a new search; typing in
a text field inside the group is the field's). Disabled items are skipped, and a group inside a group looks after its own items.

## Two-way properties

A `model` property given **one bare reference** to a Signal or local state is two-way: the user's edit is written back to it. Any other
expression is one-way, and the widget shows the expression's value.

```yaml
widget: Switch
selected: "{{ dark }}"                 # toggling writes `dark`
```

## Style

`style:` holds layout and paint: size and spacing (`width height min_width max_width min_height max_height aspect_ratio padding margin`),
flex and grid, alignment, position, `background border_width border_color corner_radius opacity elevation`, effects (`blur backdrop_blur
blend_mode filter cursor clip_children`), and the widget's extras. Values may be expressions.

A **stylesheet** (`<Name>_Stylesheet.yaml`) holds rules, so a look is written once and not on every node:

```yaml
styles:
  - widget: Card
    style: {corner_radius: 12}
  - widget: Card
    variant: outlined
    style: {border_width: 1, border_color: outline}
  - widget: Card
    part: heading
    state: hovered
    style: {foreground: primary}
```

A rule names a `widget` (a built-in or a view), and may add `variant`, `size`, `shape` (properties the widget declares), `classes`, `name`, a
`part` (a named node inside that widget's view) and a `state` (`hovered focused focus_visible pressed disabled selected checked expanded error read_only`; the last six read the
widget's own property). The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the
widget alone, and a later rule wins a tie. A widget's own shipped looks are the lowest layer and the app's stylesheet is above them. **A
node's inline `style:` beats every rule, for the fields it sets and no others.** A rule's value may be an expression over the widget's params.

## ViewModels

A view with a `name:` is bound to the ViewModel that serves that name; a view without one is a static visual.

```python
class DataViewModel(ViewModel):
    views = ["data_pie", "data_list"]          # the views it serves

    def __init__(self):
        super().__init__()
        self.rows = Signal([...])


app = App(root=".")
app.bind(DataViewModel)
app.open_view("DataPie")
app.open_view("DataList")
```

**One instance serves every view that names it**, wherever they are, so a pie chart and a list of the same rows are two views of one
Signal. `app.bind(DataViewModel)` makes it once, when the first view opens; `app.bind(instance)` uses yours; `app.bind(factory=DataViewModel)`
makes one per view instance. The ViewModel finds its open views in `self.views[name]`: `.node(name)`, `.state(var)`, `.show()`, `.hide()`, and
`self.show("data_phone", "data_list")` shows one in place of another. `on_attached(view)` and `on_detached(view)` are called as views open
and close.

`app.check()` compares every name, action and `expects:` entry of the open views with their ViewModels without a window. `expects:` is optional
data in a view's header: `expects: {count: int, rows: list, add: handler}`.

## Tools

- `tesserae migrate-yaml [PATH] [--write] [--force]` moves a project written in the older syntax to this one: [Migrating](../migration.md#to-050).
- A JSON schema of every widget's node, with its properties, ships in the package as `schema/tesserae-widget-schema.json`.
