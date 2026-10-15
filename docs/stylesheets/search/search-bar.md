# SearchBar_Stylesheet.yaml

The look of SearchBar (Material 3): a surface_container_high pill, 56 tall, at level 3; 4 pixels in from the edge, the icons 24 pixels in a 48 pixel button, the text in on_surface and the placeholder dimmed, the avatar a 30 pixel circle in primary_container.

The look of [`SearchBar`](../../components/search.md) (in [Search](../../components/search.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of SearchBar (Material 3): a surface_container_high pill, 56 tall, at level 3; 4 pixels in from the edge, the icons 24 pixels in a 48 pixel button, the text
# in on_surface and the placeholder dimmed, the avatar a 30 pixel circle in primary_container.
styles:
  - widget: SearchBar
    style:
      background: "{{ 'surface_container_high@72%' if frosted else 'surface_container_high' }}"
      backdrop_blur: "{{ 20 if frosted else 0 }}"
      corner_radius: full
      elevation: 3
      padding: {left: 4, right: 12, top: 0, bottom: 0}
      gap: 4
  - widget: SearchBar
    part: back
    style: {width: 48, height: 48, corner_radius: 24, align_content: center}
  - widget: SearchBar
    part: leading
    style: {width: 48, height: 48, corner_radius: 24, align_content: center}
  - widget: SearchBar
    part: clear
    style: {width: 48, height: 48, corner_radius: 24, align_content: center}
  - widget: SearchBar
    part: trailing
    style: {width: 48, height: 48, corner_radius: 24, align_content: center}
  - {widget: SearchBar, part: back_icon, style: {width: 24, height: 24, foreground: on_surface}}
  - {widget: SearchBar, part: leading_glyph, style: {width: 24, height: 24, foreground: on_surface}}
  - {widget: SearchBar, part: clear_icon, style: {width: 24, height: 24, foreground: on_surface_variant}}
  - {widget: SearchBar, part: trailing_glyph, style: {width: 24, height: 24, foreground: on_surface_variant}}
  - widget: SearchBar
    part: input
    style: {foreground: on_surface, background: transparent}
  - widget: SearchBar
    part: avatar
    style: {width: 30, height: 30, corner_radius: full, background: primary_container, align_content: center}
  - {widget: SearchBar, part: avatar_text, style: {foreground: on_primary_container}}
```

## How it reaches the view

Each rule names `widget: SearchBar` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `SearchBar` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'surface_container_high@72%' if frosted else 'surface_container_high' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `backdrop_blur` | `{{ 20 if frosted else 0 }}` | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| always | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `elevation` | `3` | A shadow level, 0 to 5. |
| always | `padding` | `{bottom: 0, left: 4, right: 12, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `4` | Space between its children. |

### `back` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `leading` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `clear` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `trailing` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `back_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `leading_glyph` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `clear_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `trailing_glyph` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `input` (TextInput)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

### `avatar` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `30` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `30` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `background` | `primary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `avatar_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_primary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: SearchBar
    style: {background: tertiary}
```
