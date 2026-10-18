# TextField_Stylesheet.yaml

The look of TextField (Material 3). A state here is the state of the whole field: `focused` is true while anything inside it has the focus. A later rule wins a tie, so error comes after focused and hovered: a field in error keeps the error colour while it is used.

The look of [`TextField`](../../components/text-fields.md) (in [Text fields](../../components/text-fields.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of TextField (Material 3). A state here is the state of the whole field: `focused` is true while anything inside it has the focus.
# A later rule wins a tie, so error comes after focused and hovered: a field in error keeps the error colour while it is used.
styles:
  - widget: TextField
    style: {width: 280, background: transparent}  # a fill, even a clear one, is what lets the pointer find the field
  - widget: TextField
    state: disabled
    style: {opacity: 0.38}

  # the box
  - widget: TextField
    part: box
    variant: filled
    style: {background: surface_container_highest, corner_radius: {top: 4}}  # square below: the line under it is its bottom edge
  - widget: TextField
    part: box
    variant: outlined
    style: {border_width: 1, border_color: outline, corner_radius: 4}
  - widget: TextField
    part: box
    variant: outlined
    state: hovered
    style: {border_color: on_surface}
  - widget: TextField
    part: box
    variant: outlined
    state: focused
    style: {border_width: 2, border_color: primary}
  - widget: TextField
    part: box
    variant: outlined
    state: error
    style: {border_color: error}

  # the line under a filled field
  - widget: TextField
    part: indicator
    style: {height: 1, background: on_surface_variant}
  - widget: TextField
    part: indicator
    state: hovered
    style: {background: on_surface}
  - widget: TextField
    part: indicator
    state: focused
    style: {height: 2, background: primary}
  - widget: TextField
    part: indicator
    state: error
    style: {background: error}

  # the label
  - widget: TextField
    part: label
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: label
    state: focused
    style: {foreground: primary}
  - widget: TextField
    part: label
    state: error
    style: {foreground: error}

  # the typing, and the text around it
  - widget: TextField
    part: input
    style: {foreground: on_surface, background: transparent}  # the box around the typing is the field's own
  - widget: TextField
    part: prefix
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: suffix
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: supporting
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: supporting
    state: error
    style: {foreground: error}
  - widget: TextField
    part: counter
    style: {foreground: on_surface_variant}

  # the icons
  - widget: TextField
    part: leading_icon
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: trailing_icon
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: reveal_button
    style: {background: transparent}
  - widget: TextField
    part: reveal_icon
    style: {foreground: on_surface_variant}
  - widget: TextField
    part: error_icon
    style: {foreground: error}
```

## How it reaches the view

Each rule names `widget: TextField` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `TextField` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `280` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| state `disabled` | `opacity` | `0.38` | From 0 (clear) to 1 (opaque). |

### `box` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| `variant: filled` | `background` | `surface_container_highest` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: filled` | `corner_radius` | `{top: 4}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `variant: outlined` | `border_width` | `1` | The width of its border, in pixels. |
| `variant: outlined` | `border_color` | `outline` | The colour of its border: a colour or a gradient. |
| `variant: outlined` | `corner_radius` | `4` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `variant: outlined`, state `hovered` | `border_color` | `on_surface` | The colour of its border: a colour or a gradient. |
| `variant: outlined`, state `focused` | `border_width` | `2` | The width of its border, in pixels. |
| `variant: outlined`, state `focused` | `border_color` | `primary` | The colour of its border: a colour or a gradient. |
| `variant: outlined`, state `error` | `border_color` | `error` | The colour of its border: a colour or a gradient. |

### `indicator` (Rect)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `height` | `1` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `background` | `on_surface_variant` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| state `hovered` | `background` | `on_surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| state `focused` | `height` | `2` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| state `focused` | `background` | `primary` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| state `error` | `background` | `error` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| state `focused` | `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| state `error` | `foreground` | `error` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `input` (TextInput)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

### `prefix` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `suffix` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `supporting` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| state `error` | `foreground` | `error` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `counter` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `leading_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `trailing_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `reveal_button` (Rect)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

### `reveal_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `error_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `error` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: TextField
    style: {background: tertiary}
```
