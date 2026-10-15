# Button_Stylesheet.yaml

The look of Button (Material 3, with the Expressive sizes). Sizes set the height, the padding (24 each side, 16 on the side with an icon; a text button 12 and 12) and the gap; variants set the colours; the shape is a pill or a rounded square, and a toggle that is on, or a press, takes the other. A state layer and a ripple come from the node's interaction; a filled, tonal or elevated button lifts when hovered.

The look of [`Button`](../../components/buttons.md) (in [Buttons](../../components/buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Button (Material 3, with the Expressive sizes). Sizes set the height, the padding (24 each side, 16 on the side with an icon; a text button
# 12 and 12) and the gap; variants set the colours; the shape is a pill or a rounded square, and a toggle that is on, or a press, takes the other.
# A state layer and a ripple come from the node's interaction; a filled, tonal or elevated button lifts when hovered.
styles:
  - widget: Button
    style:
      height: 40
      transition: {corner_radius: 200, elevation: 200, background: 150}
  # sizes
  - {widget: Button, size: xs, style: {height: 32, gap: 4}}
  - {widget: Button, size: s, style: {height: 40, gap: 8}}
  - {widget: Button, size: m, style: {height: 56, gap: 8}}
  - {widget: Button, size: l, style: {height: 96, gap: 12}}
  - {widget: Button, size: xl, style: {height: 136, gap: 16}}
  - widget: Button
    style:
      padding: "{{ {'left': (({'xs': 12, 's': 16, 'm': 24, 'l': 48, 'xl': 64}[size]) if (icon != '' or loading) else ({'xs': 12, 's': 24, 'm': 24, 'l': 48, 'xl': 64}[size])) if variant != 'text' else 12, 'right': (({'xs': 12, 's': 16, 'm': 24, 'l': 48, 'xl': 64}[size]) if trailing_icon != '' else ({'xs': 12, 's': 24, 'm': 24, 'l': 48, 'xl': 64}[size])) if variant != 'text' else 12, 'top': 0, 'bottom': 0} }}"
  # shapes: a pill, or a rounded square; a toggle that is on (and a press) takes the other
  - widget: Button
    shape: round
    style: {corner_radius: full}
  - widget: Button
    shape: square
    style: {corner_radius: "{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}"}
  - widget: Button
    shape: round
    state: selected
    style: {corner_radius: "{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}"}
  - widget: Button
    shape: square
    state: selected
    style: {corner_radius: full}
  - widget: Button
    shape: round
    state: pressed
    style: {corner_radius: "{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}"}
  # variants
  - widget: Button
    variant: filled
    style: {background: "{{ 'primary' if (not toggle or selected) else 'surface_container_highest' }}"}
  - widget: Button
    variant: tonal
    style: {background: "{{ 'secondary_container' if (not toggle or not selected) else 'secondary' }}"}
  - widget: Button
    variant: elevated
    style: {background: "{{ 'surface_container_low' if (not toggle or not selected) else 'primary' }}", elevation: 1}
  - widget: Button
    variant: outlined
    style:
      background: "{{ 'transparent' if (not toggle or not selected) else 'inverse_surface' }}"
      border_width: "{{ 1 if (not toggle or not selected) else 0 }}"
      border_color: outline
  - widget: Button
    variant: text
    style: {background: transparent}
  # lifting
  - {widget: Button, variant: filled, state: hovered, style: {elevation: 1}}
  - {widget: Button, variant: tonal, state: hovered, style: {elevation: 1}}
  - {widget: Button, variant: elevated, state: hovered, style: {elevation: 2}}
  - {widget: Button, variant: elevated, state: pressed, style: {elevation: 1}}
  # content colours
  - widget: Button
    variant: filled
    part: label
    style: {foreground: "{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}"}
  - widget: Button
    variant: tonal
    part: label
    style: {foreground: "{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}"}
  - widget: Button
    variant: elevated
    part: label
    style: {foreground: "{{ 'primary' if (not toggle or not selected) else 'on_primary' }}"}
  - widget: Button
    variant: outlined
    part: label
    style: {foreground: "{{ 'primary' if not toggle else ('inverse_on_surface' if selected else 'on_surface_variant') }}"}
  - widget: Button
    variant: text
    part: label
    style: {foreground: primary}
  - {widget: Button, variant: filled, part: icon, style: {foreground: "{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}"}}
  - {widget: Button, variant: tonal, part: icon, style: {foreground: "{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}"}}
  - {widget: Button, variant: elevated, part: icon, style: {foreground: "{{ 'primary' if (not toggle or not selected) else 'on_primary' }}"}}
  - {widget: Button, variant: outlined, part: icon, style: {foreground: "{{ 'primary' if not toggle else ('inverse_on_surface' if selected else 'on_surface_variant') }}"}}
  - {widget: Button, variant: text, part: icon, style: {foreground: primary}}
  - {widget: Button, variant: filled, part: trailing, style: {foreground: "{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}"}}
  - {widget: Button, variant: tonal, part: trailing, style: {foreground: "{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}"}}
  - {widget: Button, variant: elevated, part: trailing, style: {foreground: "{{ 'primary' if (not toggle or not selected) else 'on_primary' }}"}}
  - {widget: Button, variant: outlined, part: trailing, style: {foreground: "{{ 'primary' if not toggle else ('inverse_on_surface' if selected else 'on_surface_variant') }}"}}
  - {widget: Button, variant: text, part: trailing, style: {foreground: primary}}
  # icon sizes
  - {widget: Button, part: icon, style: {width: "{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}", height: "{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}"}}
  - {widget: Button, part: trailing, style: {width: "{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}", height: "{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}"}}
```

## How it reaches the view

Each rule names `widget: Button` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Button` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `height` | `40` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `transition` | `{background: 150, corner_radius: 200, elevation: 200}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| `size: xs` | `height` | `32` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `size: xs` | `gap` | `4` | Space between its children. |
| `size: s` | `height` | `40` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `size: s` | `gap` | `8` | Space between its children. |
| `size: m` | `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `size: m` | `gap` | `8` | Space between its children. |
| `size: l` | `height` | `96` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `size: l` | `gap` | `12` | Space between its children. |
| `size: xl` | `height` | `136` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `size: xl` | `gap` | `16` | Space between its children. |
| always | `padding` | `{{ {'left': (({'xs': 12, 's': 16, 'm': 24, 'l': 48, 'xl': 64}[size]) if (icon != '' or loading) else ({'xs': …` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `shape: round` | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: square` | `corner_radius` | `{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: round`, state `selected` | `corner_radius` | `{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: square`, state `selected` | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `shape: round`, state `pressed` | `corner_radius` | `{{ {'xs': 12, 's': 12, 'm': 16, 'l': 28, 'xl': 28}[size] }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `variant: filled` | `background` | `{{ 'primary' if (not toggle or selected) else 'surface_container_highest' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: tonal` | `background` | `{{ 'secondary_container' if (not toggle or not selected) else 'secondary' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: elevated` | `background` | `{{ 'surface_container_low' if (not toggle or not selected) else 'primary' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: elevated` | `elevation` | `1` | A shadow level, 0 to 5. |
| `variant: outlined` | `background` | `{{ 'transparent' if (not toggle or not selected) else 'inverse_surface' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: outlined` | `border_width` | `{{ 1 if (not toggle or not selected) else 0 }}` | The width of its border, in pixels. |
| `variant: outlined` | `border_color` | `outline` | The colour of its border: a colour or a gradient. |
| `variant: text` | `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: filled`, state `hovered` | `elevation` | `1` | A shadow level, 0 to 5. |
| `variant: tonal`, state `hovered` | `elevation` | `1` | A shadow level, 0 to 5. |
| `variant: elevated`, state `hovered` | `elevation` | `2` | A shadow level, 0 to 5. |
| `variant: elevated`, state `pressed` | `elevation` | `1` | A shadow level, 0 to 5. |

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| `variant: filled` | `foreground` | `{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: tonal` | `foreground` | `{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: elevated` | `foreground` | `{{ 'primary' if (not toggle or not selected) else 'on_primary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: outlined` | `foreground` | `{{ 'primary' if not toggle else ('inverse_on_surface' if selected else 'on_surface_variant') }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: text` | `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| `variant: filled` | `foreground` | `{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: tonal` | `foreground` | `{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: elevated` | `foreground` | `{{ 'primary' if (not toggle or not selected) else 'on_primary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: outlined` | `foreground` | `{{ 'primary' if not toggle else ('inverse_on_surface' if selected else 'on_surface_variant') }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: text` | `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

### `trailing` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| `variant: filled` | `foreground` | `{{ 'on_primary' if (not toggle or selected) else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: tonal` | `foreground` | `{{ 'on_secondary_container' if (not toggle or not selected) else 'on_secondary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: elevated` | `foreground` | `{{ 'primary' if (not toggle or not selected) else 'on_primary' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: outlined` | `foreground` | `{{ 'primary' if not toggle else ('inverse_on_surface' if selected else 'on_surface_variant') }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `variant: text` | `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| always | `height` | `{{ {'xs': 20, 's': 18, 'm': 24, 'l': 32, 'xl': 40}[size] }}` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Button
    variant: filled
    style: {background: tertiary}
```
