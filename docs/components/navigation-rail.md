# Navigation rail

*Navigation*

## In Material Design 3

A navigation rail puts three to seven destinations in a narrow column beside the content, on medium and
large windows. Each is an icon in a pill with a label; the selected one's pill is filled.

## In Tesserae

The rail is a column of `NavigationRailItem`s, one for each entry of `items`. A [shell file](../guide/app-shell.md)'s
`navigation:` builds one for you.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: NavigationRail` | A navigation rail: a narrow column of destinations beside the content. | [`NavigationRail_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail.md) |
| `component: NavigationRailItem` | One destination in a navigation rail: an icon in a pill, with a label under it. | [`NavigationRailItem_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-item.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `NavigationRail`

A navigation rail: a narrow column of destinations beside the content. Its look: [`NavigationRail_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail.md).

| Parameter | | Default |
| --- | --- | --- |
| `items` | required |  |

```yaml
params: [items]
id: root
kind: Container
children:
  - id: item
    component: NavigationRailItem
    repeat: "{{ items }}"
```

### `NavigationRailItem`

One destination in a navigation rail: an icon in a pill, with a label under it. Its look: [`NavigationRailItem_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-item.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `icon` | required |  |
| `selected` | optional | `False` |

```yaml
params:
  - label
  - icon
  - {selected: false}
id: root
kind: Container
children:
  - id: pill
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
      typography_role: label_medium
      wrap: none
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: rail
    component: NavigationRail
    with:
      items:
        - {label: Home, icon: home, selected: true}
        - {label: Search, icon: search}
```

In Python:

```python
from tesserae.widgets import navigation_rail

rail = navigation_rail(app.window, ["Home", "Search"], ["home", "search"], selected=0)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# NavigationRail_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [App Shell](../guide/app-shell.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
