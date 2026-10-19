# TopAppBar_Stylesheet.yaml

The look of TopAppBar (Material 3): a `surface` bar that becomes `surface_container` once content has scrolled under it; 4 pixels in from the edge for the icons, the title in on_surface (16 pixels from the left of a medium or large bar's title), 16 pixels of room at each end.

The look of [`TopAppBar`](../../components/top-app-bar.md) (in [Top app bar](../../components/top-app-bar.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of TopAppBar (Material 3): a `surface` bar that becomes `surface_container` once content has scrolled under it; 4 pixels in from the edge for the icons, the
# title in on_surface (16 pixels from the left of a medium or large bar's title), 16 pixels of room at each end.
styles:
  - widget: TopAppBar
    style:
      background: "{{ ('surface_container' if scrolled else 'surface') + ('@72%' if frosted else '') }}"
      backdrop_blur: "{{ 20 if frosted else 0 }}"
      padding: {left: 4, right: 4, top: 0, bottom: 0}
      clip_children: true
  - {widget: TopAppBar, part: title, style: {foreground: on_surface}}
  - {widget: TopAppBar, part: big_title, style: {foreground: on_surface, padding: {left: 12, right: 12, top: 0, bottom: 0}}}
```

## How it reaches the view

Each rule names `widget: TopAppBar` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `TopAppBar` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `{{ ('surface_container' if scrolled else 'surface') + ('@72%' if frosted else '') }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `backdrop_blur` | `{{ 20 if frosted else 0 }}` | Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface. |
| always | `padding` | `{bottom: 0, left: 4, right: 4, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `clip_children` | `true` | Whether children are cut off at its edge. |

### `title` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `big_title` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| always | `padding` | `{bottom: 0, left: 12, right: 12, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: TopAppBar
    style: {background: tertiary}
```
