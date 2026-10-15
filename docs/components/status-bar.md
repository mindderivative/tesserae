# Status bar

*Beyond MD3*

## In Material Design 3

Material Design 3 has no status bar. A desktop app often wants one, so this is a thin strip in MD3's
surface and *label* style.

## In Tesserae

`widget: StatusBar` is a view Tesserae ships (`StatusBar_View.yaml`): a 24 pixel `surface_container` strip as wide as the place it is put in, with
`label_small` text in `on_surface_variant`.

Each of `items` is `{text}` and optionally `{icon, side, value, tooltip}`; `side` is `start` (the default), `center` or `end`. `text` (a string) is a shorthand for one message
at the start, and `width` sets the bar's width instead of the place it is put in. `progress` (0 to 1) shows a 4 pixel determinate indicator along the top edge, and `busy`
one with no end. `clicked` is two-way: the `value` of the item last pressed.

An item with a `value` is a button: it has a state layer, a tooltip if it has one, and pressing it sets `clicked`. The centre section is centred on the
bar whatever the sides hold. The bar is announced politely when its items change. Not built: items that can be dragged or hidden when the window is
narrow.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: StatusBar`. A file of the same name in your project replaces it.

### `StatusBar`

A status bar (a desktop convention, not Material 3): a thin strip at the bottom of a window with short items on its left, centre and right. `items` is a list of {text} and optionally {icon, side, value, tooltip}: `side` is start (the default), center or end; an item with a `value` can be pressed, and pressing it sets `clicked` to the value; `tooltip` explains it. `progress` (0 to 1) or `busy` shows a 4 pixel indicator along the top edge. The bar is announced politely when its text changes.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `text` | `str` |  | One message at the start, for a bar that only says one thing; the same as a first item {text}. |
| `width` | `any` |  | The bar's width; the width of its place when not given. |
| `items` | `list` | `[]` | The items, each {text} and optionally {icon, side, value, tooltip}. |
| `progress` | `any` |  | 0 to 1: a determinate indicator along the top edge. Empty shows none. |
| `busy` | `bool` | `false` | An indicator with no end along the top edge. |
| `clicked` | `any` |  | The value of the item last pressed. Two-way: give it a bare reference and the view writes it back. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `section` (Container), `note` (Container), `note_icon` (Icon), `note_text` (Text), `item` (Container), `icon` (Icon), `text` (Text), `edge` (Container), `bar` (LinearProgress).

Its look is in [`StatusBar_Stylesheet.yaml`](../stylesheets/status-bar/status-bar.md).

## Using it

```yaml
name: editor
widget: Container
style: {flex_direction: vertical, width: 640, height: 200}
children:
  - widget: StatusBar
    clicked: "{{ item }}"
    busy: "{{ saving }}"
    items:
      - {text: Ready}
      - {text: Saved, side: center}
      - {text: "Ln 4, Col 2", side: end, value: goto, tooltip: Go to line}
      - {text: UTF-8, side: end, icon: home, value: encoding}
```

## Using it in Python

```python
from tesserae.widgets import status_bar

status = status_bar(app.window, "Ready", style={"height": 32})
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# StatusBar_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: StatusBar
    part: text
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
