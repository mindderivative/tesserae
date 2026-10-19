# Badge_Stylesheet.yaml

The look of Badge (Material 3): an error-coloured dot or pill, with the label in on_error. Anchored, the mark is placed over the host's top right corner: a dot overlaps it by 4, a pill starts 12 in from the corner and sits 4 above it.

The look of [`Badge`](../../components/badges.md) (in [Badges](../../components/badges.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Badge (Material 3): an error-coloured dot or pill, with the label in on_error. Anchored, the mark is placed over the host's top right
# corner: a dot overlaps it by 4, a pill starts 12 in from the corner and sits 4 above it.
styles:
  - widget: Badge
    part: mark
    style:
      background: error
      width: "{{ 6 if value == '' else (16 if len(str(value)) < 2 else 8 + 6 * len(str(value))) }}"
      height: "{{ 6 if value == '' else 16 }}"
      corner_radius: "{{ 3 if value == '' else 8 }}"
      align_content: center
      position: "{{ 'absolute' if anchored else 'relative' }}"
      x: "{{ '100%' if anchored else 'auto' }}"
      y: "{{ (0 if value == '' else -4) if anchored else 'auto' }}"
      translate_x: "{{ (-4 if value == '' else -12) if anchored else 0 }}"
  - widget: Badge
    part: label
    style: {foreground: on_error}
```

## How it reaches the view

Each rule names `widget: Badge` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `mark` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `error` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `width` | `{{ 6 if value == '' else (16 if len(str(value)) < 2 else 8 + 6 * len(str(value))) }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `{{ 6 if value == '' else 16 }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `corner_radius` | `{{ 3 if value == '' else 8 }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| always | `position` | `{{ 'absolute' if anchored else 'relative' }}` | `absolute` takes it out of the flow and places it at `x` and `y`. |
| always | `x` | `{{ '100%' if anchored else 'auto' }}` | Where an `absolute` node sits from the left; the same as `left` (say one of them). |
| always | `y` | `{{ (0 if value == '' else -4) if anchored else 'auto' }}` | Where an `absolute` node sits from the top; the same as `top` (say one of them). |
| always | `translate_x` | `{{ (-4 if value == '' else -12) if anchored else 0 }}` | Draws the node this many pixels to the right of where it is laid out. |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_error` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Badge
    part: mark
    style: {background: tertiary}
```
