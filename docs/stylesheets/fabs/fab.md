# Fab_Stylesheet.yaml

The look of Fab (Material 3): a container at elevation level 3 that lifts to 4 when hovered and settles back when pressed. The container colour is the variant's, the icon and label its "on" colour. The extended form (with a label that shows) is 56 tall with 16 pixels of padding before the icon and 20 after the label.

The look of [`Fab`](../../components/fabs.md) (in [Floating action buttons](../../components/fabs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Fab (Material 3): a container at elevation level 3 that lifts to 4 when hovered and settles back when pressed. The container colour is the
# variant's, the icon and label its "on" colour. The extended form (with a label that shows) is 56 tall with 16 pixels of padding before the icon and 20
# after the label.
styles:
  - widget: Fab
    style:
      elevation: 3
      transition: {elevation: 200, corner_radius: 200}
      height: 56
      width: auto
      corner_radius: 16
  - {widget: Fab, size: small, style: {height: 40, corner_radius: 12}}
  - {widget: Fab, size: medium, style: {height: 56, corner_radius: 16}}
  - {widget: Fab, size: large, style: {height: 96, corner_radius: 28}}
  # the shape: a square one for an icon alone, otherwise as wide as it needs
  - widget: Fab
    style:
      width: "{{ {'small': 40, 'medium': 56, 'large': 96}[size] if (label == '' or collapsed) else 'auto' }}"
      height: "{{ 56 if (label != '' and not collapsed) else {'small': 40, 'medium': 56, 'large': 96}[size] }}"
      padding: "{{ {'left': 16, 'right': 20, 'top': 0, 'bottom': 0} if (label != '' and not collapsed) else 0 }}"
      gap: 8
  - {widget: Fab, state: hovered, style: {elevation: 4}}
  - {widget: Fab, state: pressed, style: {elevation: 3}}
  # colours
  - {widget: Fab, variant: primary, style: {background: primary_container}}
  - {widget: Fab, variant: secondary, style: {background: secondary_container}}
  - {widget: Fab, variant: tertiary, style: {background: tertiary_container}}
  - {widget: Fab, variant: surface, style: {background: surface_container_high}}
  - {widget: Fab, variant: primary, part: icon, style: {foreground: on_primary_container}}
  - {widget: Fab, variant: secondary, part: icon, style: {foreground: on_secondary_container}}
  - {widget: Fab, variant: tertiary, part: icon, style: {foreground: on_tertiary_container}}
  - {widget: Fab, variant: surface, part: icon, style: {foreground: primary}}
  - {widget: Fab, variant: primary, part: label, style: {foreground: on_primary_container}}
  - {widget: Fab, variant: secondary, part: label, style: {foreground: on_secondary_container}}
  - {widget: Fab, variant: tertiary, part: label, style: {foreground: on_tertiary_container}}
  - {widget: Fab, variant: surface, part: label, style: {foreground: primary}}
  # icon sizes
  - {widget: Fab, part: icon, style: {width: "{{ 36 if size == 'large' else 24 }}", height: "{{ 36 if size == 'large' else 24 }}"}}
```

## How it reaches the view

Each rule names `widget: Fab` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Fab` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `elevation` | `3` | A shadow level, 0 to 5. |
| always | `transition` | `{corner_radius: 200, elevation: 200}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| always | `height` | `56` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `width` | `auto` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `corner_radius` | `16` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `size: small` | `height` | `40` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: small` | `corner_radius` | `12` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `size: medium` | `height` | `56` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: medium` | `corner_radius` | `16` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `size: large` | `height` | `96` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: large` | `corner_radius` | `28` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `width` | `{{ {'small': 40, 'medium': 56, 'large': 96}[size] if (label == '' or collapsed) else 'auto' }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `{{ 56 if (label != '' and not collapsed) else {'small': 40, 'medium': 56, 'large': 96}[size] }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `padding` | `{{ {'left': 16, 'right': 20, 'top': 0, 'bottom': 0} if (label != '' and not collapsed) else 0 }}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `8` | Space between its children. |
| state `hovered` | `elevation` | `4` | A shadow level, 0 to 5. |
| state `pressed` | `elevation` | `3` | A shadow level, 0 to 5. |
| `variant: primary` | `background` | `primary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: secondary` | `background` | `secondary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: tertiary` | `background` | `tertiary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: surface` | `background` | `surface_container_high` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| `variant: primary` | `foreground` | `on_primary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: secondary` | `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: tertiary` | `foreground` | `on_tertiary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: surface` | `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `{{ 36 if size == 'large' else 24 }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `{{ 36 if size == 'large' else 24 }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| `variant: primary` | `foreground` | `on_primary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: secondary` | `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: tertiary` | `foreground` | `on_tertiary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: surface` | `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Fab
    variant: primary
    style: {background: tertiary}
```
