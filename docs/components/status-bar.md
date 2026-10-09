# Status bar

*Beyond MD3*

## In Material Design 3

Material Design 3 has no status bar. A desktop app often wants one, so this is a thin strip in MD3's
surface and *label* style.

## In Tesserae

`widget: StatusBar` is a view Tesserae ships (`StatusBar_View.yaml`): a 24 pixel `surface_container` strip as wide as the place it is put in, with
`label_small` text in `on_surface_variant`.

| Property | Type | Meaning |
| --- | --- | --- |
| `items` | a list | each `{text}` and optionally `{icon, side, value, tooltip}`; `side` is `start` (the default), `center` or `end` |
| `progress` | 0 to 1 | a 4 pixel determinate indicator along the top edge |
| `busy` | true or false | an indicator with no end along the top edge |
| `clicked` | a value; two-way | the `value` of the item last pressed |

An item with a `value` is a button: it has a state layer, a tooltip if it has one, and pressing it sets `clicked`. The centre section is centred on the
bar whatever the sides hold. The bar is announced politely when its items change. Not built: items that can be dragged or hidden when the window is
narrow.

`widget: StatusBar` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: StatusBar` | A status bar: a thin strip of text along the bottom of the window. | [`StatusBar_Stylesheet.yaml`](../stylesheets/status-bar/status-bar.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `StatusBar`

A status bar: a thin strip of text along the bottom of the window. Its look: [`StatusBar_Stylesheet.yaml`](../stylesheets/status-bar/status-bar.md).

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
      typography_role: label_small
      wrap: none
      overflow: ellipsis
```

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

## Using it

In Python:

```python
from tesserae.widgets import status_bar

status = status_bar(app.window, "Ready", style={"height": 32})
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# StatusBar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
