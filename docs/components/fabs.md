# Floating action buttons

*Actions*

## In Material Design 3

A floating action button (FAB) is the screen's most important action, as an icon in a prominent container.
There are four colours (primary, secondary, tertiary and surface) and three sizes: small (40dp), the
default (56dp) and large (96dp).

## In Tesserae

`widget: Fab` is a view Tesserae ships (`Fab_View.yaml`): one widget for the four colours and three sizes, and for the extended form too (give it a
`label`).

The glyph is 24 pixels, 36 on a large FAB, and the corners are 12, 16 and 28 pixels for the three sizes. A collapsed extended FAB shows only its icon, and its
label becomes its tooltip; the label is also the accessible name.

It rests at elevation level 3, lifts to 4 when hovered and settles to 3 when pressed. To collapse as a list scrolls down and extend as it scrolls up, bind
`collapsed: "{{ way == 'down' }}"` to the `scroll_direction` of the list. Not built: easing the collapse and the extend (the width goes between a number and `auto`,
which the engine does not animate, so the FAB changes shape at once), and the FAB menu.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Fab`. A file of the same name in your project replaces it.

### `Fab`

The Material 3 floating action button, and its extended form: an icon in a prominent container, with a label beside it when `label` is given. In four colours (`variant`: primary, secondary, tertiary, surface) and three sizes (`size`: small 40, medium 56, large 96). An extended FAB collapses to just its icon when `collapsed` is true; bind that to the way a list scrolls (`collapsed: "{{ way == 'down' }}"`) for the usual behaviour. `label` names it for a screen reader and, when it is only an icon, is its tooltip. `handlers: {on_click: add}` on the call is what a press does. Colours, sizes and how it lifts are in Fab_Stylesheet.yaml.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `icon` | `str` |  | The icon. |
| `label` | `str` |  | The text beside the icon (an extended FAB); also its accessible name. |
| `variant` | `primary` or `secondary` or `tertiary` or `surface` | `primary` | The container colour. |
| `size` | `small` or `medium` or `large` | `medium` | 40, 56 or 96 pixels. An extended FAB is 56 tall. |
| `collapsed` | `bool` | `false` | An extended FAB shows only its icon. |
| `disabled` | `bool` | `false` | Dimmed, not focusable, and it does not respond. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `icon` (Icon), `label` (Text).

Its look is in [`Fab_Stylesheet.yaml`](../stylesheets/fabs/fab.md).

## Using it

```yaml
name: inbox
widget: Container
style: {flex_direction: vertical, width: 360, height: 480}
children:
  - widget: ScrollView
    scroll_direction: "{{ way }}"
    style: {height: 400}
    children: [{widget: Text, text: Messages, typography_role: body_medium, style: {foreground: on_surface}}]
  - widget: Fab
    icon: add
    label: Compose
    collapsed: "{{ way == 'down' }}"
    handlers: {on_click: compose}
```

## Using it in Python

```python
from tesserae.widgets import fab

add = fab(app.window, "add", size="default", variant="primary")
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Fab_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Fab
    variant: primary
    part: icon
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
