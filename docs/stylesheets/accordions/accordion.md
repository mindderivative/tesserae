# Accordion_Stylesheet.yaml

The look of Accordion: the header's title in on_surface and its chevron in on_surface_variant, 16 pixels in from each side; the content 16 pixels in and 16 below.

The look of [`Accordion`](../../components/accordions.md) (in [Accordions](../../components/accordions.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Accordion: the header's title in on_surface and its chevron in on_surface_variant, 16 pixels in from each side; the content 16 pixels in and 16 below.
styles:
  - widget: Accordion
    part: header
    style: {padding: {left: 16, right: 16, top: 0, bottom: 0}, gap: 12}
  - {widget: Accordion, part: title, style: {foreground: on_surface}}
  - {widget: Accordion, part: chevron, style: {width: 24, height: 24, foreground: on_surface_variant}}
  - widget: Accordion
    part: content
    style: {padding: {left: 16, right: 16, top: 0, bottom: 16}}
```

## How it reaches the view

Each rule names `widget: Accordion` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `header` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 0, left: 16, right: 16, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `12` | Space between its children. |

### `title` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `chevron` (Icon)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `width` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `24` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `content` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 16, left: 16, right: 16, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Accordion
    part: title
    style: {foreground: tertiary}
```
