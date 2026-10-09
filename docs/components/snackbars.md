# Snackbars

*Communication*

## In Material Design 3

A snackbar briefly tells the user about a process that has happened or will happen, at the bottom of the
window, and may offer one action. It goes away by itself.

## In Tesserae

Two views Tesserae ships: `Snackbar` (one message) and `SnackbarHost` (several, one after another).

| Property | Type | Meaning |
| --- | --- | --- |
| `open` | true or false; two-way | whether it is showing; it writes `false` when it closes |
| `message`, `action`, `closable` | text, text, true or false | the message, a text button after it, a close button |
| `on_action`, `on_close` | handlers | the action button's handler; called when it closes however it closes |
| `duration` | milliseconds | how long it stays (default 4000; 0 keeps it until it is closed); the pointer over it holds the time off |
| `width`, `margin`, `centered` | numbers, true or false | 344 to 560 wide, 16 from the window's edge, at the start or centred |

It is `inverse_surface` at level 3 with 4 pixel corners, 48 pixels tall (68 for two lines), over the content, not modal, and takes no focus; a screen reader hears it
as a polite alert. A `SnackbarHost` takes `messages` (`{message}` and optionally `{action, value, id, duration}`), shows the first, drops it when it closes
and shows the next; add to the list from anywhere that can write it; `chosen` is the `value` of the action pressed. An `Overlay` now has a `timeout`
and an `on_dismiss` handler, which is how this is made. Not built: swipe to dismiss, and lifting above a FAB or a bottom bar.

`widget: Snackbar` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Snackbar` | A snackbar: a short message about a process, at the bottom of the window. | [`Snackbar_Stylesheet.yaml`](../stylesheets/snackbars/snackbar.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Snackbar`

A snackbar: a short message about a process, at the bottom of the window. Its look: [`Snackbar_Stylesheet.yaml`](../stylesheets/snackbars/snackbar.md).

| Parameter | | Default |
| --- | --- | --- |
| `text` | required |  |
| `width` | required |  |

```yaml
params: [text, width]
id: root
kind: Container
children:
  - id: text
    kind: Text
    text:
      content: "{{ text }}"
      typography_role: body_medium
```

## Using it

```yaml
name: notes
widget: Container
style: {width: 480, height: 320}
children:
  - widget: SnackbarHost
    messages: "{{ toasts }}"
    chosen: "{{ undo }}"
  - widget: Snackbar
    open: "{{ saved }}"
    message: Note saved
    action: Undo
    on_action: undo_save
```

## Using it

In Python:

```python
from tesserae.widgets import snackbar

bar = snackbar(app.window, "Saved", 280, action_label="Undo", on_action=viewmodel.undo)
bar.open()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Snackbar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
