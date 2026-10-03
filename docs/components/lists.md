# Lists

*Containment*

## In Material Design 3

A list is a column of rows, each a headline with optional leading and trailing content and supporting text.

## In Tesserae

One fragment for the row; a list is a container of them. For a list that changes while the app runs, use a
[Repeater](../guide/repeater.md).

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

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: first
    component: ListItem
    with: {headline: Inbox, width: 320}
```

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
