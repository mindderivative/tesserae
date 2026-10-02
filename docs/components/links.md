# Links

*Navigation*

## In Material Design 3

A link takes the user somewhere else, or opens a related page. It is text, in the primary colour.

## In Tesserae

The `Link` node kind: text that takes focus, and that Enter or a click activates.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Link` | Text that opens something when it is clicked. | [`Link_Stylesheet.yaml`](../stylesheets/links/link.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Link`

Text that opens something when it is clicked. Its look: [`Link_Stylesheet.yaml`](../stylesheets/links/link.md).

| Parameter | | Default |
| --- | --- | --- |
| `text` | required |  |
| `width` | required |  |
| `height` | required |  |

```yaml
params: [text, width, height]
id: root
kind: Link
text:
  content: "{{ text }}"
  typography_role: body_large
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: help
    component: Link
    with: {text: Read the docs, width: 160, height: 24}
    handlers: {on_click: open_docs}
```

In Python:

```python
from tesserae.widgets import link

help_link = link(app.window, "Read the docs", 160, on_click=viewmodel.open_docs)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Link_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
