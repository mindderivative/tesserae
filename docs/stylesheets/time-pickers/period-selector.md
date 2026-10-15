# PeriodSelector_Stylesheet.yaml

The look of PeriodSelector: an outlined frame with 8 pixel corners. The halves' colours are in the view, because a rule cannot see the loop variable that says which half is which.

The look of [`PeriodSelector`](../../components/time-pickers.md) (in [Time picker](../../components/time-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of PeriodSelector: an outlined frame with 8 pixel corners. The halves' colours are in the view, because a rule cannot see the loop variable that
# says which half is which.
styles:
  - widget: PeriodSelector
    style: {corner_radius: 8, border_width: 1, border_color: outline}
```

## How it reaches the view

Each rule names `widget: PeriodSelector` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `PeriodSelector` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `corner_radius` | `8` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `border_width` | `1` | The width of its border, in pixels. |
| always | `border_color` | `outline` | The colour of its border: a colour or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: PeriodSelector
    style: {corner_radius: tertiary}
```
