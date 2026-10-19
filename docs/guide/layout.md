# Layout

A view lays out with flexbox: every node is a box, and a container
places its children in a row or a column. This page covers the layout
keys of a node's `style:` (all of them work in a stylesheet too) and the
`ScrollView` widget. Every style key is listed in the
[YAML reference](../api/yaml.md); the whole language is in
[The View Language](view-language.md).

## Rows and columns

`flex_direction` is `horizontal` (the default) or `vertical`. `gap` spaces
the children, `padding` insets them, and `margin` spaces a child from
its neighbours; both take a number or `{top:, right:, bottom:, left:}`.

```yaml
widget: Container
style: {flex_direction: vertical, gap: 12, padding: 16, width: 320}
children:
  - widget: Text
    name: title
    text: Settings
    typography_role: title_large
    style: {foreground: on_surface}
  - widget: Container
    name: row
    style: {flex_direction: horizontal, gap: 8, align_content: left}
    children:
      - widget: Rect
        name: swatch
        style: {width: 24, height: 24, background: primary, corner_radius: 12}
      - widget: Text
        name: label
        text: Primary
        typography_role: body_large
        style: {foreground: on_surface}
```

## Placing children: `align_content`

`align_content` says where a node's children sit in it, as one of nine positions:

| | | |
| --- | --- | --- |
| `top_left` | `top` | `top_right` |
| `left` | `center` | `right` |
| `bottom_left` | `bottom` | `bottom_right` |

It means the same in a row or a column: `left` is the left edge, `bottom` the bottom, `center` the middle.
Not set, children start at the top left and a box with no `width` stretches across the layout, so a column of
`Rect`s fills the width. A `Text` is as wide as its text.

```yaml
widget: Container
style: {flex_direction: vertical, width: 240, height: 120, align_content: center}   # a column, centred
children:
  - {widget: Rect, name: box, style: {width: 40, height: 20, background: primary}}
```

`spread` shares out the room that is left along the layout: `between` puts it between the children,
`around` around each, `evenly` everywhere. `align_content` still places them across.

```yaml
widget: Container
style: {flex_direction: horizontal, width: 320, spread: between, align_content: left}
children:
  - {widget: Rect, name: first, style: {width: 40, height: 20, background: primary}}
  - {widget: Rect, name: second, style: {width: 40, height: 20, background: primary}}
  - {widget: Rect, name: third, style: {width: 40, height: 20, background: primary}}
```

A child puts itself somewhere else than its parent says with `align_self`, which takes the same nine
positions and acts across the layout.

## How a node takes room: `flex`

`flex` is a node's own sizing in its parent:

| Value | What it does |
| --- | --- |
| `none` (the default) | As big as its `width` and `height`, or its content, and never squeezed. |
| `expand_horizontal` | Takes the room left over, horizontally. |
| `expand_vertical` | Takes the room left over, vertically. |
| `fill` | Both. |

In a row, `expand_horizontal` takes what the other children leave (two of them split it), and
`expand_vertical` stretches the node to the row's height; in a column it is the other way round. An
explicit `width` is the size it starts from, and `expand_*` overrides it across the layout.

## Sizes

`width` and `height` take pixels, `"auto"` (the default: its content's
size, or stretched), `"fit-content"` (its content's size along the line of the layout: across it a box is still stretched unless its parent sets
`align_content` or it sets `align_self`), a percentage of
the parent (`"50%"`), or a sum of those such as `"calc(100% - 16)"`
([below](#a-size-that-is-the-parent-minus-something)). A size is never
negative. `min_width`, `max_width`, `min_height` and `max_height` bound it
with a number, `"auto"` or a percentage, and `aspect_ratio` (width over
height) gives the missing side from the one that's set: a side the layout stretches is not computed, so set `align_content` on the parent or
`align_self` on the node (or use `flex_wrap`). A `Text` with no `width` is measured to its text; `width: auto` stretches it like any box. A size that tre
would refuse (`40px`, `10vw`, `stretch`, `100%-16`) is an error at the line
that writes it, saying what to write.

### Text in a box

A `Text` or `Link` with no `width` or `height` is measured to fit its
text (a `Text` needs a `typography_role` or a `font_family`). Its `text_align` property places the text inside its width: `start` (the default), `center` or `end`.
A `Text` that is `center` or `end` aligned and has no `width` of its own fills its parent's width, so
there is room to align in; its text's width is the least it takes. Give it a `width` to choose another.

```yaml
widget: Text
text: Settings
typography_role: title_large
text_align: center
style: {width: 240, foreground: on_surface}
```

A `TextField` has no `text_align`: what is typed starts at the left.

#### One line, or an ellipsis

A line too long for its box breaks onto the next (`wrap: word`, the default). `wrap: none` keeps one line
(and the text is then always drawn from the start: `text_align` has nothing to align within),
and `overflow: ellipsis` ends a line that doesn't fit with an ellipsis instead of cutting it off
(`overflow: clip`, the default). Together they make a single-line label that truncates:

```yaml
widget: Text
text: A very long note title
typography_role: body_large
wrap: none
overflow: ellipsis
style: {width: 160, foreground: on_surface}
```

Give the text a width (a number, or `flex: expand_horizontal` in a row with `min_width: 0`) for the ellipsis to have
something to truncate to. A `TextField` has neither property.

The labels of the built-in [components](../components/index.md) are single lines that end in an
ellipsis when they don't fit. `max_lines: 2` stops a long text at two lines (with `overflow: ellipsis` the second ends in an
ellipsis), and a Text with a width and no height is as tall as the lines it wraps to; `letter_spacing: 0.5` adds space between the letters, in pixels.

## Sharing a row

`flex: expand_horizontal` shares the space left over (it on two children splits it evenly); the other
children keep their sizes.

```yaml
widget: Container
style: {flex_direction: horizontal, width: 400, height: 48, gap: 8}
children:
  - widget: Rect
    name: sidebar
    style: {width: 120, background: surface_container}
  - widget: Rect
    name: main
    style: {flex: expand_horizontal, max_width: 400, background: surface_container_high}
```

## Wrapping

`flex_wrap: wrap` starts a new row (or column) when the children don't
fit. With a fixed `width` it gives a gallery of
equal tiles. `align_wrapped` (`start`, `center`, `end`, `stretch`, `between`, `around`, `evenly`) says how
the lines share the room left across the layout.

```yaml
widget: Container
style: {flex_direction: horizontal, flex_wrap: wrap, gap: 8, width: 340}
children:
  - widget: Rect
    name: tile
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
  - widget: Rect
    name: tile2
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
  - widget: Rect
    name: tile3
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
  - widget: Rect
    name: tile4
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
```

Rows of a wrapped layout don't line up their columns with each other,
and a tile can't span two columns: for that, use a grid.

## Grids

`display: grid` lays a container's children out in rows and columns.
`grid_template_columns` and `grid_template_rows` list the tracks: pixels, `auto` (its content), `fr` (a share of what's
left), percentages, `minmax(min, max)` and `repeat(n, ...)`, as a string
(`"120 1fr"`) or a list (`[120, "1fr"]`). Children fill the cells in
order.

```yaml
widget: Container
style: {display: grid, grid_template_columns: "1fr 1fr", row_gap: 12, column_gap: 16, width: 360, padding: 16}
state: {name: "", email: ""}
children:
  - widget: TextField
    name: name
    label: Name
    text: "{{ name }}"
  - widget: TextField
    name: email
    label: Email
    text: "{{ email }}"
```

- `grid_auto_rows` and `grid_auto_columns` size the tracks the templates
  don't list, and `grid_auto_flow` fills by `row` (the default) or
  `column`, `dense` to fill holes.
- A child is placed with `grid_column` and `grid_row`: a line number
  (`2`, or `-2` counting from the end), a span (`"span 2"`), or a range
  (`"1 / 3"`).
- `row_gap` and `column_gap` space the tracks; `gap` sets both, and
  either one wins over it.
- `align_cells` (on the grid) places the items in their cells, as one of the nine positions, and
  `align_self` (on a child) places one; `align_tracks` (`start`, `center`, `end`, `stretch`, `between`,
  `around`, `evenly`) places the tracks in a grid bigger than they are. A grid uses these instead of
  `align_content` and `spread`.

A dashboard of tiles, one spanning two columns:

```yaml
widget: Container
style: {display: grid, grid_template_columns: "repeat(3, 1fr)", grid_auto_rows: 96, gap: 8, width: 360}
children:
  - widget: Rect
    name: wide
    style: {grid_column: "span 2", background: primary_container, corner_radius: 12}
  - widget: Rect
    name: one
    style: {background: secondary_container, corner_radius: 12}
  - widget: Rect
    name: two
    style: {background: secondary_container, corner_radius: 12}
  - widget: Rect
    name: three
    style: {grid_column: "2 / 4", background: tertiary_container, corner_radius: 12}
```

A `ScrollView` can be a grid too: its `display` and track keys lay out
its children, and a `grid_column` on it places the scroll view in its
own parent.

## A size that is the parent minus something

A size may be a sum: `width: "calc(100% - 16)"`, or the same without the wrapper, `"100% - 16"`. The terms are numbers, percentages and pixels
written `16px`, joined by `+` and `-` with a space each side; there is no `*`, `/` or `min()`, and a unit other than pixels (`vw`, `em`) is an error. A sum works
for `width` and `height`; the limits (`min_width`...) take a number, `auto` or a percentage. A sum may be an expression (`width: "{{ gutter }}"`
working out to `"100% - 24"`). In the flow you often do not need one, because the layout does the sum and follows the parent when it changes:

```yaml
widget: Container
style: {flex_direction: vertical, width: 300, gap: 8}
children:
  # the full width less an 8 pixel gutter each side (100% - 16)
  - {widget: Rect, name: bar, style: {height: 20, flex: expand_horizontal, margin: {left: 8, right: 8}, background: primary}}

  # two columns with a 16 pixel gutter (50% - 8 each)
  - widget: Container
    name: columns
    style: {gap: 16, height: 20}
    children:
      - {widget: Container, name: left, style: {flex: fill, background: secondary}}
      - {widget: Container, name: right, style: {flex: fill, background: tertiary}}

  # what is left of a row after a fixed part (100% - 80)
  - widget: Container
    name: split
    style: {height: 20}
    children:
      - {widget: Rect, name: icon, style: {width: 80, height: 20, background: error}}
      - {widget: Container, name: rest, style: {flex: fill, background: outline}}
```

An **absolutely positioned** node stretched between two edges of its parent takes insets instead (below).

## Placing a node against another node

Three style fields place a node against another node, wherever it is written, and keep it there as the target moves (tre lays it out after the target, so
there is no lag):

```yaml
widget: Container
style: {width: 300, height: 200, padding: 40}
children:
  - {widget: Rect, name: target, style: {width: 60, height: 40, background: primary}}
  - widget: Rect
    style: {anchor: target, placement: top_end, offset: [6, -6], width: 12, height: 12, background: error}
```

| Field | What it says |
| --- | --- |
| `anchor` | The `name` of the node to sit against, or `parent` for the node it is written inside. The nearest node of that name wins: in a `for:` row it is the row's own node, then the view's, then the view that called this one. |
| `placement` | `below` (the default), `above`, `start`, `end`, or a corner: `top_start`, `top_end`, `bottom_start`, `bottom_end`, or `center`. A corner puts the node's *centre* on that corner of the target (and `center` on the target's centre); `offset` moves it from there. |
| `offset` | `[dx, dy]` in pixels, added to the placement. |

The node stays in the tree, so a parent's `clip_children` cuts it and its `z_index` orders it among its siblings, unlike a layer. It takes itself out of the
flow (it is absolute by itself). `anchor`, `placement` and `offset` may come from a stylesheet rule or an expression. A missing anchor name is an error at the
node, with the nearest name; a bad `placement` or `offset` is found at load. Take the fields out and the node is back in the flow. `placement` and `offset` do nothing without an `anchor`.

If the anchor goes (an `if:`), or is hidden with `visible:` (its own, or that of anything it is inside), the node is hidden with it and comes back when the anchor does,
unless its own `visible:` says no. A control with a `label:` is anchored as the row that holds the box and its label. `transition:` does not ease a placement.

An `Overlay` is the same thing as a layer: drawn above the whole window, not cut by a parent's `clip_children`, its own Tab scope. It takes the corners and `offset`
too, and `flip: false` keeps it where it is put instead of moving it to the other side when it does not fit (the default, `true`, suits a menu; a marker wants
`false`). See [Overlays](overlays.md).

## Placing a node exactly

`position: absolute` takes a node out of the flow, and `x`/`y` place it
in its parent, in pixels or percentages. The insets `left`, `top`, `right` and `bottom` say how far it is from each edge of its parent, and `inset` says all four
at once: `left: 8, right: 16` stretches a node across its parent less 8 and 16 pixels, and `inset: 4` fills the parent less 4 each side. An inset is a number
(it may be negative), a percentage or `auto`. `x` is the same as `left` and `y` as `top`; giving both, or `x` with `inset`, in one `style:` is an
error, since one would not be heard. A rule's `inset` gives way to an edge the node (or a more specific rule) says itself. On a node in the flow an inset moves it from its place. An inset
does not ease: `transition:` takes `x` and `y` for a position. A control with a `label:` (a `Checkbox`, `RadioButton` or `Switch`) is placed as the row that holds the box and its label, so an inset or a margin
moves both. `z_index` (an integer)
draws it above or below its siblings, and a container with
`clip_children: true` cuts its children to its own box. `overflow: hidden`
is another way to write that (and `overflow: visible` is `clip_children: false`); a node that gives both must
agree. It does not scroll: a `ScrollView` does. `pointer_events: none` lets the pointer through a node
(see [Gradients & Effects](effects.md#the-pointer)).

```yaml
widget: Container
style: {width: 200, height: 120, clip_children: true, background: surface_container}
children:
  - widget: Rect
    name: badge
    style: {position: absolute, x: 176, y: 8, width: 16, height: 16, corner_radius: 8, background: error, z_index: 1}
  - {widget: Rect, name: strip, style: {position: absolute, left: 8, right: 8, bottom: 8, height: 4, background: primary}}
```

## Scrolling

`widget: ScrollView` scrolls its children vertically when they're taller
than it. Its `style:` sizes, places and paints the scroll view;
`flex_direction` (vertical by default), `gap`, `padding`, alignment and
wrapping lay out its children inside it.

```yaml
widget: Container
style: {width: 320, height: 400}
children:
  - widget: ScrollView
    name: list
    style: {width: 320, height: 200, gap: 4, padding: 8, background: surface}
    children:
      - widget: Rect
        name: first
        style: {height: 56, background: surface_container, corner_radius: 12}
      - widget: Rect
        name: second
        style: {height: 56, background: surface_container, corner_radius: 12}
      - widget: Rect
        name: third
        style: {height: 56, background: surface_container, corner_radius: 12}
      - widget: Rect
        name: fourth
        style: {height: 56, background: surface_container, corner_radius: 12}
```

- The wheel scrolls it. The keys do too, when it or a node inside it has
  focus: the arrows by a line, Page Up and Page Down by its height, Home
  and End to the ends. A node that handles keys itself keeps them (a
  text field keeps its arrows, but not Page Up and Page Down). Keys held
  with Ctrl, Alt or Meta are shortcuts and don't scroll; Shift still
  does. The scroll view is a Tab stop, so it can be scrolled with nothing
  inside it focusable.
- A `ScrollView` inside another passes on what it can't use, as in a
  browser: a wheel or a scroll key over an inner one that's already at
  that end, or whose content fits, scrolls the one outside it. One that can move takes the whole wheel
  or key.
- A child that takes focus is scrolled into view, just as far as needed,
  and so is one assistive technology asks to see (`scroll_into_view`).
- `scroll_offset: "{{ pos }}"`, one bare reference to a Signal or a `state:`
  name, is two-way: setting it scrolls, and scrolling writes back where the
  user scrolled, to save and restore a position. An offset past the end is
  held at the end at once, and that is what's written back (on the next frame, when the Signal was the one that set it). `at_top`,
  `at_end` and `scroll_direction` report where it is, the same way (see
  [Scrolling](view-language.md#scrolling)).
- Its scrollbar is the theme's `outline`.
- It scrolls vertically, or sideways with `orientation: horizontal` (its children then sit in a row, and `scroll_direction` is `right` or `left`).
- `snap: start` (or `center`, `end`) makes it settle, when scrolling stops, on the nearest child whose style has a matching `snap_align`.

For a list built from data, put a node with a `for:` inside a `ScrollView`
(the rows are all built). For thousands of equal rows, use a `VirtualList`,
which builds only the rows in view: [Long lists](view-language.md#long-lists).
From Python, the container a [`Repeater`](repeater.md) fills goes inside a
`ScrollView` too.

## Hiding a node

`visible: false` on any node takes it out of the layout (it takes no room and no pointer) while it stays in
the tree. `visible: true` puts it back at once. An expression is allowed: `visible: "{{ expanded }}"`.
