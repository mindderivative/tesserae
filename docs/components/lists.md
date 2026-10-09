# Lists

*Containment*

## In Material Design 3

A list is a column of rows, each a headline with optional leading and trailing content and supporting text.

## In Tesserae

`widget: ListItem` is a view Tesserae ships (`ListItem_View.yaml`): a row as wide as its place, 56, 72 or 88 pixels tall by its lines. A list is a
container of them (or a `for:`, or a `VirtualList`, over your data).

| Property | Type | Meaning |
| --- | --- | --- |
| `headline`, `supporting`, `overline` | text | the first line, the line under it, a small line above it |
| `leading_icon`, `leading_text`, `leading_image` | an icon, letters, a picture | before the text: a 24 pixel icon, a 40 pixel circle holding letters, a 56 pixel picture |
| `trailing_text`, `trailing_icon` | text, an icon | after it |
| `lines` | 1, 2 or 3 | the height; 0 works it out from the text |
| `selectable`, `selected` | true or false; `selected` is two-way | a press flips `selected`; a selected row is `secondary_container` |
| `disabled` | true or false | dimmed, not focusable, handlers do not run |
| `divider` | true or false | a line along the bottom edge |

Your own content goes in the `leading` and `trailing` slots (`slot: trailing` on a child): a switch, a checkbox, a button. `handlers: {on_click: ...}` on
the call is what a press does. Not built: swipe actions, drag to reorder, sticky headers, and the dragged state.

`widget: ListItem` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ListItem` | A list row: a headline, and room for more. | [`ListItem_Stylesheet.yaml`](../stylesheets/lists/list-item.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ListItem`

A list row: a headline, and room for more. Its look: [`ListItem_Stylesheet.yaml`](../stylesheets/lists/list-item.md).

| Parameter | | Default |
| --- | --- | --- |
| `headline` | required |  |
| `width` | required |  |

```yaml
params: [headline, width]
id: root
kind: Container
children:
  - id: headline
    kind: Text
    text:
      content: "{{ headline }}"
      typography_role: body_large
      wrap: none
      overflow: ellipsis
```

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

## Using it

In Python:

```python
from tesserae.widgets import list_, list_item

rows = list_(app.window, [list_item(app.window, name) for name in ("Inbox", "Sent", "Drafts")], width=320)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ListItem_Stylesheet.yaml, next to your views
styles:
  - id: headline
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Repeater](../guide/repeater.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
