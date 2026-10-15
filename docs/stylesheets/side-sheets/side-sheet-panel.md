# SideSheetPanel_Stylesheet.yaml

The look of the inside of a side sheet: 24 pixels beside the header and the content, 16 above the actions, the title in on_surface.

The look of [`SideSheetPanel`](../../components/side-sheets.md) (in [Side sheets](../../components/side-sheets.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of the inside of a side sheet: 24 pixels beside the header and the content, 16 above the actions, the title in on_surface.
styles:
  - widget: SideSheetPanel
    style:
      padding: {left: 24, right: 16, top: 0, bottom: 24}
  - {widget: SideSheetPanel, part: title, style: {foreground: on_surface}}
  - {widget: SideSheetPanel, part: actions, style: {padding: {left: 0, right: 8, top: 16, bottom: 0}}}
```

## How it reaches the view

Each rule names `widget: SideSheetPanel` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `SideSheetPanel` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 24, left: 24, right: 16, top: 0}` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `title` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `actions` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `{bottom: 0, left: 0, right: 8, top: 16}` | Space inside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: SideSheetPanel
    part: title
    style: {foreground: tertiary}
```
