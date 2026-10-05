# SVG

*Content*

## In Material Design 3

Material Design 3 uses SVG for its icons and illustrations. An SVG document is vector art: shapes, gradients,
patterns, clips, masks and text, which scale to any size without blurring.

## In Tesserae

The `Svg` node kind: the engine parses and draws the whole document as one scene, scaled to fit the node's box and
centred in it. Tesserae reads the file, and decodes the raster pictures in it (`<image href="...">`: PNG, JPEG, GIF
or WebP, found next to the SVG file, or a `data:` URL) for the engine, which decodes no image format. `src:` is a
`.svg` or `.svgz` file next to the view, or `content:` is the document itself. `style.foreground` is what
`currentColor` means in the document, so a monochrome icon follows the theme, light and dark. Give a `width` or a
`height`, or both. Hot reload watches the file and the pictures in it.

This component is the `Svg` node kind, not a fragment: use `kind: Svg` in a view (the [YAML reference](../api/yaml.md#the-kinds)), or build it in Python.

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: logo
    kind: Svg
    svg:
      content: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10" fill="currentColor"/></svg>'
    style: {width: 48, height: 48, foreground: primary}
```

In Python:

```python
from tesserae.widgets import svg

logo = svg(app.window, '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10" fill="currentColor"/></svg>',
           width=48, height=48, color="primary", label="A dot")
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
