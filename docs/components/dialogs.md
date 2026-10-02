# Dialogs

*Containment*

## In Material Design 3

A dialog interrupts to ask for a decision or give needed information. It has a headline, supporting text and
up to two actions, on a raised surface over a scrim, and blocks what is behind it.

## In Tesserae

The fragment draws the scrim and the panel; `tesserae.overlays.Dialog` shows it as a modal layer, with
Escape and a click on the scrim closing it.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Dialog` | A dialog: a headline and text on a raised panel, over a scrim. | [`Dialog_Stylesheet.yaml`](../stylesheets/dialogs/dialog.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Dialog`

A dialog: a headline and text on a raised panel, over a scrim. Its look: [`Dialog_Stylesheet.yaml`](../stylesheets/dialogs/dialog.md).

| Parameter | | Default |
| --- | --- | --- |
| `headline` | required |  |
| `text` | required |  |
| `width` | required |  |
| `height` | required |  |
| `scrim_width` | required |  |
| `scrim_height` | required |  |

```yaml
params: [headline, text, width, height, scrim_width, scrim_height]
id: root
kind: Container
children:
  - id: panel
    kind: Container
    children:
      - id: headline
        kind: Text
        text:
          content: "{{ headline }}"
          typography_role: headline_small
      - id: body
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
  - id: confirm
    component: Dialog
    with: {headline: "Discard changes?", text: "Your edits will be lost.", width: 320, height: 200, scrim_width: 800, scrim_height: 600}
```

In Python:

```python
from tesserae.widgets import dialog

confirm = dialog(app.window, "Discard changes?", "Your edits will be lost.", 320, 200,
                 actions=[("Cancel", None), ("Discard", viewmodel.discard)])
confirm.open()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Dialog_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
