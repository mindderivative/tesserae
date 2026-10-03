# Navigation drawer

*Navigation*

## In Material Design 3

A navigation drawer holds more destinations than a rail, as a vertical list of icon-and-label items. It can
be permanent (standard) or slide over the content (modal).

## In Tesserae

A column of `NavigationDrawerItem`s. `tesserae.overlays.NavigationDrawer` shows the modal form.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: NavigationDrawer` | A navigation drawer: a vertical list of destinations. | [`NavigationDrawer_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer.md) |
| `component: NavigationDrawerItem` | One destination in a navigation drawer: an icon and a label, highlighted when selected. | [`NavigationDrawerItem_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer-item.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `NavigationDrawer`

A navigation drawer: a vertical list of destinations. Its look: [`NavigationDrawer_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer.md).

| Parameter | | Default |
| --- | --- | --- |
| `items` | required |  |
| `width` | required |  |
| `item_width` | required |  |

```yaml
params: [items, width, item_width]
id: root
kind: Container
children:
  - id: item
    component: NavigationDrawerItem
    with:
      width: "{{ item_width }}"
    repeat: "{{ items }}"
```

### `NavigationDrawerItem`

One destination in a navigation drawer: an icon and a label, highlighted when selected. Its look: [`NavigationDrawerItem_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer-item.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `icon` | required |  |
| `width` | required |  |
| `selected` | optional | `False` |

```yaml
params:
  - label
  - icon
  - width
  - {selected: false}
id: root
kind: Rect
children:
  - id: icon
    kind: Icon
    icon:
      name: "{{ icon }}"
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
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
  - id: drawer
    component: NavigationDrawer
    with:
      width: 280
      item_width: 256
      items:
        - {label: Inbox, icon: home, selected: true}
        - {label: Search, icon: search}
```

In Python:

```python
from tesserae.widgets import navigation_drawer

drawer = navigation_drawer(app.window, ["Inbox", "Search"], ["home", "search"], selected=0)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# NavigationDrawer_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
