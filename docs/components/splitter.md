# Splitter

*Beyond MD3*

## In Material Design 3

Material Design 3 has no splitter. It divides the window into two panes with a bar the user drags.

## In Tesserae

`widget: Splitter` has exactly two children, the panes, and a handle between them: a 16 pixel bar holding MD3's 4 by 48 drag handle, with a
resize cursor, a Tab stop, and the role of a slider for a screen reader.

`orientation` puts the panes side by side (`horizontal`, the default) or one above the other (`vertical`). `position`, from 0 to 1, is how much of the room the first
pane has, two-way: bind a Signal and the handle writes it. `min_first` and `min_second` are the least each pane can be, in pixels. With `collapsible: true` a double click
on the handle closes the first pane, and opens it again where it was. `label` is what a screen reader calls the handle.

The pointer drags it (the pointer is captured, so it keeps following outside the handle); the arrow keys along its axis move it by 5%, Home
and End go to the ends; a screen reader can increment, decrement and set it. For more than two panes, nest splitters.

## How it is built

### `Splitter`

Two panes with a draggable, keyboard-operable handle between them.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `orientation` | `horizontal` or `vertical` | `horizontal` | horizontal puts the panes side by side, vertical one above the other. |
| `position` | `float` | `0.5` | How much of the room the first pane has, from 0 to 1. Dragging the handle writes it back to a Signal it is bound to. Two-way. |
| `min_first` | `float` |  | The least the first pane can be, in pixels. |
| `min_second` | `float` |  | The least the second pane can be, in pixels. |
| `collapsible` | `bool` |  | A double click on the handle closes the first pane, and opens it again. |
| `label` | `str` | `Resize panes` | What a screen reader calls the handle. |

## Using it

```yaml
name: editor
widget: Container
style: {width: 640, height: 400}
children:
  - widget: Splitter
    position: "{{ sidebar }}"
    min_first: 120
    min_second: 240
    collapsible: true
    label: Resize the sidebar
    style: {width: 640, height: 400}
    children:
      - {widget: Container, name: sidebar_pane, style: {background: surface_container, flex: fill}}
      - {widget: Container, name: content_pane, style: {background: surface, flex: fill}}
```

## Using it in Python

```python
from tesserae.widgets import splitter

panes = splitter(app.window, left.node, right.node, 640, 400, orientation="horizontal", position=0.3)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
