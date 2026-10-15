# SVG

*Content*

## In Material Design 3

Material Design 3 uses SVG for its icons and illustrations. An SVG document is vector art: shapes, gradients,
patterns, clips, masks and text, which scale to any size without blurring.

## In Tesserae

`widget: Svg`: the engine parses and draws the whole document as one scene, scaled to fit the node's box and
centred in it. Tesserae reads the file, and decodes the raster pictures in it (`<image href="...">`: PNG, JPEG, GIF
or WebP, found next to the SVG file, or a `data:` URL) for the engine, which decodes no image format. `style.foreground` is what
`currentColor` means in the document, so a monochrome icon follows the theme, light and dark. Give a `width` or a
`height`, or both.

Give one of `src`, a `.svg` or `.svgz` file next to the view (an expression, so it follows a Signal), and `content`, the document itself as text. `alt` says what the picture
shows, for a screen reader; without it the picture is decorative and hidden from one, unless it handles clicks. A missing file, or a document that is not SVG, stops the view
opening with the widget's name in the message.

## How it is built

### `Svg`

A vector picture.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `src` | `str` |  | A .svg or .svgz file, relative to the view. |
| `content` | `str` |  | The SVG text, instead of a file. |
| `alt` | `str` |  | What the picture shows, for a screen reader. Without it the picture is decorative and hidden from one. |

Its `style:` also takes `foreground`.

## Using it

```yaml
name: brand
widget: Container
style: {flex_direction: vertical, gap: 16, width: 240, height: 160}
children:
  - widget: Svg
    src: logo.svg
    alt: The Tesserae logo
    style: {width: 96, height: 96, foreground: primary}
  - widget: Svg
    content: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10" fill="currentColor"/></svg>'
    style: {width: 24, height: 24, foreground: on_surface}
```

## Using it in Python

```python
from tesserae.widgets import svg

logo = svg(app.window, '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10" fill="currentColor"/></svg>',
           width=48, height=48, color="primary", label="A dot")
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
