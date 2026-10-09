# Dialogs

*Containment*

## In Material Design 3

A dialog interrupts to ask for a decision or give needed information. It has a headline, supporting text and
up to two actions, on a raised surface over a scrim, and blocks what is behind it.

## In Tesserae

`widget: Dialog` is a view Tesserae ships (`Dialog_View.yaml`): a modal [`Overlay`](../guide/view-language.md#overlays) holding a raised panel (28 pixel
corners, 24 of padding) with an optional icon, a headline, supporting text, your own content and text-button actions.

| Property | Type | Meaning |
| --- | --- | --- |
| `open` | true or false; two-way | whether it is showing; Escape and a press on the scrim write `false` back |
| `headline`, `text`, `icon` | text | the title, the supporting text, an icon above the headline |
| `actions` | a list | text buttons, each `{label, value}` and optionally `{variant}` |
| `result` | a value; two-way | the `value` of the action pressed; pressing one also closes the dialog |
| `dismissible` | true or false | off, only an action closes it |
| `width`, `max_height` | numbers | the panel's width, held between 280 and 560 (default 312); the content scrolls beyond `max_height` |
| `fullscreen` | true or false | the full-screen form: the panel fills the window on `surface`, with a close button, the headline and the actions in a 56 pixel bar along the top, and the content scrolling under it |

Children are the content, after the supporting text. When the content scrolls, a line shows above the actions. Actions stack when they do not fit
one row. A screen reader hears a `dialog` named by the headline (tre has no `alertdialog` role). In the full-screen form the close button writes
`false` to `open` with no result, the actions sit in the bar instead of under the content (MD3 has one confirming action there), and a line shows under
the bar once the content has scrolled; use it where the window is `compact` (`fullscreen: "{{ app.width_class == 'compact' }}"`). Not built: focusing a
form dialog's first field.

`widget: Dialog` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Dialog` | A dialog: a headline and text on a raised panel, over a scrim. | [`Dialog_Stylesheet.yaml`](../stylesheets/dialogs/dialog.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Dialog`

A dialog: a headline and text on a raised panel, over a scrim. Its look: [`Dialog_Stylesheet.yaml`](../stylesheets/dialogs/dialog.md).

| Parameter | | Default |
| --- | --- | --- |
| `headline` | required |  |
| `text` | required |  |
| `width` | required |  |
| `height` | required |  |
| `scrim_width` | required |  |
| `scrim_height` | required |  |

```yaml
params: [headline, text, width, height, scrim_width, scrim_height]
id: root
kind: Container
children:
  - id: panel
    kind: Container
    children:
      - id: headline
        kind: Text
        text:
          content: "{{ headline }}"
          typography_role: headline_small
      - id: body
        kind: Text
        text:
          content: "{{ text }}"
          typography_role: body_medium
```

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

## Using it

In Python:

```python
from tesserae.widgets import dialog

confirm = dialog(app.window, "Discard changes?", "Your edits will be lost.", 320, 200,
                 actions=[("Cancel", None), ("Discard", viewmodel.discard)])
confirm.open()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Dialog_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
