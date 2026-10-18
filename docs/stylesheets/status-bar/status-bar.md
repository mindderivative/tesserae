# StatusBar_Stylesheet.yaml

The look of StatusBar: a thin surface_container strip with label_small text in on_surface_variant; an item that can be pressed has a state layer.

The look of [`StatusBar`](../../components/status-bar.md) (in [Status bar](../../components/status-bar.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of StatusBar: a thin surface_container strip with label_small text in on_surface_variant; an item that can be pressed has a state layer.
styles:
  - widget: StatusBar
    style:
      background: surface_container
      padding: {left: 8, right: 8, top: 0, bottom: 0}
  - {widget: StatusBar, part: text, style: {foreground: on_surface_variant}}
  - {widget: StatusBar, part: note_text, style: {foreground: on_surface_variant}}
  - {widget: StatusBar, part: icon, style: {foreground: on_surface_variant, width: 16, height: 16}}
  - {widget: StatusBar, part: note_icon, style: {foreground: on_surface_variant, width: 16, height: 16}}
```

## How it reaches the view

Each rule names `widget: StatusBar` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `StatusBar` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `surface_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `padding` | `{bottom: 0, left: 8, right: 8, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `note_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `16` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `16` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |

### `note_icon` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `width` | `16` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `16` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: StatusBar
    style: {background: tertiary}
```
