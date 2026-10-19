# SideSheetModal_Stylesheet.yaml

The look of the modal side sheet: surface_container_low at level 1, with 16 pixel corners on the side that opens onto the content.

The look of [`SideSheetModal`](../../components/side-sheets.md) (in [Side sheets](../../components/side-sheets.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of the modal side sheet: surface_container_low at level 1, with 16 pixel corners on the side that opens onto the content.
styles:
  - widget: SideSheetModal
    part: sheet
    style:
      background: surface_container_low
      elevation: 1
      corner_radius: "{{ {'top_left': 16, 'bottom_left': 16, 'top_right': 0, 'bottom_right': 0} if side == 'end' else {'top_right': 16, 'bottom_right': 16, 'top_left': 0, 'bottom_left': 0} }}"
```

## How it reaches the view

Each rule names `widget: SideSheetModal` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `sheet` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `surface_container_low` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `elevation` | `1` | A shadow level, 0 to 5. |
| always | `corner_radius` | `{{ {'top_left': 16, 'bottom_left': 16, 'top_right': 0, 'bottom_right': 0} if side == 'end' else {'top_right':…` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: SideSheetModal
    part: sheet
    style: {background: tertiary}
```
