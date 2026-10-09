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
`height`, or both. Hot reload watches the file and the pictures in it.

| Property | Type | Meaning |
| --- | --- | --- |
| `src` | file | a `.svg` or `.svgz` file next to the view; an expression, so it follows a Signal |
| `content` | text | the document itself, instead of a file (give one of `src` and `content`) |
| `alt` | text | what the picture shows, for a screen reader; without it the picture is decorative and hidden from one, unless it handles clicks |

This component is a widget, not a fragment: use `widget: Svg` in a view (see [The View Language](../guide/view-language.md)), or `kind: Svg` in the older syntax.

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

## Using the fragment

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
