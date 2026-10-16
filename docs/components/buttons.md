# Buttons

*Actions*

## In Material Design 3

Buttons let people take an action with one tap. Material Design 3 has five, in order of emphasis: **filled**
for a screen's one main action, **filled tonal** and **elevated** for important but secondary ones,
**outlined** for medium emphasis, and **text** for the lowest: dialogs, cards and toolbars. A button is 40dp
high and fully rounded, and its label is in the *label large* type style.

## In Tesserae

`widget: Button` is a view Tesserae ships (`Button_View.yaml` and `Button_Stylesheet.yaml`). One widget has all five types, in five sizes. It is as wide
as its label and icons, and `handlers: {on_click: ...}` on the call is what a press does; Enter or Space on a focused button does the same.

A toggle (`toggle: true`) flips `selected` on each press, and its colours and shape swap while it is on; with `flip: false` the caller decides when it flips
(a button group's buttons are made so). While `loading` a spinner takes the icon's place and the button does not respond. A disabled button fades as a whole.

The label is `label_large` at `xs` and `s`, `title_medium` at `m`, `headline_small` at `l` and `headline_large` at `xl`; the gap between the parts is 4, 8, 8, 12 and 16 pixels. Padding
at the default size is 24 pixels each side (16 on the side with an icon, or the spinner; a text button 12); `xs` has 12, `m` 24, `l` 48 and `xl` 64 whatever is in the button.
The container is a pill and, while pressed, squares off; a toggle that is
on takes the other shape. A filled or tonal button lifts to level 1 when hovered, an elevated one rests at level 1 and lifts to 2. The state layer, ripple and
focus ring are the node's interaction. The look is in the stylesheet: write a `Button_Stylesheet.yaml` in your project to change it. Not built: the
container colour at 12% for a disabled filled button (a disabled button fades as a whole).

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Button`. A file of the same name in your project replaces it.

### `Button`

The Material 3 button: filled, tonal, elevated, outlined or text, in five sizes, with a leading and a trailing icon, a toggle form, a loading form and a disabled form. It is as wide as its label and icons, unless the call gives it a width. `handlers: {on_click: save}` on the call is what it does when pressed. With `toggle: true` a press flips `selected` (two-way) and the button swaps its colours and its shape; `loading` shows a spinner in the icon's place and stops it taking presses. Colours, sizes, shapes and how it lifts are in Button_Stylesheet.yaml: to change them, give the app rules with `App(stylesheet=...)`.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The text. |
| `variant` | `filled` or `tonal` or `elevated` or `outlined` or `text` | `filled` | filled is the screen's main action; tonal and elevated are important but secondary; outlined is medium; text is the lowest emphasis. |
| `size` | `xs` or `s` or `m` or `l` or `xl` | `s` | 32, 40, 56, 96 or 136 pixels tall. |
| `shape` | `round` or `square` | `round` | A pill, or a rounded square. A toggle button swaps to the other shape while selected. |
| `icon` | `str` |  | A leading icon. |
| `trailing_icon` | `str` |  | An icon after the label. |
| `disabled` | `bool` | `false` | Dimmed, not focusable, and it does not respond. |
| `loading` | `bool` | `false` | A spinner in the icon's place; it does not respond while it shows. |
| `toggle` | `bool` | `false` | A toggle button: it has an on and an off look, and a press flips `selected`. |
| `flip` | `bool` | `true` | For a toggle: whether a press flips `selected` itself. Off, the caller decides (a group of buttons does). |
| `selected` | `bool` | `false` | For a toggle button: whether it is on. Two-way: give it a bare reference and the view writes it back. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `spinner` (CircularProgress), `icon` (Icon), `label` (Text), `trailing` (Icon).

Its look is in [`Button_Stylesheet.yaml`](../stylesheets/buttons/button.md).

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

## Using it in Python

```python
from tesserae.widgets import button

save = button(app.window, "Save", 120, 40, variant="filled", on_click=viewmodel.save)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Button_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Button
    variant: filled
    part: label
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Widget Catalog](../guide/widget-catalog.md)
- [Interaction](../guide/interaction.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
