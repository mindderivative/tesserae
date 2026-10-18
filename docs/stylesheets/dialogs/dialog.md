# Dialog_Stylesheet.yaml

The look of Dialog (Material 3): a raised panel with 28 pixel corners, 24 pixels of padding, an icon in `secondary`, the supporting text in `on_surface_variant`. The scrim is the modal Overlay's.

The look of [`Dialog`](../../components/dialogs.md) (in [Dialogs](../../components/dialogs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Dialog (Material 3): a raised panel with 28 pixel corners, 24 pixels of padding, an icon in `secondary`, the supporting text in
# `on_surface_variant`. The scrim is the modal Overlay's.
styles:
  - widget: Dialog
    part: panel
    style:
      background: "{{ 'surface' if fullscreen else 'surface_container_high' }}"
      corner_radius: "{{ 0 if fullscreen else 28 }}"
      padding: "{{ 0 if fullscreen else 24 }}"
      gap: "{{ 0 if fullscreen else 16 }}"
      elevation: "{{ 0 if fullscreen else 3 }}"
  - {widget: Dialog, part: icon, style: {foreground: secondary, width: 24, height: 24}}
  - {widget: Dialog, part: headline, style: {foreground: on_surface}}
  - {widget: Dialog, part: body, style: {foreground: on_surface_variant}}
  - {widget: Dialog, part: bar, style: {padding: {left: 4, right: 16, top: 0, bottom: 0}, gap: 8}}
  - {widget: Dialog, part: bar_title, style: {foreground: on_surface}}
  - {widget: Dialog, part: content, style: {padding: "{{ {'left': 24, 'right': 24, 'top': 16, 'bottom': 16} if fullscreen else 0 }}"}}
```

## How it reaches the view

Each rule names `widget: Dialog` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `panel` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'surface' if fullscreen else 'surface_container_high' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `corner_radius` | `{{ 0 if fullscreen else 28 }}` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `padding` | `{{ 0 if fullscreen else 24 }}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `{{ 0 if fullscreen else 16 }}` | Space between its children. |
| always | `elevation` | `{{ 0 if fullscreen else 3 }}` | A shadow level, 0 to 5. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `secondary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |

### `headline` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `body` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `bar` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 0, left: 4, right: 16, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `8` | Space between its children. |

### `bar_title` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `content` (ScrollView)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{{ {'left': 24, 'right': 24, 'top': 16, 'bottom': 16} if fullscreen else 0 }}` | Space inside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Dialog
    part: panel
    style: {background: tertiary}
```
