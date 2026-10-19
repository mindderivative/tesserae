# IconButton_Stylesheet.yaml

The look of IconButton (Material 3, with the Expressive sizes, widths and shapes). The icon is 20, 24, 24, 32 or 40 pixels for the five sizes. A toggle that is on takes the selected colours and the other shape; a press squares a round button off.

The look of [`IconButton`](../../components/icon-buttons.md) (in [Icon buttons](../../components/icon-buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of IconButton (Material 3, with the Expressive sizes, widths and shapes). The icon is 20, 24, 24, 32 or 40 pixels for the five sizes. A toggle
# that is on takes the selected colours and the other shape; a press squares a round button off.
styles:
  - widget: IconButton
    style:
      height: 40
      width: 40
      transition: {corner_radius: 200, background: 150}
  - {widget: IconButton, size: xs, style: {height: 32}}
  - {widget: IconButton, size: s, style: {height: 40}}
  - {widget: IconButton, size: m, style: {height: 56}}
  - {widget: IconButton, size: l, style: {height: 96}}
  - {widget: IconButton, size: xl, style: {height: 136}}
  - widget: IconButton
    style:
      width: "{{ {'xs': {'narrow': 28, 'default': 32, 'wide': 40}, 's': {'narrow': 32, 'default': 40, 'wide': 52}, 'm': {'narrow': 48, 'default': 56, 'wide': 72}, 'l': {'narrow': 64, 'default': 96, 'wide': 128}, 'xl': {'narrow': 104, 'default': 136, 'wide': 184}}[size][width_kind] }}"
  # shapes
  - {widget: IconButton, shape: round, style: {corner_radius: full}}
  - {widget: IconButton, shape: square, style: {corner_radius: "{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}"}}
  - {widget: IconButton, shape: round, state: selected, style: {corner_radius: "{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}"}}
  - {widget: IconButton, shape: square, state: selected, style: {corner_radius: full}}
  - {widget: IconButton, shape: round, state: pressed, style: {corner_radius: "{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}"}}
  # variants
  - {widget: IconButton, variant: standard, style: {background: transparent}}
  - {widget: IconButton, variant: filled, style: {background: "{{ 'primary' if (not toggle or selected) else 'surface_container_highest' }}"}}
  - {widget: IconButton, variant: tonal, style: {background: "{{ 'secondary_container' if (not toggle or not selected) else 'secondary' }}"}}
  - widget: IconButton
    variant: outlined
    style:
      background: "{{ 'transparent' if (not toggle or not selected) else 'inverse_surface' }}"
      border_width: "{{ 1 if (not toggle or not selected) else 0 }}"
      border_color: outline
  # the icon
  - {widget: IconButton, part: icon, style: {transition: {icon: 200}}}
  - {widget: IconButton, part: icon, style: {width: "{{ {'xs': 20, 's': 24, 'm': 24, 'l': 32, 'xl': 40}[size] }}", height: "{{ {'xs': 20, 's': 24, 'm': 24, 'l': 32, 'xl': 40}[size] }}"}}
  - {widget: IconButton, variant: standard, part: icon, style: {foreground: "{{ tint if tint != '' else ('primary' if (toggle and selected) else 'on_surface_variant') }}"}}
  - {widget: IconButton, variant: filled, part: icon, style: {foreground: "{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}"}}
  - {widget: IconButton, variant: tonal, part: icon, style: {foreground: "{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}"}}
  - {widget: IconButton, variant: outlined, part: icon, style: {foreground: "{{ 'on_surface_variant' if (not toggle or not selected) else 'inverse_on_surface' }}"}}
```

## How it reaches the view

Each rule names `widget: IconButton` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `IconButton` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `height` | `40` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `width` | `40` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `transition` | `{background: 150, corner_radius: 200}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| `size: xs` | `height` | `32` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: s` | `height` | `40` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: m` | `height` | `56` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: l` | `height` | `96` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `size: xl` | `height` | `136` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `width` | `{{ {'xs': {'narrow': 28, 'default': 32, 'wide': 40}, 's': {'narrow': 32, 'default': 40, 'wide': 52}, 'm': {'n…` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `shape: round` | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: square` | `corner_radius` | `{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: round`, state `selected` | `corner_radius` | `{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: square`, state `selected` | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: round`, state `pressed` | `corner_radius` | `{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `variant: standard` | `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: filled` | `background` | `{{ 'primary' if (not toggle or selected) else 'surface_container_highest' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: tonal` | `background` | `{{ 'secondary_container' if (not toggle or not selected) else 'secondary' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: outlined` | `background` | `{{ 'transparent' if (not toggle or not selected) else 'inverse_surface' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: outlined` | `border_width` | `{{ 1 if (not toggle or not selected) else 0 }}` | The width of its border, in pixels. |
| `variant: outlined` | `border_color` | `outline` | The colour of its border: a colour or a gradient. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `transition` | `{icon: 200}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| always | `width` | `{{ {'xs': 20, 's': 24, 'm': 24, 'l': 32, 'xl': 40}[size] }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `{{ {'xs': 20, 's': 24, 'm': 24, 'l': 32, 'xl': 40}[size] }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `variant: standard` | `foreground` | `{{ tint if tint != '' else ('primary' if (toggle and selected) else 'on_surface_variant') }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: filled` | `foreground` | `{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: tonal` | `foreground` | `{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: outlined` | `foreground` | `{{ 'on_surface_variant' if (not toggle or not selected) else 'inverse_on_surface' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: IconButton
    variant: standard
    style: {background: tertiary}
```
