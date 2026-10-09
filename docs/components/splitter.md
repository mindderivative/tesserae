# Splitter

*Beyond MD3*

## In Material Design 3

Material Design 3 has no splitter. It divides the window into two panes with a bar the user drags.

## In Tesserae

`widget: Splitter` has exactly two children, the panes, and a handle between them: a 16 pixel bar holding MD3's 4 by 48 drag handle, with a
resize cursor, a Tab stop, and the role of a slider for a screen reader.

| Property | Type | Meaning |
| --- | --- | --- |
| `orientation` | `horizontal` or `vertical` | side by side, or one above the other |
| `position` | 0 to 1, two-way | how much of the room the first pane has; bind a Signal and the handle writes it |
| `min_first`, `min_second` | pixels | the least each pane can be |
| `collapsible` | true or false | a double click on the handle closes the first pane, and opens it again where it was |
| `label` | text | what a screen reader calls the handle |

The pointer drags it (the pointer is captured, so it keeps following outside the handle); the arrow keys along its axis move it by 5%, Home
and End go to the ends; a screen reader can increment, decrement and set it. The parts a stylesheet can address are `first`, `handle`
and `second`. For more than two panes, nest splitters.

This component has no `component:` fragment: build it in Python.

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

## Using it

In Python:

```python
from tesserae.widgets import splitter

panes = splitter(app.window, left.node, right.node, 640, 400, orientation="horizontal", position=0.3)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
