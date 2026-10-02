# Video

*Content*

## In Material Design 3

Video is content, not a component, in Material Design 3; Tesserae shows frames you supply.

## In Tesserae

An `Image` node whose frame is pushed to it, from a binding.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Video` | A frame of video, fitted to its box. Frames come from a binding. | [`Video_Stylesheet.yaml`](../stylesheets/video/video.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Video`

A frame of video, fitted to its box. Frames come from a binding. Its look: [`Video_Stylesheet.yaml`](../stylesheets/video/video.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |
| `fit` | optional | `fill` |
| `frame` | optional | `None` |

```yaml
params:
  - width
  - height
  - {fit: fill}
  - {frame: null}
id: root
kind: Image
image:
  fit: "{{ fit }}"
bindings:
  if: "{{ frame }}"
  then:
    frame: "{{ frame }}"
a11y: {hidden: true}
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: clip
    component: Video
    with: {width: 320, height: 180, fit: contain}
```

In Python:

```python
from tesserae.widgets import video

clip = video(app.window, 320, 180, fit="contain")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Video_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
