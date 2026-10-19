# NavigationDrawerItem_Stylesheet.yaml

The look of NavigationDrawerItem (Material 3): a pill (28 pixel corners) that is secondary_container when selected, 16 pixels in on the left and 24 on the right, the icon, label and badge in on_secondary_container when selected and on_surface_variant otherwise.

The look of [`NavigationDrawerItem`](../../components/navigation-drawer.md) (in [Navigation drawer](../../components/navigation-drawer.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of NavigationDrawerItem (Material 3): a pill (28 pixel corners) that is secondary_container when selected, 16 pixels in on the left and 24 on the right, the
# icon, label and badge in on_secondary_container when selected and on_surface_variant otherwise.
styles:
  - widget: NavigationDrawerItem
    style:
      corner_radius: 28
      padding: {left: 16, right: 24, top: 0, bottom: 0}
      gap: 12
      background: "{{ 'secondary_container' if selected else 'transparent' }}"
      transition: {background: 150}
  - {widget: NavigationDrawerItem, part: icon, style: {width: 24, height: 24, foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
  - {widget: NavigationDrawerItem, part: label, style: {foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
  - {widget: NavigationDrawerItem, part: badge, style: {foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
```

## How it reaches the view

Each rule names `widget: NavigationDrawerItem` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `NavigationDrawerItem` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `corner_radius` | `28` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `padding` | `{bottom: 0, left: 16, right: 24, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `12` | Space between its children. |
| always | `background` | `{{ 'secondary_container' if selected else 'transparent' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `transition` | `{background: 150}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `badge` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: NavigationDrawerItem
    style: {background: tertiary}
```
