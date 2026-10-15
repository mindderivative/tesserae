# SearchView_Stylesheet.yaml

The look of SearchView (Material 3): a surface_container_high panel with 28 pixel corners, 8 pixels above and below the rows.

The look of [`SearchView`](../../components/search.md) (in [Search](../../components/search.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of SearchView (Material 3): a surface_container_high panel with 28 pixel corners, 8 pixels above and below the rows.
styles:
  - widget: SearchView
    part: panel
    style:
      background: "{{ 'surface_container_high@72%' if frosted else 'surface_container_high' }}"
      backdrop_blur: "{{ 20 if frosted else 0 }}"
      corner_radius: 28
      padding: {left: 0, right: 0, top: 8, bottom: 8}
  - {widget: SearchView, part: none, style: {foreground: on_surface_variant, padding: {left: 16, right: 16, top: 12, bottom: 12}}}
  - {widget: SearchView, part: count, style: {foreground: on_surface_variant}}
```

## How it reaches the view

Each rule names `widget: SearchView` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `panel` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'surface_container_high@72%' if frosted else 'surface_container_high' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `backdrop_blur` | `{{ 20 if frosted else 0 }}` | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| always | `corner_radius` | `28` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `padding` | `{bottom: 8, left: 0, right: 0, top: 8}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `none` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `padding` | `{bottom: 12, left: 16, right: 16, top: 12}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `count` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: SearchView
    part: panel
    style: {background: tertiary}
```
