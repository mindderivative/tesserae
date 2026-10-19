# Chip_Stylesheet.yaml

The look of Chip (Material 3): 8 pixel corners, 8 pixels between parts, 16 pixels of padding (8 beside an icon or the close button). Assist, suggestion, filter and input chips are outlined in `outline_variant`; elevated ones are `surface_container_low` at level 1 with no outline; a selected filter or input chip is `secondary_container` with no outline.

The look of [`Chip`](../../components/chips.md) (in [Chips](../../components/chips.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Chip (Material 3): 8 pixel corners, 8 pixels between parts, 16 pixels of padding (8 beside an icon or the close button). Assist, suggestion,
# filter and input chips are outlined in `outline_variant`; elevated ones are `surface_container_low` at level 1 with no outline; a selected filter or input chip
# is `secondary_container` with no outline.
styles:
  - widget: Chip
    style:
      corner_radius: 8
      gap: 8
      padding: "{{ {'left': 8 if (avatar_text != '' or icon != '' or (variant == 'filter' and selected)) else 16, 'right': 8 if removable else 16, 'top': 0, 'bottom': 0} }}"
      transition: {background: 150}
      border_width: "{{ 0 if (elevated or (selected and variant in ('filter', 'input'))) else 1 }}"
      border_color: outline_variant
      background: "{{ 'secondary_container' if (selected and variant in ('filter', 'input')) else ('surface_container_low' if elevated else 'transparent') }}"
      elevation: "{{ 1 if (elevated and not (selected and variant in ('filter', 'input'))) else 0 }}"
  - {widget: Chip, part: label, style: {foreground: "{{ 'on_secondary_container' if (selected and variant in ('filter', 'input')) else ('on_surface_variant' if variant in ('filter', 'input') else 'on_surface') }}"}}
  - {widget: Chip, part: icon, style: {width: 18, height: 18, foreground: "{{ 'on_secondary_container' if (selected and variant in ('filter', 'input')) else ('primary' if variant in ('assist', 'suggestion') else 'on_surface_variant') }}"}}
  - widget: Chip
    part: avatar
    style: {width: 24, height: 24, corner_radius: full, background: primary_container, align_content: center}
  - {widget: Chip, part: avatar_text, style: {foreground: on_primary_container}}
  - widget: Chip
    part: close
    style: {width: 18, height: 18, corner_radius: 9, align_content: center}
  - {widget: Chip, part: close_icon, style: {width: 18, height: 18, foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
```

## How it reaches the view

Each rule names `widget: Chip` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Chip` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `corner_radius` | `8` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `gap` | `8` | Space between its children. |
| always | `padding` | `{{ {'left': 8 if (avatar_text != '' or icon != '' or (variant == 'filter' and selected)) else 16, 'right': 8 …` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `transition` | `{background: 150}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| always | `border_width` | `{{ 0 if (elevated or (selected and variant in ('filter', 'input'))) else 1 }}` | The width of its border, in pixels. |
| always | `border_color` | `outline_variant` | The colour of its border: a colour or a gradient. |
| always | `background` | `{{ 'secondary_container' if (selected and variant in ('filter', 'input')) else ('surface_container_low' if el…` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `elevation` | `{{ 1 if (elevated and not (selected and variant in ('filter', 'input'))) else 0 }}` | A shadow level, 0 to 5. |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'on_secondary_container' if (selected and variant in ('filter', 'input')) else ('on_surface_variant' if va…` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `18` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `18` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `foreground` | `{{ 'on_secondary_container' if (selected and variant in ('filter', 'input')) else ('primary' if variant in ('…` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `avatar` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `background` | `primary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `avatar_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_primary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `close` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `18` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `18` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `corner_radius` | `9` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `close_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `18` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `18` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Chip
    style: {background: tertiary}
```
