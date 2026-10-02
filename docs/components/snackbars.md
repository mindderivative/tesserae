# Snackbars

*Communication*

## In Material Design 3

A snackbar briefly tells the user about a process that has happened or will happen, at the bottom of the
window, and may offer one action. It goes away by itself.

## In Tesserae

The fragment is its look; `tesserae.overlays.Snackbar` shows it on a layer above the window, with the
action and the close button.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Snackbar` | A snackbar: a short message about a process, at the bottom of the window. | [`Snackbar_Stylesheet.yaml`](../stylesheets/snackbars/snackbar.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Snackbar`

A snackbar: a short message about a process, at the bottom of the window. Its look: [`Snackbar_Stylesheet.yaml`](../stylesheets/snackbars/snackbar.md).

| Parameter | | Default |
| --- | --- | --- |
| `text` | required |  |
| `width` | required |  |

```yaml
params: [text, width]
id: root
kind: Container
children:
  - id: text
    kind: Text
    text:
      content: "{{ text }}"
      typography_role: body_medium
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: saved
    component: Snackbar
    with: {text: Saved, width: 280}
```

In Python:

```python
from tesserae.widgets import snackbar

bar = snackbar(app.window, "Saved", 280, action_label="Undo", on_action=viewmodel.undo)
bar.open()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Snackbar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
