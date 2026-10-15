# Lists

*Containment*

## In Material Design 3

A list is a column of rows, each a headline with optional leading and trailing content and supporting text.

## In Tesserae

`widget: ListItem` is a view Tesserae ships (`ListItem_View.yaml`): a row as wide as its place, 56, 72 or 88 pixels tall by its lines. A list is a
container of them (or a `for:`, or a `VirtualList`, over your data).

The `headline` is the first line, `supporting` the line under it and `overline` a small line above it; they set the height (56 for one line, 72 for two, 88 for three) unless
`lines` says. Before the text goes a 24 pixel `leading_icon`, a 40 pixel circle holding the letters of `leading_text`, or a 56 pixel `leading_image`; after it a `trailing_text` or a
`trailing_icon`. With `selectable` a press flips `selected`, and a selected row is `secondary_container`. `divider` draws a line along the bottom edge.

Your own content goes in the `leading` and `trailing` slots (`slot: trailing` on a child): a switch, a checkbox, a button. `handlers: {on_click: ...}` on
the call is what a press does. A section's header can hold the top of a `ScrollView` while its rows scroll past: give it `style: {sticky: 0}`. Not built: swipe actions, drag to
reorder, and the dragged state.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: ListItem`. A file of the same name in your project replaces it.

### `ListItem`

The Material 3 list item: one, two or three lines of text with something before it and something after it. `headline` is the first line, `supporting` the second, and an `overline` goes above the headline; the item is 56, 72 or 88 pixels tall by how many of those it has (`lines` overrides). Before the text: a `leading_icon`, a `leading_text` in a circle (an avatar), a `leading_image` (56 pixels), or your own content in the `leading` slot. After it: a `trailing_text`, a `trailing_icon`, or your own content in the `trailing` slot (a switch, a checkbox, a button). It is pressable (a state layer, a ripple, Enter); `handlers: {on_click: open}` on the call is what a press does. With `selectable` a press flips `selected`, and a selected item is `secondary_container`. `divider` draws a line along its bottom edge.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `headline` | `str` |  | The first line. |
| `supporting` | `str` |  | The line under the headline. |
| `overline` | `str` |  | A small line above the headline. |
| `leading_icon` | `str` |  | An icon before the text. |
| `leading_text` | `str` |  | One or two letters in a circle before the text (an avatar). |
| `leading_image` | `str` |  | A picture before the text, 56 pixels, relative to the view. |
| `trailing_text` | `str` |  | Small text after it. |
| `trailing_icon` | `str` |  | An icon after it. |
| `lines` | `int` | `0` | 1, 2 or 3 lines; 0 works it out from the text it has. |
| `selectable` | `bool` | `false` | A press flips `selected`. |
| `selected` | `bool` | `false` | Whether it is selected. Two-way: give it a bare reference and the view writes it back. |
| `disabled` | `bool` | `false` | Dimmed, not focusable, and it does not respond. |
| `divider` | `bool` | `false` | A line along the bottom edge. |

Children go in the `leading` slot, the `trailing` slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `leading_icon` (Icon), `avatar` (Container), `avatar_text` (Text), `picture` (Image), `text` (Container), `overline` (Text), `headline` (Text), `supporting` (Text), `trailing_text` (Text), `trailing_icon` (Icon), `line` (Divider).

Its look is in [`ListItem_Stylesheet.yaml`](../stylesheets/lists/list-item.md).

## Using it

```yaml
name: mail
widget: Container
style: {flex_direction: vertical, width: 360, height: 300}
children:
  - {widget: ListItem, headline: Inbox, supporting: 12 unread, leading_icon: home, trailing_text: 5m, divider: true, handlers: {on_click: open_inbox}}
  - widget: ListItem
    headline: Wi-Fi
    supporting: Connected
    children:
      - {widget: Switch, slot: trailing, selected: "{{ wifi }}"}
```

## Using it in Python

```python
from tesserae.widgets import list_, list_item

rows = list_(app.window, [list_item(app.window, name) for name in ("Inbox", "Sent", "Drafts")], width=320)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# ListItem_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: ListItem
    part: headline
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Repeater](../guide/repeater.md)
- [Effects](../guide/effects.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
