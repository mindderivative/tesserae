# Carousel

*Content*

## In Material Design 3

A carousel shows a row of items that scroll, with the focused one largest. MD3 has multi-browse, uncontained,
hero and full-screen layouts.

## In Tesserae

Python only.

This component has no `component:` fragment: build it in Python.

## Using it

In Python:

```python
from tesserae.widgets import carousel

gallery = carousel(app.window, 480, 180, layout="multi_browse", items=[])
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
