# Tooltips

*Communication*

## In Material Design 3

A tooltip names or explains a control when the pointer rests on it, or it has keyboard focus.

## In Tesserae

Any node takes a `tooltip:`. A plain one is text on the inverse surface; a rich one has a `title`, up to two `actions` and a `placement`
(`below`, `above`, `start`, `end`, or a corner: `top_start`, `top_end`, `bottom_start`, `bottom_end`, `center`, which puts the middle of the tooltip on that point and is not flipped), is a raised surface the pointer can move onto, and closes when an action is pressed. It shows after the
pointer rests for `delay` (500 ms by default), at once on keyboard focus (focus that a click gave does not count), or after a touch held in place; Escape, a press, or leaving
closes it. The text also names the node for a screen reader, unless the node has a description of its own. Not built: reaching the actions by keyboard.

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

## Using it in Python

```python
from tesserae.widgets import tooltip

tip = tooltip(app.window, "Save the file", anchor=save.node)
```

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
