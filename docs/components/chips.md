# Chips

*Selection and input*

## In Material Design 3

Chips are compact elements for an action, a filter, a piece of input, or a suggestion. **Assist** chips
start an action, **filter** chips narrow results (and show a check when selected), **input** chips are
things the user entered, and **suggestion** chips offer a reply or next step.

## In Tesserae

`widget: Chip` is a view Tesserae ships (`Chip_View.yaml`): 32 pixels tall with 8 pixel corners, as wide as its label. `widget: ChipGroup` is a wrapping row of
them.

A chip has a leading 18 pixel `icon`, or `avatar_text`: letters in a 24 pixel circle. A filter or input chip that is `selected` is `secondary_container` with no outline, and
a filter chip also shows a check in place of its icon. `elevated` swaps the outline for a raised surface. A `removable` chip (an input chip) has a close button: pressing it
sets `removed` to true and runs `on_remove`. A filter chip is a checkbox to a screen reader and the others are buttons; a disabled chip is dimmed and not focusable.

A filter chip flips `selected` itself (`flip: false` leaves that to you); `handlers: {on_click: ...}` on the call is what a press does. A `ChipGroup` takes
`chips` (`{value, label}` and optionally `{icon, avatar_text, disabled}`) and a `mode`: `none` (assist or suggestion chips; the last pressed goes to
`chosen`), `single` or `multiple` (filter chips; `selected` is the value or the list of values), or `input` (chips with a close, and a field: Enter adds a
chip, the close removes one, and `chips` is two-way; `entry` is what is typed and `placeholder` its hint). In `none` mode `variant` is `assist` or `suggestion`, and
`elevated` raises every chip. The group is one Tab stop and the arrow keys move the focus along the chips (in `single` mode the focus carries the choice with it). Not built:
dragging chips to reorder, and a chip group that scrolls sideways.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Chip`. A file of the same name in your project replaces it.

### `Chip`

The Material 3 chip: assist (an action), filter (a toggle), input (a piece of what the user entered, with a close) or suggestion (a suggested reply or query). 32 pixels tall with 8 pixel corners, a `label_large` label and an optional 18 pixel leading `icon` or 24 pixel avatar (`avatar_text`, letters in a circle). A filter chip flips `selected` on a press, and while it is on it is `secondary_container` with a check in place of its icon. An input chip has a close button, `removable`, which sets `removed` to true. `elevated` swaps the outline for a raised surface. `handlers: {on_click: ...}` on the call is what a press does. Colours and shapes are in Chip_Stylesheet.yaml.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The text. |
| `variant` | `assist` or `filter` or `input` or `suggestion` | `assist` | assist runs an action; filter toggles; input is what the user entered; suggestion offers a reply or a query. |
| `icon` | `str` |  | A leading icon. |
| `avatar_text` | `str` |  | Letters in a circle before the label (an avatar). |
| `selected` | `bool` | `false` | For a filter or input chip: whether it is on. Two-way: give it a bare reference and the view writes it back. |
| `elevated` | `bool` | `false` | A raised surface instead of an outline. |
| `removable` | `bool` | `false` | A close button after the label (an input chip). |
| `removed` | `bool` | `false` | Set to true when the close button is pressed. Two-way: give it a bare reference and the view writes it back. |
| `on_remove` | `handler` |  | What to do when the close button is pressed, written as a handler (an action name or statements). |
| `flip` | `bool` | `true` | For a filter chip: whether a press flips `selected` itself. Off, the caller decides (a chip group does). |
| `disabled` | `bool` | `false` | Dimmed, not focusable, and it does not respond. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `avatar` (Container), `avatar_text` (Text), `icon` (Icon), `label` (Text), `close` (Container), `close_icon` (Icon).

Its look is in [`Chip_Stylesheet.yaml`](../stylesheets/chips/chip.md).

### `ChipGroup`

A group of chips, wrapping onto new rows. `chips` is a list of {value, label} and optionally {icon, avatar_text, disabled}. `mode` says how they behave: `none` suggestion/assist chips that act (the last one pressed goes to `chosen`); `single` and `multiple` filter chips (`selected` is the chosen value, or the list of them); `input` chips with a close button and a text field after them, so typing and pressing Enter adds a chip, and the close removes one (`chips` is two-way: the list the user has built). One Tab stop; the arrows move the focus along the chips (and, for `single`, the choice).

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `chips` | `list` | `[]` | The chips, each {value, label} and optionally {icon, avatar_text, disabled}. In input mode adding and removing write it back. Two-way: give it a bare reference and the view writes it back. |
| `mode` | `none` or `single` or `multiple` or `input` | `none` | none: actions; single or multiple: filters; input: what the user entered. |
| `selected` | `any` |  | single: the chosen value; multiple: the list of chosen values. Two-way: give it a bare reference and the view writes it back. |
| `chosen` | `any` |  | none: the value of the chip last pressed. Two-way: give it a bare reference and the view writes it back. |
| `variant` | `assist` or `suggestion` | `assist` | The look of the chips in `none` mode. |
| `elevated` | `bool` | `false` | Raised chips instead of outlined ones. |
| `placeholder` | `str` | `Add` | Input mode: the hint in the text field. |
| `entry` | `str` |  | Input mode: what is typed in the field. Two-way: give it a bare reference and the view writes it back. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `chip` (Chip), `entry` (TextField).

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

## Using it in Python

```python
from tesserae.widgets import chip

shipped = chip(app.window, "Shipped", 96, variant="filter", selected=True)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Chip_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Chip
    part: label
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
