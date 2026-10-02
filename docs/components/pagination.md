# Pagination

*Content*

## In Material Design 3

Pagination shows where the user is among pages: a row of dots or numbers.

## In Tesserae

Python only.

This component has no `component:` fragment: build it in Python.

## Using it

In Python:

```python
from tesserae.widgets import pagination

pages = pagination(app.window, 10, current=0)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
