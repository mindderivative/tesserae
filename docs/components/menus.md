# Menus

*Navigation*

## In Material Design 3

A menu shows a list of choices on a temporary surface, opened by a button, a right click or a keyboard
shortcut.

## In Tesserae

Two views Tesserae ships: `Menu`, an anchored `Overlay` holding the rows, and `MenuItem`, one 48 pixel row.

| Property of `Menu` | Type | Meaning |
| --- | --- | --- |
| `open` | true or false; two-way | whether it is showing; Escape and a press outside write `false` |
| `anchor`, `placement` | a node's name, `below`/`above`/`start`/`end` | the node in the calling view it sits against, and which side (it flips to fit) |
| `items` | a list | rows: `{value, label}` and optionally `{icon, shortcut, checked, disabled, submenu}`; `{divider: true}`; `{heading: Text}` |
| `chosen` | a value; two-way | the `value` of the item pressed; pressing one closes the menu |
| `mode`, `checks`, `selected` | `plain`, `check`, `radio`; a list; a value | `check`: pressing flips an item's check (the checked values are `checks`); `radio`: one is checked (`selected`) |
| `width`, `on_pick` | a number, a handler | 112 to 280 pixels; called after an item is chosen |

A `MenuItem` has a `label`, an `icon`, `trailing_text` (a shortcut), `checked` (true shows a check, false keeps the room, empty is not checkable), `submenu` (a chevron) and
`disabled`. An item with a `submenu` list opens another `Menu` beside it, on a press or the Right arrow, and choosing in it closes both. The arrows move between rows,
Enter chooses, typing the start of a label jumps to it. A right-click or long-press opener, and the exposed dropdown under a text field, are not built.

`widget: Menu` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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
      wrap: none
      overflow: ellipsis
```

## Using it

```yaml
name: editor
widget: Container
style: {width: 480, height: 360}
children:
  - {widget: Button, name: more, label: More, handlers: {on_click: "open = True"}}
  - widget: Menu
    open: "{{ open }}"
    anchor: more
    chosen: "{{ command }}"
    items:
      - {value: cut, label: Cut, shortcut: Ctrl+X}
      - {value: copy, label: Copy, icon: content_copy}
      - {divider: true}
      - {value: share, label: Share, submenu: [{value: mail, label: Mail}, {value: link, label: Link}]}
```

## Using it

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
