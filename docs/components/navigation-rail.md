# Navigation rail

*Navigation*

## In Material Design 3

A navigation rail puts three to seven destinations in a narrow column beside the content, on medium and
large windows. Each is an icon in a pill with a label; the selected one's pill is filled.

## In Tesserae

Four views Tesserae ships: `NavigationRail` (the column), `NavigationRailItem` (one destination), `NavigationRailScreens` (a rail whose destinations are the
app's screens) and `NavigationRailScreen` (one such destination).

The `items` of a `NavigationRail` are `{value, label, icon}` and optionally `{badge, disabled}` (`badge: true` is a dot), and `selected` is the value of the chosen one: a press, or an
arrow key, writes it back. Those of a `NavigationRailScreens` are `{screen, label, icon}` and optionally `{badge}`. The rail is 80 pixels wide with the labels under the icons, or 220
with `expanded: true` and the labels beside them; `alignment` puts the destinations at the `top` (the default), `center` or `bottom` of the column, and `frosted: true` makes the
surface translucent and blurred.

A destination is a 24 pixel icon in a 56 by 32 pill (`secondary_container` when it is the chosen one) over a `label_medium` label, 12 pixels from the
next, starting 44 pixels down. Children with `slot: header` (a menu button, a FAB) go above the destinations and `slot: footer` below. There is one Tab stop;
the up and down arrows move the focus and choose the destination. A screen reader hears a link named by the label, the current one marked as the page.
The screens rail follows `app.current_screen` and a press is `navigate_to(screen)`; it belongs in each screen (or in a window's shell). Not built: the
modal expanded rail, sections with headings, the pill growing as it is selected (it fades in), and a `navigation` role for the rail (tre has none, so it is a `group` named Navigation).

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: NavigationRail`. A file of the same name in your project replaces it.

### `NavigationRail`

The Material 3 navigation rail: a column of 3 to 7 destinations, 80 pixels wide (220 when `expanded`, with the labels beside the icons). `items` is a list of {value, label, icon, badge}; `selected` is the value of the chosen one and a press writes it back. A `header` slot above the items holds a menu button or a FAB (children with `slot: header`), a `footer` slot below them. `alignment` groups the destinations at the top (the default), centre or bottom. One Tab stop; the up and down arrows move the focus and choose the destination.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `items` | `list` | `[]` | The destinations, each {value, label, icon} and optionally {badge, disabled}. |
| `selected` | `any` |  | The value of the chosen destination; a press writes it back. Two-way: give it a bare reference and the view writes it back. |
| `expanded` | `bool` | `false` | 220 pixels wide, with the labels beside the icons. |
| `alignment` | `top` or `center` or `bottom` | `top` | Where the destinations sit in the column. |

Children go in the `header` slot, the `footer` slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `destinations` (Container), `item` (NavigationRailItem).

Its look is in [`NavigationRail_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail.md).

### `NavigationRailItem`

One destination of a navigation rail: an icon in a 56 by 32 pill with its label under it (or, in an expanded rail, a 56 high pill with the label beside the icon). A selected item has a `secondary_container` pill; a `badge` sits on the icon. A screen reader hears a link named by the label, current when it is selected. `handlers: {on_click: ...}` on the call is what a press does.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `icon` | `str` |  | The icon. |
| `label` | `str` |  | The destination's name. |
| `selected` | `bool` | `false` | Whether this is where the user is. |
| `badge` | `any` |  | A count or text on the icon; empty for none, and `true` for a dot. |
| `expanded` | `bool` | `false` | The label beside the icon, as in an expanded rail. |
| `disabled` | `bool` | `false` | Dimmed and not pressable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `pill` (Container), `badged` (Badge), `badged_icon` (Icon), `icon` (Icon), `inline_label` (Text), `label` (Text).

Its look is in [`NavigationRailItem_Stylesheet.yaml`](../stylesheets/navigation-rail/navigation-rail-item.md).

### `NavigationRailScreens`

A navigation rail whose destinations are the app's screens: `items` is a list of {screen, label, icon} and optionally {badge}. The destination of the screen showing is selected, and pressing one navigates to its screen. The up and down arrows move the focus along the rail.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `items` | `list` | `[]` | The destinations, each {screen, label, icon} and optionally {badge}. |
| `expanded` | `bool` | `false` | 220 pixels wide, with the labels beside the icons. |
| `alignment` | `top` or `center` or `bottom` | `top` | Where the destinations sit in the column. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `item` (NavigationRailScreen).

### `NavigationRailScreen`

One destination of a navigation rail that goes to a screen of the app (Tesserae's, not Material 3's): a `NavigationRailItem` that is selected while its `screen` is the app's current one, and whose press is `navigate_to(screen)`. The view needs an App, which is what holds the screens.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `screen` | `str` |  | The name of the screen it goes to. |
| `label` | `str` |  | The destination's name. |
| `icon` | `str` |  | The icon. |
| `badge` | `any` |  | A count or text on the icon. |
| `expanded` | `bool` | `false` | The label beside the icon. |

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

## Using it in Python

```python
from tesserae.widgets import navigation_rail

rail = navigation_rail(app.window, ["Home", "Search"], ["home", "search"], selected=0)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# NavigationRail_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: NavigationRail
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Effects](../guide/effects.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
