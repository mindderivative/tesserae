# Menus

*Navigation*

## In Material Design 3

A menu shows a list of choices on a temporary surface, opened by a button, a right click or a keyboard
shortcut.

## In Tesserae

A column of `MenuItem`s; `tesserae.overlays.Menu` opens it next to an anchor, at a point, or as a context
menu, and handles the arrow keys.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Menu` | A menu: a surface listing choices, each a menu item. | [`Menu_Stylesheet.yaml`](../stylesheets/menus/menu.md) |
| `component: MenuItem` | One choice in a menu. | [`MenuItem_Stylesheet.yaml`](../stylesheets/menus/menu-item.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Menu`

A menu: a surface listing choices, each a menu item. Its look: [`Menu_Stylesheet.yaml`](../stylesheets/menus/menu.md).

| Parameter | | Default |
| --- | --- | --- |
| `items` | required |  |
| `width` | required |  |

```yaml
params: [items, width]
id: root
kind: Container
children:
  - id: item
    component: MenuItem
    with:
      width: "{{ width }}"
      height: 48
      padding: {left: 12, right: 12, top: 0, bottom: 0}
    repeat: "{{ items }}"
```

### `MenuItem`

One choice in a menu. Its look: [`MenuItem_Stylesheet.yaml`](../stylesheets/menus/menu-item.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |
| `height` | optional | `56` |
| `padding` | optional | `16` |

```yaml
params:
  - label
  - width
  - {height: 56}
  - {padding: 16}
id: root
kind: Container
children:
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: actions
    component: Menu
    with:
      width: 200
      items: [{label: Cut}, {label: Copy}, {label: Paste}]
```

In Python:

```python
from tesserae.widgets import menu

actions = menu(app.window, [("Cut", viewmodel.cut), ("Copy", viewmodel.copy)], width=200)
actions.open(save.node)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Menu_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
