# TimePicker_Stylesheet.yaml

The look of TimePicker (Material 3): a surface_container_high dialog with 28 pixel corners and 24 pixels of padding; the heading in on_surface_variant, the time in on_surface.

The look of [`TimePicker`](../../components/time-pickers.md) (in [Time picker](../../components/time-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of TimePicker (Material 3): a surface_container_high dialog with 28 pixel corners and 24 pixels of padding; the heading in on_surface_variant,
# the time in on_surface.
styles:
  - widget: TimePicker
    part: panel
    style:
      background: surface_container_high
      corner_radius: 28
      padding: 24
      elevation: 3
  - {widget: TimePicker, part: heading, style: {foreground: on_surface_variant}}
  - {widget: TimePicker, part: colon, style: {foreground: on_surface}}
```

## How it reaches the view

Each rule names `widget: TimePicker` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `panel` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `surface_container_high` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `corner_radius` | `28` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `padding` | `24` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `elevation` | `3` | A shadow level, 0 to 5. |

### `heading` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `colon` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: TimePicker
    part: panel
    style: {background: tertiary}
```
