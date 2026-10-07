# Navigation rail

*Navigation*

## In Material Design 3

A navigation rail puts three to seven destinations in a narrow column beside the content, on medium and
large windows. Each is an icon in a pill with a label; the selected one's pill is filled.

## In Tesserae

The rail is a column of `NavigationRailItem`s, one for each entry of `items`. `NavigationRailScreens` is the same
rail whose destinations go to screens of the app: each entry of `items` has a `screen`, choosing one is
`navigate.<screen>`, and the destination is filled while that screen is the app's current one (a Window view's routed
views are the screens). A [shell file](../guide/app-shell.md)'s `navigation:` builds a rail for you.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: NavigationRail` | A navigation rail: a narrow column of destinations beside the content. | [`NavigationRail_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail.md) |
| `component: NavigationRailItem` | One destination in a navigation rail: an icon in a pill, with a label under it. | [`NavigationRailItem_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-item.md) |
| `component: NavigationRailScreens` | A navigation rail whose destinations go to screens of the app: a narrow column of `NavigationRailScreen`s. | [`NavigationRailScreens_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-screens.md) |
| `component: NavigationRailScreen` | One destination in a navigation rail that goes to a screen of the app: an icon in a pill, with a label under it. Choosing | [`NavigationRailScreen_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-screen.md) |

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

### `NavigationRailScreens`

A navigation rail whose destinations go to screens of the app: a narrow column of `NavigationRailScreen`s. Its look: [`NavigationRailScreens_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-screens.md).

| Parameter | | Default |
| --- | --- | --- |
| `items` | required |  |

```yaml
params: [items]
id: root
kind: Container
children:
  - id: item
    component: NavigationRailScreen
    repeat: "{{ items }}"
```

### `NavigationRailScreen`

One destination in a navigation rail that goes to a screen of the app: an icon in a pill, with a label under it. Choosing Its look: [`NavigationRailScreen_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-screen.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `icon` | required |  |
| `screen` | required |  |

```yaml
params:
  - label
  - icon
  - screen
id: root
kind: Container
handlers:
  on_click: "navigate.{{ screen }}"
children:
  - id: pill
    kind: Rect
    bindings:
      background: "{{ app.current_screen.get() == '{{ screen }}' and 'secondary_container' or 'transparent' }}"
    children:
      - id: icon
        kind: Icon
        icon:
          name: "{{ icon }}"
        bindings:
          foreground: "{{ app.current_screen.get() == '{{ screen }}' and 'on_secondary_container' or 'on_surface_variant' }}"
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_medium
      wrap: none
    bindings:
      foreground: "{{ app.current_screen.get() == '{{ screen }}' and 'on_surface' or 'on_surface_variant' }}"
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
  # in a window view, a rail that navigates and follows the current screen:
  - id: nav
    component: NavigationRailScreens
    with:
      items:
        - {label: Tasks, icon: home, screen: Main}
        - {label: Settings, icon: settings, screen: Settings}
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
