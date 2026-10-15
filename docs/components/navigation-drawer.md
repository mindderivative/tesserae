# Navigation drawer

*Navigation*

## In Material Design 3

A navigation drawer holds more destinations than a rail, as a vertical list of icon-and-label items. It can
be permanent (standard) or slide over the content (modal).

## In Tesserae

Views Tesserae ships: `NavigationDrawer` (standard, beside the content), `NavigationDrawerModal` (over a scrim), `NavigationDrawerScreens` (the app's screens), and
`NavigationDrawerItem` (one destination) and `NavigationDrawerPanel` (the inside the first two share).

The `items` are rows: `{value, label, icon}` and optionally `{badge, disabled}`, `{heading: Text}` for a section's title, and `{divider: true}` for a line (for
`NavigationDrawerScreens`, `{screen, label, icon}` in place of `value`). `selected` is the chosen destination, and a press or an arrow key writes it back. `open` is two-way: on a
standard drawer it says whether the drawer takes its room (the width eases, which is how it collapses), on a modal one whether it is showing. The drawer is `width` wide, held between
256 and 360 pixels (360 by default). `frosted: true` makes the surface translucent and blurred.

A destination is a 56 pixel pill with 28 pixel corners, a 24 pixel icon, a `label_large` label and a badge at the end; the chosen one is `secondary_container`.
Children with `slot: header` and `slot: footer` go above and below the destinations, which scroll when there are too many. A modal drawer is
`surface_container_low` at level 1 with 16 pixel corners on the right; a press on a destination closes it, as do Escape and a press on the scrim. A screen reader hears
a link per destination, the current one marked as the page. Not built: the modal drawer sliding in (an overlay is where its style says when first drawn), and a
standard drawer that becomes a rail by itself when the window narrows.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: NavigationDrawer`. A file of the same name in your project replaces it.

### `NavigationDrawer`

The Material 3 standard navigation drawer: a permanent column of destinations beside the content, 360 pixels wide (256 to 360), a `surface` column. While `open` it takes its width from the content and when it is closed it takes none (the width eases): that is how it collapses, and a rail can take its place. Children with `slot: header` and `slot: footer` go above and below the destinations. See `NavigationDrawerPanel` for the items and the keyboard.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `open` | `bool` | `true` | Whether the drawer takes its room. Two-way: give it a bare reference and the view writes it back. |
| `items` | `list` | `[]` | The rows: {value, label, icon} and optionally {badge, disabled}; {heading: Text}; {divider: true}. |
| `selected` | `any` |  | The value of the chosen destination. Two-way: give it a bare reference and the view writes it back. |
| `width` | `float` | `360` | From 256 to 360 pixels. |

Children go in the `header` slot, the `footer` slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `panel` (NavigationDrawerPanel).

Its look is in [`NavigationDrawer_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer.md).

### `NavigationDrawerItem`

One destination of a navigation drawer (Material 3): a 56 pixel tall pill with a 24 pixel icon, a `label_large` label and, at the end, a badge (a count or short text). The selected one is `secondary_container`. A screen reader hears a link named by the label, current when it is selected. `handlers: {on_click: ...}` on the call is what a press does.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The destination's name. |
| `icon` | `str` |  | The icon. |
| `badge` | `any` |  | A count or short text at the end; empty for none. |
| `selected` | `bool` | `false` | Whether this is where the user is. |
| `disabled` | `bool` | `false` | Dimmed and not pressable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `icon` (Icon), `label` (Text), `filler` (Container), `badge` (Text).

Its look is in [`NavigationDrawerItem_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer-item.md).

### `NavigationDrawerModal`

The Material 3 modal navigation drawer: the same destinations, over the content on a scrim from the start edge, `surface_container_low` at level 1 with 16 pixel corners on the side that opens. Pressing a destination closes it (and writes the choice); Escape and a press on the scrim close it too, writing false to `open`, and focus goes back to where it was. A menu button in the calling view opens it by writing `open`.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `open` | `bool` | `false` | Whether the drawer is showing. Two-way: give it a bare reference and the view writes it back. |
| `items` | `list` | `[]` | The rows: {value, label, icon} and optionally {badge, disabled}; {heading: Text}; {divider: true}. |
| `selected` | `any` |  | The value of the chosen destination. Two-way: give it a bare reference and the view writes it back. |
| `width` | `float` | `360` | From 256 to 360 pixels. |

Children go in the `header` slot, the `footer` slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `sheet` (Container), `panel` (NavigationDrawerPanel).

Its look is in [`NavigationDrawerModal_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer-modal.md).

### `NavigationDrawerPanel`

The inside of a navigation drawer, which `NavigationDrawer` (standard) and `NavigationDrawerModal` both put in a sheet: a header slot, the destinations in a column that scrolls when there are more than fit, and a footer slot. `items` is a list of {value, label, icon} and optionally {badge, disabled}; a {heading: Text} is a section's title and a {divider: true} a line. `selected` is the value of the chosen one and a press writes it back. One Tab stop on the current destination; the up and down arrows move the focus and choose it.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `items` | `list` | `[]` | The rows: {value, label, icon} and optionally {badge, disabled}; {heading: Text}; {divider: true}. |
| `selected` | `any` |  | The value of the chosen destination. Two-way: give it a bare reference and the view writes it back. |
| `on_pick` | `handler` |  | Called after a destination has been pressed (a modal drawer closes itself with it). |
| `width` | `float` | `360` | From 256 to 360 pixels. |

Children go in the `header` slot, the `footer` slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `list` (ScrollView), `row` (Container), `divider` (Divider), `heading` (Text), `item` (NavigationDrawerItem).

Its look is in [`NavigationDrawerPanel_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer-panel.md).

### `NavigationDrawerScreens`

A standard navigation drawer whose destinations are the app's screens: `items` is a list of {screen, label, icon} and optionally {badge}, with {heading: Text} and {divider: true} rows between them. The destination of the screen showing is selected, and pressing one navigates to its screen. It belongs in each screen (or in a window's shell).

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `items` | `list` | `[]` | The rows: {screen, label, icon} and optionally {badge}; {heading: Text}; {divider: true}. |
| `width` | `float` | `360` | From 256 to 360 pixels. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `row` (Container), `divider` (Divider), `heading` (Text), `item` (NavigationDrawerItem).

Its look is in [`NavigationDrawerScreens_Stylesheet.yaml`](../stylesheets/navigation-drawer/navigation-drawer-screens.md).

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

## Using it in Python

```python
from tesserae.widgets import navigation_drawer

drawer = navigation_drawer(app.window, ["Inbox", "Search"], ["home", "search"], selected=0)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# NavigationDrawer_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: NavigationDrawer
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Effects](../guide/effects.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
