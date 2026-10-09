# Tabs

*Navigation*

## In Material Design 3

Tabs organise content at one level of hierarchy, with the selected tab marked by an indicator. Primary tabs
may carry an icon above the label.

## In Tesserae

`widget: Tabs` is a view Tesserae ships (`Tabs_View.yaml`): a row of equal tabs over a divider, with an indicator under the chosen tab that
slides to the next one.

| Property | Type | Meaning |
| --- | --- | --- |
| `tabs` | a list | the tabs, each `{value, label}` and optionally `{icon, badge}`; an expression follows its Signals |
| `selected` | a value; two-way | the chosen tab; a press, or an arrow key, writes it back |
| `variant` | `primary` or `secondary` | primary: a 3 pixel rounded indicator as wide as the label's share of the tab; secondary: 2 pixels across the whole tab |
| `tab_width` | a number | how wide each tab is (default 120) |

The bar is 48 pixels tall, or 64 when a primary bar has an icon. The chosen tab's label and icon are `primary`, the others `on_surface_variant`. The bar
is a `tablist` with one Tab stop; the arrow keys, Home and End move the focus and choose the tab. The panel each tab shows is yours: put an
`if: "selected == 'trips'"` on it. Not built: a bar that scrolls when the tabs do not fit (the engine's scroll view scrolls only vertically).

`widget: Tabs` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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
              wrap: none
      - {id: indicator, kind: Rect}
```

## Using it

```yaml
name: trips
widget: Container
style: {flex_direction: vertical, width: 360, height: 160}
children:
  - widget: Tabs
    selected: "{{ tab }}"
    tabs:
      - {value: flights, label: Flights, icon: home}
      - {value: trips, label: Trips, icon: search, badge: 3}
      - {value: explore, label: Explore, icon: menu}
```

## Using it

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
