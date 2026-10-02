# Time input

*Selection and input*

## In Material Design 3

A time input field is a numeric field for the hour or the minute, used in the time picker's keyboard mode.

## In Tesserae

Python only.

This component has no `component:` fragment: build it in Python.

## Using it

In Python:

```python
from tesserae.widgets import time_input_field

hour = time_input_field(app.window, 9, unit="hour")
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
