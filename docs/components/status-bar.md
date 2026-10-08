# Status bar

*Beyond MD3*

## In Material Design 3

Material Design 3 has no status bar. A desktop app often wants one, so this is a thin strip in MD3's
surface and *label* style.

## In Tesserae

A container with one `Text`. It keeps its height when the window is short, and takes a `style`.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: StatusBar` | A status bar: a thin strip of text along the bottom of the window. | [`StatusBar_Stylesheet.yaml`](../stylesheets/status-bar/status-bar.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `StatusBar`

A status bar: a thin strip of text along the bottom of the window. Its look: [`StatusBar_Stylesheet.yaml`](../stylesheets/status-bar/status-bar.md).

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
      typography_role: label_small
      wrap: none
      overflow: ellipsis
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: status
    component: StatusBar
    with: {text: Ready, width: 640}
```

In Python:

```python
from tesserae.widgets import status_bar

status = status_bar(app.window, "Ready", style={"height": 32})
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# StatusBar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
