# Checkbox

*Selection and input*

## In Material Design 3

A checkbox lets the user select one or more items from a set, or turn an option on or off. It has a 40dp
state layer around an 18dp box.

## In Tesserae

`widget: Checkbox` is one of Tesserae's controls (`tesserae.controls.Checkbox`). Give `checked` a bare reference and a press writes it back. It has three
states: on, off, and empty (`null`), which is neither: a dash in a filled box, for a parent of some checked children. A press turns an empty one on.

The `label` sits beside the box and is part of what you press: pressing the text toggles the box and gives it the focus. `error` draws it in the error colours, and a
disabled one is dimmed and does nothing. `handlers: {on_change: ...}` runs after the user changes it (not when the bound value changes).

The colour is `style.foreground`. The 18 pixel box sits in a 48 pixel target with a 40 pixel state layer; Tab reaches it, and Space or Enter toggles it.

## How it is built

### `Checkbox`

A box that is on or off.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `checked` | `bool` |  | true, false, or empty (null) for a box that is neither: a parent of some checked children. Two-way. |
| `disabled` | `bool` |  |  |
| `error` | `bool` |  | Drawn in the error colours. |
| `label` | `str` |  | Text beside it that is part of what you press, and what a screen reader calls it. |

Its `style:` also takes `foreground`.

## Using it

```yaml
name: terms
widget: Container
style: {flex_direction: vertical, gap: 4, width: 280, height: 160, padding: 16}
children:
  - {widget: Checkbox, checked: "{{ all_read }}", label: I have read the terms, error: "{{ show_error }}"}
  - {widget: Checkbox, checked: "{{ some_read }}", label: Select all}      # empty while only some are on
```

## Using it in Python

```python
from tesserae.widgets import checkbox

agree = checkbox(app.window, (0xFF, 0xFF, 0xFF, 0xFF), 48, 48, checked=False)
agree.checked.get()
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
