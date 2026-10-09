# Buttons

*Actions*

## In Material Design 3

Buttons let people take an action with one tap. Material Design 3 has five, in order of emphasis: **filled**
for a screen's one main action, **filled tonal** and **elevated** for important but secondary ones,
**outlined** for medium emphasis, and **text** for the lowest: dialogs, cards and toolbars. A button is 40dp
high and fully rounded, and its label is in the *label large* type style.

## In Tesserae

`widget: Button` is a view Tesserae ships (`Button_View.yaml` and `Button_Stylesheet.yaml`). One widget has all five types, in five sizes. It is as wide
as its label and icons, and `handlers: {on_click: ...}` on the call is what a press does.

| Property | Type | Meaning |
| --- | --- | --- |
| `label` | text | the text |
| `variant` | `filled`, `tonal`, `elevated`, `outlined`, `text` | the type (default `filled`) |
| `size` | `xs`, `s`, `m`, `l`, `xl` | 32, 40, 56, 96 or 136 pixels tall (default `s`) |
| `shape` | `round`, `square` | a pill, or a rounded square |
| `icon`, `trailing_icon` | an icon name | before and after the label |
| `disabled` | true or false | dimmed, not focusable, handlers do not run |
| `loading` | true or false | a spinner in the icon's place; does not respond |
| `toggle`, `selected` | true or false; `selected` is two-way | a press flips `selected`; the colours and the shape swap while it is on |
| `flip` | true or false | for a toggle: off, a press does not flip `selected` and the caller decides (a button group's buttons) |

Padding is 24 pixels each side (16 on the side with an icon; a text button 12). The container is a pill and, while pressed, squares off; a toggle that is
on takes the other shape. A filled or tonal button lifts to level 1 when hovered, an elevated one rests at level 1 and lifts to 2. The state layer, ripple and
focus ring are the node's interaction. The look is in the stylesheet: write a `Button_Stylesheet.yaml` in your project to change it. Not built: the
container colour at 12% for a disabled filled button (a disabled button fades as a whole).

`widget: Button` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ButtonFilled` | A filled button: the highest-emphasis button, for a screen's main action. | [`ButtonFilled_Stylesheet.yaml`](../stylesheets/buttons/button-filled.md) |
| `component: ButtonFilledTonal` | A filled tonal button: a medium-emphasis button in the secondary container colour. | [`ButtonFilledTonal_Stylesheet.yaml`](../stylesheets/buttons/button-filled-tonal.md) |
| `component: ButtonElevated` | An elevated button: a tinted surface with a shadow, for emphasis on a busy background. | [`ButtonElevated_Stylesheet.yaml`](../stylesheets/buttons/button-elevated.md) |
| `component: ButtonOutlined` | An outlined button: a medium-emphasis button with a border and no fill. | [`ButtonOutlined_Stylesheet.yaml`](../stylesheets/buttons/button-outlined.md) |
| `component: ButtonText` | A text button: the lowest-emphasis button, for dialogs and cards. | [`ButtonText_Stylesheet.yaml`](../stylesheets/buttons/button-text.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ButtonFilled`, `ButtonFilledTonal`, `ButtonElevated`, `ButtonOutlined`, `ButtonText`

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |
| `height` | required |  |
| `corner_radius` | required |  |

These 5 have one structure; only their stylesheets, above, differ.

```yaml
params: [label, width, height, corner_radius]
id: root
kind: Rect
children:
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
      text_align: center
```

## Using it

```yaml
name: actions
widget: Container
style: {flex_direction: horizontal, gap: 12, padding: 16, align_content: center}
children:
  - {widget: Button, label: Save, icon: home, handlers: {on_click: save}}
  - {widget: Button, label: Draft, variant: outlined}
  - {widget: Button, label: Mute, variant: tonal, toggle: true, selected: "{{ muted }}"}
  - {widget: Button, label: Sync, variant: text, loading: "{{ syncing }}"}
```

## Using it

In Python:

```python
from tesserae.widgets import button

save = button(app.window, "Save", 120, 40, variant="filled", on_click=viewmodel.save)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ButtonFilled_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Widget Catalog](../guide/widget-catalog.md)
- [Interaction](../guide/interaction.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
