# Checkbox

*Selection and input*

## In Material Design 3

A checkbox lets the user select one or more items from a set, or turn an option on or off. It has a 40dp
state layer around an 18dp box.

## In Tesserae

`widget: Checkbox` is one of Tesserae's controls (`tesserae.controls.Checkbox`). Give `checked` a bare reference and a press writes it back.

| Property | Type | Meaning |
| --- | --- | --- |
| `checked` | true, false or empty, two-way | empty (`null`) is neither on nor off: a dash in a filled box, for a parent of some checked children; a press turns it on |
| `label` | text | beside the box, part of what you press, and what a screen reader calls it |
| `error` | true or false | drawn in the error colours |
| `disabled` | true or false | dimmed and does nothing |

The colour is `style.foreground`. The 18 pixel box sits in a 48 pixel target with a 40 pixel state layer; Space toggles it from the keyboard.

`widget: Checkbox` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Checkbox` | A checkbox: one choice, on or off. | [`Checkbox_Stylesheet.yaml`](../stylesheets/checkboxes/checkbox.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Checkbox`

A checkbox: one choice, on or off. Its look: [`Checkbox_Stylesheet.yaml`](../stylesheets/checkboxes/checkbox.md).

| Parameter | | Default |
| --- | --- | --- |
| `background` | required |  |
| `width` | required |  |
| `height` | required |  |
| `checked` | required |  |

```yaml
params: [background, width, height, checked]
id: root
kind: Checkbox
checked: "{{ checked }}"
```

## Using it

```yaml
name: terms
widget: Container
style: {flex_direction: vertical, gap: 4, width: 280, height: 160, padding: 16}
children:
  - {widget: Checkbox, checked: "{{ all_read }}", label: I have read the terms, error: "{{ show_error }}"}
  - {widget: Checkbox, checked: "{{ some_read }}", label: Select all}      # empty while only some are on
```

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: agree
    component: Checkbox
    with: {background: surface, width: 48, height: 48, checked: false}
    handlers: {on_change: toggled}
```

In Python:

```python
from tesserae.widgets import checkbox

agree = checkbox(app.window, (0xFF, 0xFF, 0xFF, 0xFF), 48, 48, checked=False)
agree.checked.get()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Checkbox_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
