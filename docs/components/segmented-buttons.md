# Segmented buttons

*Selection and input*

## In Material Design 3

A segmented button is a row of two to five connected options, for one choice or several.

## In Tesserae

Python only: there is no `component:` fragment, because the number of segments changes its structure.

This component has no `component:` fragment: build it in Python.

## Using it

In Python:

```python
from tesserae.widgets import segmented_button

view = segmented_button(app.window, ["Day", "Week", "Month"], selected=0)
many = segmented_button(app.window, ["Bold", "Italic"], multi=True, selected=[0])
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
