# Snackbar_Stylesheet.yaml

The look of Snackbar (Material 3): inverse_surface at level 3 with 4 pixel corners, 16 pixels in from the edge on the left and 8 on the right of the buttons; the message in inverse_on_surface, the action in inverse_primary.

The look of [`Snackbar`](../../components/snackbars.md) (in [Snackbars](../../components/snackbars.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Snackbar (Material 3): inverse_surface at level 3 with 4 pixel corners, 16 pixels in from the edge on the left and 8 on the right of the buttons;
# the message in inverse_on_surface, the action in inverse_primary.
styles:
  - widget: Snackbar
    style:
      background: inverse_surface
      corner_radius: 4
      elevation: 3
  - widget: Snackbar
    part: bar
    style: {padding: {left: 16, right: 8, top: 0, bottom: 0}}
  - {widget: Snackbar, part: message, style: {foreground: inverse_on_surface, flex: expand_horizontal, padding: {left: 0, right: 0, top: 14, bottom: 14}}}
  - widget: Snackbar
    part: action
    style: {padding: {left: 8, right: 8, top: 8, bottom: 8}, corner_radius: 16}
  - {widget: Snackbar, part: action_text, style: {foreground: inverse_primary}}
  - widget: Snackbar
    part: close
    style: {width: 40, height: 40, corner_radius: 20, align_content: center}
  - {widget: Snackbar, part: close_icon, style: {foreground: inverse_on_surface, width: 24, height: 24}}
```

## How it reaches the view

Each rule names `widget: Snackbar` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Snackbar` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `inverse_surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `corner_radius` | `4` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `elevation` | `3` | A shadow level, 0 to 5. |

### `bar` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 0, left: 16, right: 8, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `message` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `inverse_on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `flex` | `expand_horizontal` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| always | `padding` | `{bottom: 14, left: 0, right: 0, top: 14}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `action` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 8, left: 8, right: 8, top: 8}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `corner_radius` | `16` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |

### `action_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `inverse_primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `close` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `40` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `40` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `corner_radius` | `20` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `close_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `inverse_on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Snackbar
    style: {background: tertiary}
```
