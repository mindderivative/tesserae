# ListItem_Stylesheet.yaml

The look of ListItem (Material 3): 16 pixels of padding each side, 16 between the parts; the headline in on_surface, the supporting text and the small text in on_surface_variant; a selected item is secondary_container.

The look of [`ListItem`](../../components/lists.md) (in [Lists](../../components/lists.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of ListItem (Material 3): 16 pixels of padding each side, 16 between the parts; the headline in on_surface, the supporting text and the
# small text in on_surface_variant; a selected item is secondary_container.
styles:
  - widget: ListItem
    style:
      padding: {left: 16, right: 16, top: 8, bottom: 8}
      gap: 16
      background: "{{ 'secondary_container' if selected else 'transparent' }}"
  - {widget: ListItem, part: headline, style: {foreground: on_surface}}
  - {widget: ListItem, part: supporting, style: {foreground: on_surface_variant}}
  - {widget: ListItem, part: overline, style: {foreground: on_surface_variant}}
  - {widget: ListItem, part: trailing_text, style: {foreground: on_surface_variant}}
  - {widget: ListItem, part: leading_icon, style: {foreground: on_surface_variant, width: 24, height: 24}}
  - {widget: ListItem, part: trailing_icon, style: {foreground: on_surface_variant, width: 24, height: 24}}
  - widget: ListItem
    part: avatar
    style: {width: 40, height: 40, corner_radius: full, background: primary_container, align_content: center}
  - {widget: ListItem, part: avatar_text, style: {foreground: on_primary_container}}
  - {widget: ListItem, part: picture, style: {width: 56, height: 56, corner_radius: 4}}
```

## How it reaches the view

Each rule names `widget: ListItem` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `ListItem` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 8, left: 16, right: 16, top: 8}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `16` | Space between its children. |
| always | `background` | `{{ 'secondary_container' if selected else 'transparent' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

### `headline` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `supporting` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `overline` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `trailing_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `leading_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

### `trailing_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

### `avatar` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `40` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `40` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `background` | `primary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `avatar_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_primary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `picture` (Image)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `4` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: ListItem
    style: {background: tertiary}
```
