# Dialogs

*Containment*

## In Material Design 3

A dialog interrupts to ask for a decision or give needed information. It has a headline, supporting text and
up to two actions, on a raised surface over a scrim, and blocks what is behind it.

## In Tesserae

`widget: Dialog` is a view Tesserae ships (`Dialog_View.yaml`): a modal [`Overlay`](../guide/view-language.md#overlays) holding a raised panel (28 pixel
corners, 24 of padding) with an optional icon, a headline, supporting text, your own content and text-button actions.

`open` is two-way: Escape and a press on the scrim write `false` back, unless `dismissible` is off, when only an action closes it. Each of the `actions` is `{label, value}`
and optionally `{variant}` (a text button unless it says otherwise); pressing one closes the dialog and writes its `value` to `result`, which stays empty when the dialog was
dismissed. The panel is `width` wide, held between 280 and 560 pixels (312 by default), and the content scrolls beyond `max_height` (480). `fullscreen` is the full-screen
form: the panel fills the window on `surface`, with a close button, the headline and the actions in a 56 pixel bar along the top, and the content scrolling under it.

Children are the content, after the supporting text. When the content scrolls, a line shows above the actions. Actions stack when they do not fit
one row. A screen reader hears a `dialog` named by the headline (tre has no `alertdialog` role). In the full-screen form the close button writes
`false` to `open` with no result, the actions sit in the bar instead of under the content (MD3 has one confirming action there), and a line shows under
the bar once the content has scrolled; use it where the window is `compact` (`fullscreen: "{{ app.width_class == 'compact' }}"`). Not built: focusing a
form dialog's first field.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Dialog`. A file of the same name in your project replaces it.

### `Dialog`

The Material 3 dialog, basic or (`fullscreen: true`) full-screen: a modal panel over a scrim, with an optional icon, a headline, supporting text or your own content, and up to a few text button actions. `open` is two-way (Escape and a press on the scrim close it, unless `dismissible: false`); pressing an action closes it and writes the action's value to `result`, so the caller can tell which was chosen. A screen reader hears a `dialog` named by the headline (tre has no `alertdialog` role, so an alert is a `dialog` with `dismissible: false`). The content scrolls when it is taller than the dialog, and a line shows above the actions then. Children are the content: they follow the supporting text. Actions stack when they do not fit the width on one row.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `open` | `bool` | `false` | Whether it is showing. Two-way: give it a bare reference and the view writes it back. |
| `headline` | `str` |  | The title. |
| `text` | `str` |  | Supporting text. |
| `icon` | `str` |  | An icon above the headline. |
| `actions` | `list` | `[]` | Text buttons, each {label, value} and optionally {variant}. Pressing one closes the dialog and sets `result` to its value. |
| `result` | `any` |  | The value of the action last pressed; empty when it was dismissed. Two-way: give it a bare reference and the view writes it back. |
| `dismissible` | `bool` | `true` | Escape and a press on the scrim close it. Off, it is an alert dialog: only an action closes it. |
| `width` | `float` | `312` | From 280 to 560 pixels. |
| `max_height` | `float` | `480` | The content scrolls beyond this. |
| `fullscreen` | `bool` | `false` | The full-screen form: it fills the window, with a close button, the headline and the actions along the top, and the content scrolling under them. |

Children go in the default slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `panel` (Container), `bar` (Container), `close` (IconButton), `bar_title` (Text), `bar_action` (Button), `bar_line` (Divider), `icon` (Icon), `headline` (Text), `content` (ScrollView), `body` (Text), `line` (Divider), `actions` (Container), `action` (Button).

Its look is in [`Dialog_Stylesheet.yaml`](../stylesheets/dialogs/dialog.md).

## Using it

```yaml
name: files
widget: Container
style: {flex_direction: vertical, width: 480, height: 360}
children:
  - widget: Dialog
    open: "{{ confirming }}"
    result: "{{ choice }}"
    headline: Discard draft?
    text: This cannot be undone.
    icon: home
    actions:
      - {label: Cancel, value: cancel}
      - {label: Discard, value: discard}
```

## Using it in Python

```python
from tesserae.widgets import dialog

confirm = dialog(app.window, "Discard changes?", "Your edits will be lost.", 320, 200,
                 actions=[("Cancel", None), ("Discard", viewmodel.discard)])
confirm.open()
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Dialog_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Dialog
    part: panel
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
