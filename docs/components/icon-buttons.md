# Icon buttons

*Actions*

## In Material Design 3

An icon button is an action shown as a glyph alone. Like buttons it has four emphases: standard (no
container), filled, filled tonal and outlined. It is 40dp, with a 48dp touch target.

## In Tesserae

`widget: IconButton` is a view Tesserae ships (`IconButton_View.yaml`): one widget for the four types, in five sizes and three widths. The `label`
names it for a screen reader and is its tooltip. `handlers: {on_click: ...}` on the call is what a press does.

The glyph is 20, 24, 24, 32 or 40 pixels for the five sizes. `width_kind` makes it as wide as it is tall (`default`), or narrower or wider (a 40 pixel button is 32
pixels wide when `narrow` and 52 when `wide`). A toggle (`toggle: true`) flips `selected` on a press, and the `selected_icon`, the colours and the shape show while it is on. The
glyph morphs into the other over 200 ms when the two are both closed shapes or both open lines (`add` and `remove` do); other pairs, such as `play` and `pause`, switch partway through
instead. `tint` sets a standard button's icon colour to a colour role. A button with a `label` shows it as a tooltip, and without one there is no tooltip.

The state layer, ripple and focus ring are the node's interaction; a pressed circle squares off. Not built: the 12% container of a disabled filled
button, and the 48 pixel touch target around a 40 pixel button.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: IconButton`. A file of the same name in your project replaces it.

### `IconButton`

The Material 3 icon button: standard, filled, tonal or outlined, in five sizes and three widths, round or square, with a toggle form that swaps its icon. `label` is required in spirit: it names the button for a screen reader and is its tooltip, since an icon has no text. `handlers: {on_click: save}` on the call is what a press does. A toggle flips `selected` (two-way, or held by the button when nothing is bound). Colours, sizes and shapes are in IconButton_Stylesheet.yaml.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `icon` | `str` |  | The icon. |
| `selected_icon` | `str` |  | For a toggle: the icon while it is on (the same icon when empty). |
| `label` | `str` |  | What it does: its accessible name and its tooltip. |
| `variant` | `standard` or `filled` or `tonal` or `outlined` | `standard` | standard has no container; filled is the strongest; tonal is softer; outlined has a border. |
| `size` | `xs` or `s` or `m` or `l` or `xl` | `s` | 32, 40, 56, 96 or 136 pixels tall. |
| `width_kind` | `narrow` or `default` or `wide` | `default` | narrow, as tall as it is, or wide. |
| `shape` | `round` or `square` | `round` | A circle, or a rounded square. A toggle swaps to the other shape while selected. |
| `disabled` | `bool` | `false` | Dimmed, not focusable, and it does not respond. |
| `toggle` | `bool` | `false` | A press flips `selected`. |
| `selected` | `bool` | `false` | For a toggle: whether it is on. Two-way: give it a bare reference and the view writes it back. |
| `tint` | `str` |  | A standard button's icon colour, a colour role such as on_primary_container (on_surface_variant when empty). |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `icon` (Icon).

Its look is in [`IconButton_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button.md).

## Using it

```yaml
name: toolbar
widget: Container
style: {flex_direction: horizontal, gap: 8, padding: 16}
children:
  - {widget: IconButton, icon: settings, label: Settings, handlers: {on_click: open_settings}}
  - {widget: IconButton, icon: home, selected_icon: search, label: Favourite, variant: filled, toggle: true, selected: "{{ favourite }}"}
```

## Using it in Python

```python
from tesserae.widgets import icon_button

settings = icon_button(app.window, "settings", 40, variant="standard")
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# IconButton_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: IconButton
    variant: standard
    part: icon
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
