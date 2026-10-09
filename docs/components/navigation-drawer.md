# Navigation drawer

*Navigation*

## In Material Design 3

A navigation drawer holds more destinations than a rail, as a vertical list of icon-and-label items. It can
be permanent (standard) or slide over the content (modal).

## In Tesserae

Views Tesserae ships: `NavigationDrawer` (standard, beside the content), `NavigationDrawerModal` (over a scrim), `NavigationDrawerScreens` (the app's screens), and
`NavigationDrawerItem` (one destination) and `NavigationDrawerPanel` (the inside the first two share).

| Property | Type | Meaning |
| --- | --- | --- |
| `items` | a list | rows: `{value, label, icon}` and optionally `{badge, disabled}`; `{heading: Text}`; `{divider: true}`. For `NavigationDrawerScreens`, `{screen, label, icon}` |
| `selected` | a value; two-way | the chosen destination; a press (or an arrow key) writes it back |
| `open` | true or false; two-way | standard: whether it takes its room (the width eases, which is how it collapses); modal: whether it is showing |
| `width` | a number | held between 256 and 360 pixels (default 360) |

A destination is a 56 pixel pill with 28 pixel corners, a 24 pixel icon, a `label_large` label and a badge at the end; the chosen one is `secondary_container`.
Children with `slot: header` and `slot: footer` go above and below the destinations, which scroll when there are too many. A modal drawer is
`surface_container_low` at level 1 with 16 pixel corners on the right; a press on a destination closes it, as do Escape and a press on the scrim. A screen reader hears
a link per destination, the current one marked as the page. Not built: the modal drawer sliding in (an overlay is where its style says when first drawn), and a
standard drawer that becomes a rail by itself when the window narrows.

`widget: NavigationDrawer` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: shell
widget: Container
style: {flex_direction: horizontal, width: 720, height: 480}
children:
  - widget: NavigationDrawer
    selected: "{{ page }}"
    items:
      - {value: inbox, label: Inbox, icon: home, badge: 24}
      - {value: sent, label: Sent, icon: send}
      - {divider: true}
      - {heading: Labels}
      - {value: work, label: Work, icon: tag}
  - widget: NavigationDrawerScreens
    items: [{screen: Main, label: Tasks, icon: home}, {screen: Settings, label: Settings, icon: cog}]
```

## Using it

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
