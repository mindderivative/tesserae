# Chips

*Selection and input*

## In Material Design 3

Chips are compact elements for an action, a filter, a piece of input, or a suggestion. **Assist** chips
start an action, **filter** chips narrow results (and show a check when selected), **input** chips are
things the user entered, and **suggestion** chips offer a reply or next step.

## In Tesserae

A rounded `Rect` with a label. The selected filter chip is its own fragment because a fragment's structure
can't change with a parameter: it adds the check mark.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ChipAssist` | An assist chip: a smart or automated action, such as adding to a calendar. | [`ChipAssist_Stylesheet.yaml`](../stylesheets/chips/chip-assist.md) |
| `component: ChipFilter` | A filter chip, not selected: narrows a set of results. | [`ChipFilter_Stylesheet.yaml`](../stylesheets/chips/chip-filter.md) |
| `component: ChipFilterSelected` | A filter chip, selected: shows a check mark and the selected colour. | [`ChipFilterSelected_Stylesheet.yaml`](../stylesheets/chips/chip-filter-selected.md) |
| `component: ChipInput` | An input chip: a piece of information the user entered, such as a tag. | [`ChipInput_Stylesheet.yaml`](../stylesheets/chips/chip-input.md) |
| `component: ChipSuggestion` | A suggestion chip: a dynamic suggestion, such as a smart reply. | [`ChipSuggestion_Stylesheet.yaml`](../stylesheets/chips/chip-suggestion.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ChipAssist`, `ChipFilter`, `ChipInput`, `ChipSuggestion`

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params: [label, width]
id: root
kind: Rect
children:
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
      text_align: center
```

### `ChipFilterSelected`

A filter chip, selected: shows a check mark and the selected colour. Its look: [`ChipFilterSelected_Stylesheet.yaml`](../stylesheets/chips/chip-filter-selected.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |

```yaml
params: [label, width]
id: root
kind: Rect
children:
  - id: check
    kind: Icon
    icon: {name: check}
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
      text_align: center
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: shipped
    component: ChipFilterSelected
    with: {label: Shipped, width: 96}
```

In Python:

```python
from tesserae.widgets import chip

shipped = chip(app.window, "Shipped", 96, variant="filter", selected=True)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ChipAssist_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
