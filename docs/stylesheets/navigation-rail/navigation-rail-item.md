# NavigationRailItem_Stylesheet.yaml

The look of NavigationRailItem (Material 3): a 56 by 32 pill that is secondary_container when selected, with a 24 pixel icon in on_secondary_container (on_surface_variant otherwise) and the label in on_surface (on_surface_variant otherwise). In an expanded rail the pill is 56 high and as wide as the item, with the label inside it.

The look of [`NavigationRailItem`](../../components/navigation-rail.md) (in [Navigation rail](../../components/navigation-rail.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of NavigationRailItem (Material 3): a 56 by 32 pill that is secondary_container when selected, with a 24 pixel icon in on_secondary_container
# (on_surface_variant otherwise) and the label in on_surface (on_surface_variant otherwise). In an expanded rail the pill is 56 high and as wide as the
# item, with the label inside it.
styles:
  - widget: NavigationRailItem
    style:
      corner_radius: 16
      transition: {background: 150}
  - widget: NavigationRailItem
    part: pill
    style:
      width: "{{ 'auto' if expanded else 56 }}"
      height: "{{ 56 if expanded else 32 }}"
      corner_radius: "{{ 28 if expanded else 16 }}"
      padding: "{{ {'left': 16, 'right': 24, 'top': 0, 'bottom': 0} if expanded else 0 }}"
      background: "{{ 'secondary_container' if selected else 'transparent' }}"
      transition: {background: 150}
  - {widget: NavigationRailItem, part: icon, style: {width: 24, height: 24, foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
  - {widget: NavigationRailItem, part: badged_icon, style: {width: 24, height: 24, foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
  - {widget: NavigationRailItem, part: label, style: {foreground: "{{ 'on_surface' if selected else 'on_surface_variant' }}"}}
  - {widget: NavigationRailItem, part: inline_label, style: {foreground: "{{ 'on_secondary_container' if selected else 'on_surface_variant' }}"}}
```

## How it reaches the view

Each rule names `widget: NavigationRailItem` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `NavigationRailItem` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `corner_radius` | `16` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `transition` | `{background: 150}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |

### `pill` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `{{ 'auto' if expanded else 56 }}` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `{{ 56 if expanded else 32 }}` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `corner_radius` | `{{ 28 if expanded else 16 }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `padding` | `{{ {'left': 16, 'right': 24, 'top': 0, 'bottom': 0} if expanded else 0 }}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `background` | `{{ 'secondary_container' if selected else 'transparent' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `transition` | `{background: 150}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `badged_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'on_surface' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `inline_label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'on_secondary_container' if selected else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: NavigationRailItem
    part: pill
    style: {background: tertiary}
```
