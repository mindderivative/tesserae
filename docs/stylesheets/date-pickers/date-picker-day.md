# DatePickerDay_Stylesheet.yaml

The look of DatePickerDay: the selected day is a primary circle with on_primary text; today a 1 pixel primary outline with primary text; a day outside the month is on_surface_variant; the rest on_surface.

The look of [`DatePickerDay`](../../components/date-pickers.md) (in [Date picker](../../components/date-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of DatePickerDay: the selected day is a primary circle with on_primary text; today a 1 pixel primary outline with primary text; a day outside the month is
# on_surface_variant; the rest on_surface.
styles:
  - widget: DatePickerDay
    part: circle
    style:
      background: "{{ 'primary' if selected else 'transparent' }}"
      border_width: "{{ 1 if (today and not selected) else 0 }}"
      border_color: primary
  - widget: DatePickerDay
    part: number
    style: {foreground: "{{ 'on_primary' if selected else ('primary' if today else ('on_surface_variant' if outside else 'on_surface')) }}"}
```

## How it reaches the view

Each rule names `widget: DatePickerDay` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `circle` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'primary' if selected else 'transparent' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `border_width` | `{{ 1 if (today and not selected) else 0 }}` | The width of its border, in pixels. |
| always | `border_color` | `primary` | The colour of its border: a colour or a gradient. |

### `number` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `{{ 'on_primary' if selected else ('primary' if today else ('on_surface_variant' if outside else 'on_surface')…` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: DatePickerDay
    part: circle
    style: {background: tertiary}
```
