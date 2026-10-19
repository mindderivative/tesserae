# SpinBoxField_Stylesheet.yaml

The look of SpinBoxField: the label in on_surface_variant, the supporting text in on_surface_variant and an error in error; 16 pixels in from the edge, as a text field's are.

The look of [`SpinBoxField`](../../components/spin-boxes.md) (in [Spin box](../../components/spin-boxes.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of SpinBoxField: the label in on_surface_variant, the supporting text in on_surface_variant and an error in error; 16 pixels in from the edge, as a
# text field's are.
styles:
  - {widget: SpinBoxField, part: label, style: {foreground: "{{ 'error' if error != '' else 'on_surface_variant' }}", margin: {left: 4}}}
  - {widget: SpinBoxField, part: help, style: {foreground: "{{ 'error' if error != '' else 'on_surface_variant' }}", margin: {left: 4}}}
```

## How it reaches the view

Each rule names `widget: SpinBoxField` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `label` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'error' if error != '' else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `margin` | `{left: 4}` | Space outside it: one number, or `{left, right, top, bottom}`. |

### `help` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'error' if error != '' else 'on_surface_variant' }}` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `margin` | `{left: 4}` | Space outside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: SpinBoxField
    part: label
    style: {foreground: tertiary}
```
