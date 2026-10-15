# Switch

*Selection and input*

## In Material Design 3

A switch toggles one setting on or off, and takes effect at once. It has a track and a thumb that grows when
it is on.

## In Tesserae

`widget: Switch`, a Tesserae control: a 52 by 32 pixel track and a handle that slides across it and grows when pressed (16 pixels off, 24 on, 28 pressed). The `label` sits beside
the track and is part of what you press. With `icons: true` the handle carries a check when on and a cross when off, and the off handle is then as big as the on one. Space or
Enter toggles it from the keyboard, and `handlers: {on_change: ...}` runs after the user toggles it.

## How it is built

### `Switch`

A toggle.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `selected` | `bool` |  |  Two-way. |
| `disabled` | `bool` |  |  |
| `label` | `str` |  | Text beside it that is part of what you press, and what a screen reader calls it. |
| `icons` | `bool` |  | A check on the handle when on and a cross when off. |

Its `style:` also takes `foreground`.

## Using it

```yaml
name: settings
widget: Container
style: {flex_direction: vertical, gap: 8, width: 240, height: 140, padding: 16}
children:
  - {widget: Switch, selected: "{{ wifi }}", label: Wi-Fi}
  - {widget: Switch, selected: "{{ dark }}", label: Dark mode, icons: true}
```

## Using it in Python

```python
from tesserae.widgets import switch

dark = switch(app.window, selected=False)
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
