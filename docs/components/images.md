# Images

*Content*

## In Material Design 3

An image shows a picture, fitted to its box. Material Design 3 describes how to crop and round it in a
container: a corner from the shape scale, a circle for an avatar.

## In Tesserae

`widget: Image` is the engine's picture node: Tesserae reads and decodes the file (Pillow), and `fit` says how it fills the box (`cover` by default, or `contain` or `fill`).
`src` is relative to the view, and can be an expression, so it follows a Signal. `alt` says what the picture shows, for a screen reader; without it the picture is decorative
and hidden from one, unless it handles clicks. The path must be relative and stay inside the view's directory; an absolute one, or one that leaves it, is refused.

Its shape is `style.corner_radius`: a number, a shape token, `full` for a circle on a square picture, or a different radius on each
corner (`{top_left: 24}`). The engine clips the picture to it: `full` on a square picture is a circle (an avatar), and on any other a pill. Put it in a rule
(`classes: [avatar]`) and every picture with the class takes the shape. Not built: a picture clipped to any other shape (the engine can mask a node with a circle, a rounded rectangle or a path, but no style passes one on).
A missing or unreadable file stops the view opening, with the widget's name and the file in the message.

## How it is built

### `Image`

A picture.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `src` | `str` |  | A path relative to the file. |
| `fit` | `cover` or `contain` or `fill` | `cover` | How the picture fills its box. |
| `alt` | `str` |  | What the picture shows, for a screen reader. Without it the picture is decorative and hidden from one. |
| `frame` | `any` |  | A video frame, (rgba, width, height), pushed from a ViewModel. |

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

## Using it in Python

```python
from tesserae.widgets import image

photo = image(app.window, "cat.png", 200, 150, fit="cover")
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
