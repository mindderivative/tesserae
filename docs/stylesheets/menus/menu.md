# Menu_Stylesheet.yaml

The look of Menu (Material 3): a surface_container surface with 4 pixel corners at level 2, 8 pixels above and below its items; headings in on_surface_variant.

The look of [`Menu`](../../components/menus.md) (in [Menus](../../components/menus.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Menu (Material 3): a surface_container surface with 4 pixel corners at level 2, 8 pixels above and below its items; headings in on_surface_variant.
styles:
  - widget: Menu
    part: surface
    style:
      background: "{{ 'surface_container@72%' if frosted else 'surface_container' }}"
      backdrop_blur: "{{ 20 if frosted else 0 }}"
      corner_radius: 4
      elevation: 2
      padding: {left: 0, right: 0, top: 8, bottom: 8}
  - {widget: Menu, part: heading, style: {foreground: on_surface_variant, padding: {left: 12, right: 12, top: 8, bottom: 8}}}
```

## How it reaches the view

Each rule names `widget: Menu` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `surface` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'surface_container@72%' if frosted else 'surface_container' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `backdrop_blur` | `{{ 20 if frosted else 0 }}` | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| always | `corner_radius` | `4` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `elevation` | `2` | A shadow level, 0 to 5. |
| always | `padding` | `{bottom: 8, left: 0, right: 0, top: 8}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `heading` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `padding` | `{bottom: 8, left: 12, right: 12, top: 8}` | Space inside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Menu
    part: surface
    style: {background: tertiary}
```
