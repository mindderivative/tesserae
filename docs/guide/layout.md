# Layout

A view lays out with flexbox: every node is a box, and a container
places its children in a row or a column. This page covers the layout
keys of a node's `style:` (all of them work in a stylesheet too) and the
`ScrollView` kind.

## Rows and columns

`flex_direction` is `horizontal` (the default) or `vertical`. `gap` spaces
the children, `padding` insets them, and `margin` spaces a child from
its neighbours; both take a number or `{top:, right:, bottom:, left:}`.

```yaml
id: root
kind: Container
style: {flex_direction: vertical, gap: 12, padding: 16, width: 320}
children:
  - id: title
    kind: Text
    text: {content: "Settings", typography_role: title_large}
    style: {foreground: on_surface}
  - id: row
    kind: Container
    style: {flex_direction: horizontal, gap: 8, align_items: center}
    children:
      - id: swatch
        kind: Rect
        style: {width: 24, height: 24, background: primary, corner_radius: 12}
      - id: name
        kind: Text
        text: {content: "Primary", typography_role: body_large}
        style: {foreground: on_surface}
```

`align_items` places children across the direction (`flex_start`,
`center`, `flex_end`, `stretch`, `baseline`); `justify_content` along it
(`flex_start`, `center`, `flex_end`, `space_between`, `space_around`,
`space_evenly`). A child overrides its parent's `align_items` with
`align_self` (M71).

## Sizes

`width` and `height` take pixels, `"auto"` (the default: its content's
size, or stretched), or a percentage of the parent (`"50%"`).
`min_width`, `max_width`, `min_height` and `max_height` bound it the same
ways, and `aspect_ratio` (width over height) gives the missing side from
the one that's set (M71).

### Text in a box

A `Text` or `Link` with no `width` or `height` is measured to fit its
text. Give it a `width` and `text:`'s `text_align` places the text inside
it: `start` (the default), `center` or `end` (0.3.1).

```yaml
- id: heading
  kind: Text
  text: {content: "Settings", typography_role: title_large, text_align: center}
  style: {width: 240, foreground: on_surface}
```

A `TextField` has no `text_align`: what is typed starts at the left.

## Flexible sizing

`flex_grow` shares the space left over (`1` on two children splits it
evenly), `flex_shrink` gives space back when there isn't enough (`1`, the
default, shrinks; `0` doesn't), and `flex_basis` is the size to start
from.

```yaml
id: root
kind: Container
style: {flex_direction: horizontal, width: 400, height: 48, gap: 8}
children:
  - id: sidebar
    kind: Rect
    style: {width: 120, flex_shrink: 0, background: surface_container}
  - id: main
    kind: Rect
    style: {flex_grow: 1, max_width: 400, background: surface_container_high}
```

## Wrapping

`flex_wrap: wrap` starts a new row (or column) when the children don't
fit (M71). With a fixed `flex_basis` or `width` it gives a gallery of
equal tiles:

```yaml
id: root
kind: Container
style: {flex_direction: horizontal, flex_wrap: wrap, gap: 8, width: 340}
children:
  - id: tile
    kind: Rect
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
  - id: tile2
    kind: Rect
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
  - id: tile3
    kind: Rect
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
  - id: tile4
    kind: Rect
    style: {width: 100, aspect_ratio: 1, background: secondary_container, corner_radius: 12}
```

Rows of a wrapped layout don't line up their columns with each other,
and a tile can't span two columns: for that, use a grid.

## Grids

`display: grid` lays a container's children out in rows and columns
(M74, on `tre` 0.4.2). `grid_template_columns` and `grid_template_rows`
list the tracks: pixels, `auto` (its content), `fr` (a share of what's
left), percentages, `minmax(min, max)` and `repeat(n, ...)`, as a string
(`"120 1fr"`) or a list (`[120, "1fr"]`). Children fill the cells in
order.

```yaml
id: root
kind: Container
style: {display: grid, grid_template_columns: "120 1fr", row_gap: 12, column_gap: 16, width: 360, padding: 16}
children:
  - id: name_label
    kind: Text
    text: {content: "Name", typography_role: label_large}
    style: {foreground: on_surface_variant}
  - id: name
    kind: TextField
    text: {content: "", typography_role: body_large}
    style: {height: 40, background: surface_container_highest, corner_radius: 4}
  - id: email_label
    kind: Text
    text: {content: "Email", typography_role: label_large}
    style: {foreground: on_surface_variant}
  - id: email
    kind: TextField
    text: {content: "", typography_role: body_large}
    style: {height: 40, background: surface_container_highest, corner_radius: 4}
```

- `grid_auto_rows` and `grid_auto_columns` size the tracks the templates
  don't list, and `grid_auto_flow` fills by `row` (the default) or
  `column`, `dense` to fill holes.
- A child is placed with `grid_column` and `grid_row`: a line number
  (`2`, or `-2` counting from the end), a span (`"span 2"`), or a range
  (`"1 / 3"`).
- `row_gap` and `column_gap` space the tracks; `gap` sets both, and
  either one wins over it.
- `justify_items` (on the grid) and `justify_self` (on a child) place
  children across their cells; `align_items` and `align_self` down them;
  `align_content` places the tracks in a grid bigger than they are.

A dashboard of tiles, one spanning two columns:

```yaml
id: root
kind: Container
style: {display: grid, grid_template_columns: "repeat(3, 1fr)", grid_auto_rows: 96, gap: 8, width: 360}
children:
  - id: wide
    kind: Rect
    style: {grid_column: "span 2", background: primary_container, corner_radius: 12}
  - id: one
    kind: Rect
    style: {background: secondary_container, corner_radius: 12}
  - id: two
    kind: Rect
    style: {background: secondary_container, corner_radius: 12}
  - id: three
    kind: Rect
    style: {grid_column: "2 / 4", background: tertiary_container, corner_radius: 12}
```

A `ScrollView` can be a grid too: its `display` and track keys lay out
its children, and a `grid_column` on it places the scroll view in its
own parent.

## Placing a node exactly

`position: absolute` takes a node out of the flow, and `x`/`y` place it
in its parent, in pixels or percentages (M71). `z_index` (an integer)
draws it above or below its siblings, and a container with
`clip_children: true` cuts its children to its own box.

```yaml
id: root
kind: Container
style: {width: 200, height: 120, clip_children: true, background: surface_container}
children:
  - id: badge
    kind: Rect
    style: {position: absolute, x: 176, y: 8, width: 16, height: 16, corner_radius: 8, background: error, z_index: 1}
```

A node whose style gives these keeps what Python code sets on it
otherwise: a widget placed with `x=`/`y=`, or an overlay, keeps its place
through a re-theme or a reload.

## Scrolling

`kind: ScrollView` scrolls its children vertically when they're taller
than it (M71). Its `style:` sizes, places and paints the scroll view;
`flex_direction` (vertical by default), `gap`, `padding`, alignment and
wrapping lay out its children inside it.

```yaml
id: root
kind: Container
style: {width: 320, height: 400}
children:
  - id: list
    kind: ScrollView
    style: {width: 320, height: 200, gap: 4, padding: 8, background: surface}
    children:
      - id: first
        kind: Rect
        style: {height: 56, background: surface_container, corner_radius: 12}
      - id: second
        kind: Rect
        style: {height: 56, background: surface_container, corner_radius: 12}
      - id: third
        kind: Rect
        style: {height: 56, background: surface_container, corner_radius: 12}
      - id: fourth
        kind: Rect
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
  that end, or whose content fits, scrolls the one outside it (`tre`
  0.4.4; M80). One that can move takes the whole wheel or key.
- A child that takes focus is scrolled into view, just as far as needed,
  and so is one assistive technology asks to see (`scroll_into_view`).
  (`tre` does all of this since 0.4.2; M73.)
- `scroll_offset` binds (`bindings: {scroll_offset: "{{ pos.get() }}"}`),
  and `two_way: scroll_offset` writes back where the user scrolled, to
  save and restore a position. An offset past the end is held at the end
  at once, and that is what's written back (`tre` 0.4.3; M79).
- Its scrollbar is the theme's `outline`.
- It scrolls vertically only, as `tre`'s does.

For a long list built from data, put a `Repeater`'s container
(`tesserae.Repeater`) inside a `ScrollView`.
