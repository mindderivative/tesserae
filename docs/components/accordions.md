# Accordions

*Containment*

## In Material Design 3

Material Design 3 has no accordion of its own. Tesserae's is built in MD3's terms: a list row with a chevron
that turns when the section opens.

## In Tesserae

The header only; the section under it is yours to show and hide, usually with a binding.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: AccordionHeader` | A section header that expands and collapses its content: a title and a chevron. | [`AccordionHeader_Stylesheet.yaml`](../stylesheets/accordions/accordion-header.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `AccordionHeader`

A section header that expands and collapses its content: a title and a chevron. Its look: [`AccordionHeader_Stylesheet.yaml`](../stylesheets/accordions/accordion-header.md).

| Parameter | | Default |
| --- | --- | --- |
| `title` | required |  |
| `width` | required |  |

```yaml
params: [title, width]
id: root
kind: Container
children:
  - id: title
    kind: Text
    text:
      content: "{{ title }}"
      typography_role: label_large
  - id: chevron
    kind: Icon
    icon: {name: expand_more}
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: details
    component: AccordionHeader
    with: {title: Details, width: 320}
```

In Python:

```python
from tesserae.widgets import accordion_header

details = accordion_header(app.window, "Details", expanded=False, width=320)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# AccordionHeader_Stylesheet.yaml, next to your views
styles:
  - id: title
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
