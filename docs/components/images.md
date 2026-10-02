# Images

*Content*

## In Material Design 3

An image shows a picture, fitted to its box. Material Design 3 describes how to crop and round it in a
container.

## In Tesserae

The `Image` kind: Tesserae reads and decodes the file, and `fit` says how it fills the box.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Image` | A picture from a file, fitted to its box. | [`Image_Stylesheet.yaml`](../stylesheets/images/image.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Image`

A picture from a file, fitted to its box. Its look: [`Image_Stylesheet.yaml`](../stylesheets/images/image.md).

| Parameter | | Default |
| --- | --- | --- |
| `src` | required |  |
| `width` | required |  |
| `height` | required |  |
| `fit` | required |  |

```yaml
params: [src, width, height, fit]
id: root
kind: Image
image:
  src: "{{ src }}"
  fit: "{{ fit }}"
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: photo
    component: Image
    with: {src: cat.png, width: 200, height: 150, fit: cover}
```

In Python:

```python
from tesserae.widgets import image

photo = image(app.window, "cat.png", 200, 150, fit="cover")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Image_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
