# Tooltips

*Communication*

## In Material Design 3

A tooltip names or explains a control when the pointer rests on it, or it has keyboard focus.

## In Tesserae

Any node takes a `tooltip:`. A plain one is text on the inverse surface; a rich one has a `title`, up to two `actions` and a `placement`
(`below`, `above`, `start`, `end`), is a raised surface the pointer can move onto, and closes when an action is pressed. It shows after the
pointer rests for `delay` (500 ms), at once on keyboard focus, or after a long press; Escape, a press, or leaving closes it. The text also names
the node for a screen reader. Not built: reaching the actions by keyboard.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Tooltip` | A tooltip: a short label that appears beside what the pointer rests on. | [`Tooltip_Stylesheet.yaml`](../stylesheets/tooltips/tooltip.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Tooltip`

A tooltip: a short label that appears beside what the pointer rests on. Its look: [`Tooltip_Stylesheet.yaml`](../stylesheets/tooltips/tooltip.md).

| Parameter | | Default |
| --- | --- | --- |
| `text` | required |  |
| `width` | required |  |

```yaml
params: [text, width]
id: root
kind: Container
children:
  - id: text
    kind: Text
    text:
      content: "{{ text }}"
      typography_role: body_small
      wrap: none
      overflow: ellipsis
```

## Using it

```yaml
name: file
widget: Container
style: {width: 240, height: 120, padding: 24}
children:
  - widget: Button
    label: Delete
    tooltip: {title: Delete, text: Removes the file for good, actions: [{label: Undo, on_click: undo}]}
  - widget: Button
    label: Save
    variant: tonal
    tooltip: Save the file
```

## Using it

In Python:

```python
from tesserae.widgets import tooltip

tip = tooltip(app.window, "Save the file", anchor=save.node)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Tooltip_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
