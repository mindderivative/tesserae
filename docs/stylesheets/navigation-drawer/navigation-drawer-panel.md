# NavigationDrawerPanel_Stylesheet.yaml

The look of the inside of a drawer: 12 pixels in from the edge, section headings in on_surface_variant, a little space above the first destination.

The look of [`NavigationDrawerPanel`](../../components/navigation-drawer.md) (in [Navigation drawer](../../components/navigation-drawer.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of the inside of a drawer: 12 pixels in from the edge, section headings in on_surface_variant, a little space above the first destination.
styles:
  - widget: NavigationDrawerPanel
    style:
      padding: {left: 12, right: 12, top: 12, bottom: 12}
  - {widget: NavigationDrawerPanel, part: heading, style: {foreground: on_surface_variant, padding: {left: 16, right: 16, top: 18, bottom: 18}}}
```

## How it reaches the view

Each rule names `widget: NavigationDrawerPanel` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `NavigationDrawerPanel` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 12, left: 12, right: 12, top: 12}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `heading` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `padding` | `{bottom: 18, left: 16, right: 16, top: 18}` | Space inside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: NavigationDrawerPanel
    part: heading
    style: {foreground: tertiary}
```
