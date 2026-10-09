# Chips

*Selection and input*

## In Material Design 3

Chips are compact elements for an action, a filter, a piece of input, or a suggestion. **Assist** chips
start an action, **filter** chips narrow results (and show a check when selected), **input** chips are
things the user entered, and **suggestion** chips offer a reply or next step.

## In Tesserae

`widget: Chip` is a view Tesserae ships (`Chip_View.yaml`): 32 pixels tall with 8 pixel corners, as wide as its label. `widget: ChipGroup` is a wrapping row of
them.

| Property | Type | Meaning |
| --- | --- | --- |
| `label` | text | the text |
| `variant` | `assist`, `filter`, `input`, `suggestion` | what it is for (default `assist`) |
| `icon`, `avatar_text` | an icon, letters | a leading 18 pixel icon, or letters in a 24 pixel circle |
| `selected` | true or false; two-way | a filter or input chip that is on: `secondary_container`, no outline, a check in place of the icon |
| `elevated` | true or false | a raised surface instead of an outline |
| `removable`, `removed`, `on_remove` | true or false; true or false, two-way; a handler | a close button; pressing it sets `removed` and runs `on_remove` |
| `disabled` | true or false | dimmed, not focusable, handlers do not respond |

A filter chip flips `selected` itself (`flip: false` leaves that to you); `handlers: {on_click: ...}` on the call is what a press does. A `ChipGroup` takes
`chips` (`{value, label}` and optionally `{icon, avatar_text, disabled}`) and a `mode`: `none` (assist or suggestion chips; the last pressed goes to
`chosen`), `single` or `multiple` (filter chips; `selected` is the value or the list of values), or `input` (chips with a close, and a field: Enter adds a
chip, the close removes one, and `chips` is two-way). Not built: dragging chips to reorder, and a chip group that scrolls sideways.

`widget: Chip` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: filters
widget: Container
style: {flex_direction: vertical, gap: 16, width: 420, height: 240}
children:
  - {widget: Chip, label: Share, icon: home, handlers: {on_click: share}}
  - widget: ChipGroup
    mode: multiple
    selected: "{{ filters }}"
    chips: [{value: open, label: Open}, {value: mine, label: Mine}, {value: late, label: Overdue}]
  - {widget: ChipGroup, mode: input, chips: "{{ tags }}", entry: "{{ typed }}"}
```

## Using it

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
