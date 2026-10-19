# Tabs

*Navigation*

## In Material Design 3

Tabs organise content at one level of hierarchy, with the selected tab marked by an indicator. Primary tabs
may carry an icon above the label.

## In Tesserae

`widget: Tabs` is a view Tesserae ships (`Tabs_View.yaml`): a row of equal tabs over a divider, with an indicator under the chosen tab that
slides to the next one.

The `tabs` are `{value, label}` and optionally `{icon, badge}`; an expression follows its Signals. `selected` is the value of the chosen tab, and a press or an arrow key writes it
back. With `variant: primary` (the default) the indicator is 3 pixels tall, rounded on top, and 12 pixels in from each side of the tab; with `secondary` it is 2 pixels tall across
the whole tab. Every tab is `tab_width` wide (120 by default).

The bar is 48 pixels tall, or 64 when a primary bar has an icon. The chosen tab's label and icon are `primary`, the others `on_surface_variant`. The bar
is a `tablist` with one Tab stop; the arrow keys, Home and End move the focus and choose the tab. The panel each tab shows is yours: put an
`if: "selected == 'trips'"` on it. Not built: a bar that scrolls when the tabs do not fit.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Tabs`. A file of the same name in your project replaces it.

### `Tabs`

The Material 3 tab bar: a row of tabs over a divider, an indicator under the selected one that slides to the next. `tabs` is a list of {value, label, icon, badge}; `selected` is the chosen value and a press writes it back. `variant: primary` (48 tall, 64 with icons, a 3 dp indicator as wide as the label's share of the tab) or `secondary` (48 tall, a 2 dp indicator across the whole tab). The tabs are `tab_width` wide each: a fixed bar. Arrow keys move the focus along the bar and choose the tab (one Tab stop); the panel each tab shows is yours to switch on `selected`.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `tabs` | `list` | `[]` | The tabs, each {value, label} and optionally {icon, badge}. |
| `selected` | `any` |  | The value of the chosen tab; a press writes it back. Two-way: give it a bare reference and the view writes it back. |
| `variant` | `primary` or `secondary` | `primary` | primary has a short rounded indicator; secondary one across the tab. |
| `tab_width` | `float` | `120` | How wide each tab is. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `bar` (Container), `tab` (Container), `badged` (Badge), `badged_icon` (Icon), `icon` (Icon), `label` (Text), `indicator` (Container), `divider` (Divider).

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

## Using it in Python

```python
from tesserae.widgets import tabs

bar = tabs(app.window, ["Videos", "Photos"], selected=0)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
