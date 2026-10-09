# Accordions

*Containment*

## In Material Design 3

Material Design 3 has no accordion of its own. Tesserae's is built in MD3's terms: a list row with a chevron
that turns when the section opens.

## In Tesserae

Two views Tesserae ships. `widget: Accordion` is one section: a 56 pixel header button (the `title` and a chevron that turns over in 200 milliseconds) and, while `expanded`
(two-way), its content (the children). `widget: AccordionGroup` makes several behave as one set with dividers between them.

| Property | Type | Meaning |
| --- | --- | --- |
| `title`, `expanded`, `disabled` | text, true or false (two-way), true or false | the header, whether the content shows, dimmed and not toggling |
| `on_toggle` | a handler | called after the header has been pressed |
| `items`, `mode`, `open` (`AccordionGroup`) | a list of `{value, title, text}`, `single` or `multiple`, a value or a list; two-way | the sections, whether one or several can be open, and which are |

A screen reader hears a button that says whether it is expanded and what it controls; the content is hidden from it while closed and its parts are not built, so they
take no Tab stop. The up and down arrows move between the headers, and Home and End go to the first and last. Not built: the content's height easing open
(the engine cannot ease a height to `auto`).

`widget: Accordion` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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
      wrap: none
      overflow: ellipsis
  - id: chevron
    kind: Icon
    icon: {name: expand_more}
```

## Using it

```yaml
name: faq
widget: Container
style: {flex_direction: vertical, gap: 16, width: 420, height: 360}
children:
  - widget: Accordion
    title: Details
    expanded: "{{ showing }}"
    children:
      - {widget: Text, text: More about it, typography_role: body_medium, style: {foreground: on_surface_variant}}
  - widget: AccordionGroup
    open: "{{ which }}"
    items:
      - {value: a, title: Shipping, text: Two days.}
      - {value: b, title: Returns, text: Thirty days.}
```

## Using it

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
