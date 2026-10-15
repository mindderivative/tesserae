# Pagination_Stylesheet.yaml

The look of Pagination: the ellipsis and the "3 of 12" in on_surface_variant and on_surface.

The look of [`Pagination`](../../components/pagination.md) (in [Pagination](../../components/pagination.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Pagination: the ellipsis and the "3 of 12" in on_surface_variant and on_surface.
styles:
  - {widget: Pagination, part: gap, style: {foreground: on_surface_variant}}
  - {widget: Pagination, part: summary, style: {foreground: on_surface}}
```

## How it reaches the view

Each rule names `widget: Pagination` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `gap` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `summary` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Pagination
    part: gap
    style: {foreground: tertiary}
```
