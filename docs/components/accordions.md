# Accordions

*Containment*

## In Material Design 3

Material Design 3 has no accordion of its own. Tesserae's is built in MD3's terms: a list row with a chevron
that turns when the section opens.

## In Tesserae

Two views Tesserae ships. `widget: Accordion` is one section: a 56 pixel header button (the `title` and a chevron that turns over in 200 milliseconds) and, while `expanded`
(two-way), its content (the children). `widget: AccordionGroup` makes several behave as one set with dividers between them.

A press, Enter or Space on the header toggles `expanded`, and `on_toggle` is called after it. A `disabled` section is dimmed and does not toggle. An `AccordionGroup` takes
`items`, each `{value, title, text}` (the text is the section's content; for more than text, write the `Accordion` sections yourself); `mode` is `single` (the default: opening one
closes the rest) or `multiple`, and `open` is the value that is open (empty for none), or with `multiple` the list of values that are.

A screen reader hears a button that says whether it is expanded and what it controls; the content is hidden from it while closed and its parts are not built, so they
take no Tab stop. The up and down arrows move between the headers, and Home and End go to the first and last. Not built: the content's height easing open
(the engine cannot ease a height to `auto`).

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Accordion`. A file of the same name in your project replaces it.

### `Accordion`

One section of an accordion: a 56 pixel header button (the title, and a chevron that turns over when it opens) and, while `expanded`, the content (the children). A press, Enter or Space toggles it; `expanded` is two-way. A screen reader hears a button that says whether it is expanded and what it controls. `AccordionGroup` makes several of them behave as one set.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `title` | `str` |  | The header's text. |
| `expanded` | `bool` | `false` | Whether the content shows. Two-way: give it a bare reference and the view writes it back. |
| `disabled` | `bool` | `false` | Dimmed, and it does not toggle. |
| `on_toggle` | `handler` |  | Called after the header has been pressed (a group uses it to close the others). |

Children go in the default slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `header` (Container), `title` (Text), `filler` (Container), `chevron` (Icon), `content` (Container), `inner` (Container).

Its look is in [`Accordion_Stylesheet.yaml`](../stylesheets/accordions/accordion.md).

### `AccordionGroup`

Several accordion sections as one set, with a divider between them. `items` is a list of {value, title, text} (the text is the section's content; for more than text, use `Accordion` sections yourself). `mode: single` keeps one open (opening one closes the rest), `multiple` lets any number be; `open` is the value that is open, or the list of values with `multiple`, and is two-way. The up and down arrows move between the headers, and Home and End go to the first and last.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `items` | `list` | `[]` | The sections, each {value, title, text}. |
| `mode` | `single` or `multiple` | `single` | single: at most one open; multiple: any number. |
| `open` | `any` |  | single: the value that is open (empty for none); multiple: the list of values that are open. Two-way: give it a bare reference and the view writes it back. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `section` (Container), `divider` (Divider), `panel` (Accordion), `text` (Text).

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

## Using it in Python

```python
from tesserae.widgets import accordion_header

details = accordion_header(app.window, "Details", expanded=False, width=320)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Accordion_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Accordion
    part: title
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
