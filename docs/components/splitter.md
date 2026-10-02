# Splitter

*Beyond MD3*

## In Material Design 3

Material Design 3 has no splitter. It divides the window into two panes with a bar the user drags.

## In Tesserae

Python only.

This component has no `component:` fragment: build it in Python.

## Using it

In Python:

```python
from tesserae.widgets import splitter

panes = splitter(app.window, left.node, right.node, 640, 400, orientation="horizontal", position=0.3)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
