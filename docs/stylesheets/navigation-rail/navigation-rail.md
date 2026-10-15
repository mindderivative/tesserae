# NavigationRail_Stylesheet.yaml

The look of NavigationRail (Material 3): a surface column 80 pixels wide, with 44 pixels above the first destination (less when there is a header), 12 between destinations. An expanded rail has 20 pixels of padding each side.

The look of [`NavigationRail`](../../components/navigation-rail.md) (in [Navigation rail](../../components/navigation-rail.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of NavigationRail (Material 3): a surface column 80 pixels wide, with 44 pixels above the first destination (less when there is a header),
# 12 between destinations. An expanded rail has 20 pixels of padding each side.
styles:
  - widget: NavigationRail
    style:
      background: "{{ 'surface@72%' if frosted else 'surface' }}"
      backdrop_blur: "{{ 20 if frosted else 0 }}"
      padding: "{{ {'left': 20, 'right': 20, 'top': 44, 'bottom': 56} if expanded else {'left': 0, 'right': 0, 'top': 44, 'bottom': 56} }}"
      gap: 12
```

## How it reaches the view

Each rule names `widget: NavigationRail` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `NavigationRail` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'surface@72%' if frosted else 'surface' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `backdrop_blur` | `{{ 20 if frosted else 0 }}` | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| always | `padding` | `{{ {'left': 20, 'right': 20, 'top': 44, 'bottom': 56} if expanded else {'left': 0, 'right': 0, 'top': 44, 'bo…` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `12` | Space between its children. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: NavigationRail
    style: {background: tertiary}
```
