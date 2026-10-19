# TimeInput_Stylesheet.yaml

The look of TimeInput: the colon in on_surface, centred on the fields.

The look of [`TimeInput`](../../components/time-input.md) (in [Time input](../../components/time-input.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of TimeInput: the colon in on_surface, centred on the fields.
styles:
  - {widget: TimeInput, part: colon, style: {foreground: on_surface}}
```

## How it reaches the view

Each rule names `widget: TimeInput` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `colon` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: TimeInput
    part: colon
    style: {foreground: tertiary}
```
