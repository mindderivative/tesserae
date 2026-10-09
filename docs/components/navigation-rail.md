# Navigation rail

*Navigation*

## In Material Design 3

A navigation rail puts three to seven destinations in a narrow column beside the content, on medium and
large windows. Each is an icon in a pill with a label; the selected one's pill is filled.

## In Tesserae

Four views Tesserae ships: `NavigationRail` (the column), `NavigationRailItem` (one destination), `NavigationRailScreens` (a rail whose destinations are the
app's screens) and `NavigationRailScreen` (one such destination).

| Property | Type | Meaning |
| --- | --- | --- |
| `items` | a list | the destinations of a `NavigationRail`, each `{value, label, icon}` and optionally `{badge, disabled}` |
| `selected` | a value; two-way | the value of the chosen destination; a press (or an arrow key) writes it back |
| `expanded` | true or false | 220 pixels wide with the labels beside the icons, instead of 80 with them under |
| `alignment` | `top`, `center`, `bottom` | where the destinations sit in the column |
| `items` | a list | the destinations of a `NavigationRailScreens` (and of a `NavigationRail`, above), each `{screen, label, icon}` and optionally `{badge}` |

A destination is a 24 pixel icon in a 56 by 32 pill (`secondary_container` when it is the chosen one) over a `label_medium` label, 12 pixels from the
next, starting 44 pixels down. Children with `slot: header` (a menu button, a FAB) go above the destinations and `slot: footer` below. There is one Tab stop;
the up and down arrows move the focus and choose the destination. A screen reader hears a link named by the label, the current one marked as the page.
The screens rail follows `app.current_screen` and a press is `navigate_to(screen)`; it belongs in each screen (or in a window's shell). Not built: the
modal expanded rail, sections with headings, the pill's fade and scale as it is selected, and the destinations' `tab` role (tre has no `navigation` role).

`widget: NavigationRail` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: shell
widget: Container
style: {flex_direction: horizontal, width: 480, height: 400}
children:
  - widget: NavigationRail
    selected: "{{ page }}"
    items:
      - {value: home, label: Home, icon: home}
      - {value: search, label: Search, icon: search, badge: 3}
  - widget: NavigationRailScreens
    items:
      - {screen: Main, label: Tasks, icon: home}
      - {screen: Settings, label: Settings, icon: settings}
```

## Using it

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

- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
