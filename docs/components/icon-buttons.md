# Icon buttons

*Actions*

## In Material Design 3

An icon button is an action shown as a glyph alone. Like buttons it has four emphases: standard (no
container), filled, filled tonal and outlined. It is 40dp, with a 48dp touch target.

## In Tesserae

`widget: IconButton` is a view Tesserae ships (`IconButton_View.yaml`): one widget for the four types, in five sizes and three widths. The `label`
names it for a screen reader and is its tooltip. `handlers: {on_click: ...}` on the call is what a press does.

| Property | Type | Meaning |
| --- | --- | --- |
| `icon`, `selected_icon` | an icon name | the glyph; the one shown while a toggle is on |
| `label` | text | what it does: its name and its tooltip |
| `variant` | `standard`, `filled`, `tonal`, `outlined` | the type (default `standard`) |
| `size` | `xs`, `s`, `m`, `l`, `xl` | 32, 40, 56, 96 or 136 pixels tall; the glyph is 20, 24, 24, 32 or 40 |
| `width_kind` | `narrow`, `default`, `wide` | as tall as it is, or narrower or wider |
| `shape` | `round`, `square` | a circle, or a rounded square |
| `toggle`, `selected` | true or false; `selected` is two-way | a press flips `selected`; the glyph, the colours and the shape change while it is on |
| `disabled` | true or false | dimmed, not focusable, handlers do not run |

The state layer, ripple and focus ring are the node's interaction; a pressed circle squares off. Not built: the 12% container of a disabled filled
button, and the 48 pixel touch target around a 40 pixel button.

`widget: IconButton` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: IconButtonStandard` | A standard icon button: a low-emphasis action shown as an icon alone. | [`IconButtonStandard_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-standard.md) |
| `component: IconButtonFilled` | A filled icon button: a high-emphasis action shown as an icon. | [`IconButtonFilled_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-filled.md) |
| `component: IconButtonFilledTonal` | A filled tonal icon button: a medium-emphasis action shown as an icon. | [`IconButtonFilledTonal_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-filled-tonal.md) |
| `component: IconButtonOutlined` | An outlined icon button: a medium-emphasis action shown as an icon with a border. | [`IconButtonOutlined_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-outlined.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `IconButtonStandard`, `IconButtonFilled`, `IconButtonFilledTonal`, `IconButtonOutlined`

| Parameter | | Default |
| --- | --- | --- |
| `icon` | required |  |
| `size` | required |  |
| `corner_radius` | required |  |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params: [icon, size, corner_radius]
id: root
kind: Rect
children:
  - id: icon
    kind: Icon
    icon:
      name: "{{ icon }}"
```

## Using it

```yaml
name: toolbar
widget: Container
style: {flex_direction: horizontal, gap: 8, padding: 16}
children:
  - {widget: IconButton, icon: settings, label: Settings, handlers: {on_click: open_settings}}
  - {widget: IconButton, icon: home, selected_icon: search, label: Favourite, variant: filled, toggle: true, selected: "{{ favourite }}"}
```

## Using it

In Python:

```python
from tesserae.widgets import icon_button

settings = icon_button(app.window, "settings", 40, variant="standard")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# IconButtonStandard_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
