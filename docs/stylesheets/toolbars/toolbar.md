# Toolbar_Stylesheet.yaml

The look of Toolbar (Material 3): a docked one is a 64 pixel surface_container strip with 16 pixels of padding; a floating one is a pill at elevation level 3 with 8 pixels of padding. Vibrant uses primary_container. The buttons stand 4 pixels apart.

The look of [`Toolbar`](../../components/toolbars.md) (in [Toolbars](../../components/toolbars.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Toolbar (Material 3): a docked one is a 64 pixel surface_container strip with 16 pixels of padding; a floating one is a pill at elevation level 3 with 8 pixels of padding.
# Vibrant uses primary_container. The buttons stand 4 pixels apart.
styles:
  - widget: Toolbar
    style:
      background: "{{ 'primary_container' if vibrant else 'surface_container' }}"
  - {widget: Toolbar, variant: docked, style: {padding: {left: 16, right: 16, top: 0, bottom: 0}, gap: 8}}
  - {widget: Toolbar, variant: floating, style: {padding: 8, gap: 8, corner_radius: full, elevation: 3}}
  - {widget: Toolbar, part: group, style: {gap: 4}}
```

## How it reaches the view

Each rule names `widget: Toolbar` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Toolbar` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ 'primary_container' if vibrant else 'surface_container' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: docked` | `padding` | `{bottom: 0, left: 16, right: 16, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `variant: docked` | `gap` | `8` | Space between its children. |
| `variant: floating` | `padding` | `8` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `variant: floating` | `gap` | `8` | Space between its children. |
| `variant: floating` | `corner_radius` | `full` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `variant: floating` | `elevation` | `3` | A shadow level, 0 to 5. |

### `group` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `gap` | `4` | Space between its children. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Toolbar
    style: {background: tertiary}
```
