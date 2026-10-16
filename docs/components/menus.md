# Menus

*Navigation*

## In Material Design 3

A menu shows a list of choices on a temporary surface, opened by a button, a right click or a keyboard
shortcut.

## In Tesserae

Two views Tesserae ships: `Menu`, an anchored `Overlay` holding the rows, and `MenuItem`, one 48 pixel row.

A `Menu` is shown while `open` is true; Escape and a press outside write `false` back. `anchor` is the name of the node in the calling view it sits against, and `placement`
(`below` by default, `above`, `start` or `end`) the side, which it flips or shifts to fit. The `items` are rows `{value, label}` and optionally `{icon, shortcut, checked, disabled,
submenu}`, `{divider: true}` for a line and `{heading: Text}` for a small heading. Pressing an item writes its `value` to `chosen`, closes the menu and calls `on_pick`. With `mode:
check` pressing an item flips its check (the checked values are `checks`); with `mode: radio` one item is checked (`selected`). The menu is `width` wide, 112 to 280 pixels (200 by
default), and `frosted: true` makes the surface translucent and blurred.

A `MenuItem` has a `label`, an `icon`, `trailing_text` (a shortcut), `checked` (true shows a check, false keeps the room, empty is not checkable), `submenu` (a chevron) and
`disabled`. An item with a `submenu` list opens another `Menu` beside it, on a press or the Right arrow, and choosing in it closes both. The arrows move between rows,
Enter chooses, typing the start of a label jumps to it. A long press can open it (`handlers: {on_long_press: ...}` on the node, writing `open`), and in Python `attach_context(node)`
on a `menu(...)` opens it at the pointer on a right-click. Not built: a right-click opener in a view, and the exposed dropdown under a text field.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Menu`. A file of the same name in your project replaces it.

### `Menu`

The Material 3 menu: a list of choices on a temporary surface next to the node it comes from (`anchor`, the name of a node in the view that has the menu). `items` is a list of {value, label} and optionally {icon, shortcut, checked, disabled, submenu}; a {divider: true} is a line and a {heading: "Text"} a small heading. Pressing an item sets `chosen` to its `value` and closes the menu; `mode: check` makes pressing an item flip its check (kept in `checks`, the list of checked values) and `mode: radio` keeps one checked (`selected`). An item with a `submenu` list opens another menu beside it (with Right, or a press). Escape and a press outside close it (writing false to `open`); the arrows move, Enter chooses, typing the start of a label jumps to it.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `open` | `bool` | `false` | Whether the menu is showing; Escape and a press outside write false. Two-way: give it a bare reference and the view writes it back. |
| `anchor` | `str` |  | The name of the node in the calling view the menu sits against. |
| `items` | `list` | `[]` | The rows: {value, label} and optionally {icon, shortcut, checked, disabled, submenu}; {divider: true}; {heading: Text}. |
| `chosen` | `any` |  | The value of the item last pressed. Two-way: give it a bare reference and the view writes it back. |
| `mode` | `plain` or `check` or `radio` | `plain` | plain: actions; check: items flip their checks; radio: one item is checked. |
| `checks` | `list` | `[]` | check mode: the values that are checked. Two-way: give it a bare reference and the view writes it back. |
| `selected` | `any` |  | radio mode: the value that is checked. Two-way: give it a bare reference and the view writes it back. |
| `placement` | `below` or `above` or `start` or `end` | `below` | Which side of the anchor; it flips or shifts to fit. |
| `width` | `float` | `200` | How wide the menu is, from 112 to 280 pixels. |
| `focus_first` | `bool` | `false` | When it opens, the focus moves to its first row (a menu opened with the keyboard). |
| `on_pick` | `handler` |  | Called after an item has been chosen (a submenu uses it to close the menu it came from). |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `surface` (Container), `row` (Container), `divider` (Divider), `heading` (Text), `item` (MenuItem), `parent_item` (MenuItem), `sub` (Menu).

Its look is in [`Menu_Stylesheet.yaml`](../stylesheets/menus/menu.md).

### `MenuItem`

One row of a menu (Material 3): 48 pixels tall, `label_large` text, an optional 24 pixel leading icon, trailing text such as a keyboard shortcut, and a chevron when it opens a submenu. `checked` makes it a checkable item: true shows a check where the icon would be, false leaves the space, and nothing (null) is no check at all. It is pressable (a state layer, a ripple, Enter); `handlers: {on_click: ...}` on the call is what a press does. Roles: a `menuitem`, with `checked` for a checkable one.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The text. |
| `icon` | `str` |  | A leading icon. |
| `trailing_text` | `str` |  | Text at the end, such as a shortcut. |
| `checked` | `any` |  | true: a check shows; false: its space is kept; empty: not checkable. |
| `submenu` | `bool` | `false` | A chevron at the end: the item opens another menu. |
| `disabled` | `bool` | `false` | Dimmed, not focusable, and it does not respond. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `lead` (Icon), `lead_space` (Container), `label` (Text), `filler` (Container), `trailing` (Text), `chevron` (Icon).

Its look is in [`MenuItem_Stylesheet.yaml`](../stylesheets/menus/menu-item.md).

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

## Using it in Python

```python
from tesserae.widgets import menu

actions = menu(app.window, [("Cut", viewmodel.cut), ("Copy", viewmodel.copy)], width=200)
actions.open(save.node)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Menu_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Menu
    part: surface
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Effects](../guide/effects.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
