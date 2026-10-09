# Images

*Content*

## In Material Design 3

An image shows a picture, fitted to its box. Material Design 3 describes how to crop and round it in a
container: a corner from the shape scale, a circle for an avatar.

## In Tesserae

`widget: Image` is the engine's picture node: Tesserae reads and decodes the file (Pillow), and `fit` says how it fills the box.

| Property | Type | Meaning |
| --- | --- | --- |
| `src` | file | the picture, relative to the view; an expression, so it follows a Signal |
| `fit` | `cover`, `contain` or `fill` | how it fills its box; `cover` by default |
| `alt` | text | what the picture shows, for a screen reader; without it the picture is decorative and hidden from one, unless it handles clicks |

Its shape is `style.corner_radius`: a number, a shape token, `full` for a circle on a square picture, or a different radius on each
corner (`{top_left: 24}`). The engine clips the picture to it: `full` on a square picture is a circle (an avatar), and on any other a pill. Put it in a rule
(`classes: [avatar]`) and every picture with the class takes the shape. A shape that is not a rounded rectangle needs a mask the engine does not have.
A missing or unreadable file stops the view opening, with the widget's name and the file in the message.

`widget: Image` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: profile
widget: Container
style: {flex_direction: vertical, gap: 16, width: 240, height: 320}
children:
  - widget: Image
    src: cat.png
    alt: A grey cat asleep on a windowsill
    fit: cover
    style: {width: 240, height: 160, corner_radius: medium}
  - widget: Image
    src: avatar.png
    alt: Your photo
    style: {width: 64, height: 64, corner_radius: full}
```

## Using the fragment

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
