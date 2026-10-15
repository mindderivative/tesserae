# Extended FABs

*Actions*

## In Material Design 3

An extended FAB is a FAB with a text label, for a main action that an icon alone wouldn't explain.

## In Tesserae

It is the same `widget: Fab` (see Floating action buttons) given a `label`: 56 tall, as wide as its label, with 16 pixels before the icon and 20
after the text. Give no `icon` for a text-only one.

## How it is built

It is the same view as the [fabs](../components/fabs.md): see there for what it takes and how it looks.

## Using it

```yaml
name: inbox
widget: Container
style: {width: 240, height: 120}
children:
  - {widget: Fab, label: New, icon: add, variant: secondary, handlers: {on_click: create}}
```

## Using it in Python

```python
from tesserae.widgets import extended_fab

new = extended_fab(app.window, "New", 120, icon="add", variant="primary")
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
