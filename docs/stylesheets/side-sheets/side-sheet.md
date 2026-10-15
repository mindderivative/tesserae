# SideSheet_Stylesheet.yaml

The look of the standard side sheet: a `surface` column.

The look of [`SideSheet`](../../components/side-sheets.md) (in [Side sheets](../../components/side-sheets.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of the standard side sheet: a `surface` column.
styles:
  - widget: SideSheet
    style:
      background: surface
```

## How it reaches the view

Each rule names `widget: SideSheet` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `SideSheet` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: SideSheet
    style: {background: tertiary}
```
