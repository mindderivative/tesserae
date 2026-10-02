# Tabs

*Navigation*

## In Material Design 3

Tabs organise content at one level of hierarchy, with the selected tab marked by an indicator. Primary tabs
may carry an icon above the label.

## In Tesserae

A row of `TabsItem`s over a divider, one for each entry of `items`. Give an item an `icon` and it is taller.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Tabs` | Tabs: a row of destinations in one view, with the selected one marked. | [`Tabs_Stylesheet.yaml`](../stylesheets/tabs/tabs.md) |
| `component: TabsItem` | One tab: a label, and an icon if you want one, with an indicator when selected. | [`TabsItem_Stylesheet.yaml`](../stylesheets/tabs/tabs-item.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Tabs`

Tabs: a row of destinations in one view, with the selected one marked. Its look: [`Tabs_Stylesheet.yaml`](../stylesheets/tabs/tabs.md).

| Parameter | | Default |
| --- | --- | --- |
| `items` | required |  |
| `item_width` | required |  |

```yaml
params: [items, item_width]
id: root
kind: Container
children:
  - id: row
    kind: Container
    children:
      - id: item
        component: TabsItem
        with:
          width: "{{ item_width }}"
        repeat: "{{ items }}"
  - {id: divider, kind: Rect}
```

### `TabsItem`

One tab: a label, and an icon if you want one, with an indicator when selected. Its look: [`TabsItem_Stylesheet.yaml`](../stylesheets/tabs/tabs-item.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |
| `icon` | optional | `None` |
| `selected` | optional | `False` |

```yaml
params:
  - label
  - width
  - {icon: null}
  - {selected: false}
id: root
kind: Rect
children:
  - id: tab
    kind: Container
    children:
      - {id: top, kind: Rect}
      - id: content
        kind: Container
        children:
          - id: icon
            when: "{{ icon }}"
            kind: Icon
            icon:
              name: "{{ icon }}"
          - id: label
            kind: Text
            text:
              content: "{{ label }}"
              typography_role: title_small
      - {id: indicator, kind: Rect}
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: tabs
    component: Tabs
    with:
      item_width: 120
      items:
        - {label: Videos, selected: true}
        - {label: Photos}
```

In Python:

```python
from tesserae.widgets import tabs

bar = tabs(app.window, ["Videos", "Photos"], selected=0)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Tabs_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
