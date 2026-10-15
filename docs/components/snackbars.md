# Snackbars

*Communication*

## In Material Design 3

A snackbar briefly tells the user about a process that has happened or will happen, at the bottom of the
window, and may offer one action. It goes away by itself.

## In Tesserae

Two views Tesserae ships: `Snackbar` (one message) and `SnackbarHost` (several, one after another).

A `Snackbar` shows while `open` is true and writes `false` back when it closes. It closes itself after `duration` milliseconds (4000 by default; 0 keeps it until it is closed),
and the pointer over it holds the time off. The `action` is a text button after the message: pressing it runs `on_action` and closes the snackbar. `closable` adds a close
button, and `on_close` is called when it closes however it closes. It is 344 to 560 pixels wide (`width`), 16 from the window's edge (`margin`), at the start or `centered`.

It is `inverse_surface` at level 3 with 4 pixel corners, 48 pixels tall (68 for two lines), over the content, not modal, and takes no focus; a screen reader hears it
as a polite alert. A `SnackbarHost` takes `messages` (`{message}` and optionally `{action, value, id, duration}`), shows the first, drops it when it closes
and shows the next; add to the list from anywhere that can write it; `chosen` is the `value` of the action pressed. An `Overlay` has a `timeout`
and an `on_dismiss` handler, which is how this is made. Not built: swipe to dismiss, and lifting above a FAB or a bottom bar.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Snackbar`. A file of the same name in your project replaces it.

### `Snackbar`

The Material 3 snackbar: a short message near the bottom of the window, over the content, that goes by itself. It is not modal, takes no focus and blocks nothing. `open` shows it (and is written false when it closes); it closes `duration` milliseconds after it opens (4000 by default; 0 keeps it up) unless the pointer is over it, when the action or the close button is pressed, and calls `on_close` then. An `action` is a text button after the message: pressing it runs `on_action`, then closes. Announced politely. `SnackbarHost` shows several one after another.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `open` | `bool` | `false` | Whether it is showing; it writes false when it closes. Two-way: give it a bare reference and the view writes it back. |
| `message` | `str` |  | What to say. |
| `action` | `str` |  | The label of a text button after the message. |
| `on_action` | `handler` |  | What the action button does. |
| `on_close` | `handler` |  | Called when it closes, however it closes. |
| `closable` | `bool` | `false` | A close button after the message. |
| `duration` | `float` | `4000` | Milliseconds before it closes itself; 0 keeps it until it is closed. |
| `margin` | `float` | `16` | The space between it and the window's edge. |
| `centered` | `bool` | `false` | In the middle of the window instead of at the start. |
| `width` | `float` | `344` | How wide it is, from 344 to 560 pixels; a message longer than fits goes onto a second line. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `bar` (Container), `message` (Text), `action` (Container), `action_text` (Text), `close` (Container), `close_icon` (Icon).

Its look is in [`Snackbar_Stylesheet.yaml`](../stylesheets/snackbars/snackbar.md).

### `SnackbarHost`

Several snackbars, one after another (Material 3 shows one at a time). `messages` is a list of {message} and optionally {action, value, id, duration}; the first shows, and when it closes it is taken off the list and the next one shows. Add to the list (`messages = messages + [{'message': 'Saved'}]`) from anywhere that can write it. The `value` of an action that was pressed goes to `chosen`. It takes no room where it is written.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `messages` | `list` | `[]` | The waiting messages, each {message} and optionally {action, value, id, duration}. The first is showing. Two-way: give it a bare reference and the view writes it back. |
| `chosen` | `any` |  | The value of the action last pressed. Two-way: give it a bare reference and the view writes it back. |
| `closable` | `bool` | `false` | A close button on each. |
| `centered` | `bool` | `false` | In the middle of the window instead of at the start. |
| `margin` | `float` | `16` | The space between a snackbar and the window's edge. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `current` (Snackbar).

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

## Using it in Python

```python
from tesserae.widgets import snackbar

bar = snackbar(app.window, "Saved", 280, action_label="Undo", on_action=viewmodel.undo)
bar.open()
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Snackbar_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Snackbar
    part: message
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
