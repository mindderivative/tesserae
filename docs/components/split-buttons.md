# Split buttons

*Actions*

## In Material Design 3

A split button joins a main action to a menu of related ones: the leading part does the usual thing, and the
trailing chevron opens the others.

## In Tesserae

`widget: SplitButton` is a view Tesserae ships (`SplitButton_View.yaml`): two `Button`s 2 pixels apart and a `Menu` for the trailing one. One widget covers all five types.

The main part has the `label` and an optional `icon` and runs `on_click`; the trailing part opens a `Menu` of `items` (rows as `Menu` takes them), and the `value`
of the row pressed goes to `chosen`. `variant` and `size` are `Button`'s and both parts take them.

The inner corners are small (4 pixels) and the outer ones round; while the menu is open the trailing part is round on every corner and its chevron is turned over. Each part is its
own Tab stop; the trailing part says it is expanded while its menu shows. Arrow-down on either part opens the menu and moves the focus to its first row (a press opens it
without moving the focus). Not built: a toggle form.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: SplitButton`. A file of the same name in your project replaces it.

### `SplitButton`

The Material 3 split button: a main action and, 2 pixels beside it, a menu button whose chevron turns over while its menu is open. `variant` and `size` are Button's (filled, tonal, elevated, outlined, text; xs to xl). The main part has a `label` and an optional `icon` and calls `on_click`; the trailing part opens a `Menu` of `items` ({value, label} and the rest of Menu's rows) and pressing a row sets `chosen`. The inner corners are small and the outer ones round, and the trailing part is round on both sides while its menu is open. Tab reaches both parts; Enter or Space on either does what pressing it does.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The main action's text. |
| `icon` | `str` |  | A leading icon in the main part. |
| `variant` | `filled` or `tonal` or `elevated` or `outlined` or `text` | `filled` | Passed to both parts. |
| `size` | `xs` or `s` or `m` or `l` or `xl` | `s` | Passed to both parts. |
| `items` | `list` | `[]` | The menu's rows, as Menu takes them. |
| `chosen` | `any` |  | The value of the menu row last pressed. Two-way: give it a bare reference and the view writes it back. |
| `on_click` | `handler` |  | What the main part does. |
| `disabled` | `bool` | `false` | Both parts are dimmed and do not respond. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `main` (Button), `trailing` (Button), `menu` (Menu).

## Using it

```yaml
name: compose
widget: Container
style: {width: 420, height: 240, padding: 16}
children:
  - widget: SplitButton
    label: Send
    icon: send
    on_click: send_now
    chosen: "{{ when }}"
    items:
      - {value: later, label: Send later}
      - {value: draft, label: Save as draft}
```

## Using it in Python

```python
from tesserae.widgets import split_button

send = split_button(app.window, "Send", 160, 40, variant="filled")
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
