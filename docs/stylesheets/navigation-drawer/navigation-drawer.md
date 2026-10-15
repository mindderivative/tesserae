# NavigationDrawer_Stylesheet.yaml

The look of the standard navigation drawer: a `surface` column.

The look of [`NavigationDrawer`](../../components/navigation-drawer.md) (in [Navigation drawer](../../components/navigation-drawer.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of the standard navigation drawer: a `surface` column.
styles:
  - widget: NavigationDrawer
    style:
      background: "{{ 'surface@72%' if frosted else 'surface' }}"
      backdrop_blur: "{{ 20 if frosted else 0 }}"
```

## How it reaches the view

Each rule names `widget: NavigationDrawer` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `NavigationDrawer` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'surface@72%' if frosted else 'surface' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `backdrop_blur` | `{{ 20 if frosted else 0 }}` | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: NavigationDrawer
    style: {background: tertiary}
```
