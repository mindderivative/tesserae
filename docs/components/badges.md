# Badges

*Communication*

## In Material Design 3

A badge shows that something has news. The small one is a dot, and the large one carries a short count or
text. It sits on the corner of what it describes.

## In Tesserae

`widget: Badge` is a view Tesserae ships (`Badge_View.yaml`) with its look as rules (`Badge_Stylesheet.yaml`): a 6 pixel `error` dot, or with a
`value` a 16 pixel pill in `label_small` on `on_error`, at least 16 wide and growing with its text.

A `value` that is a number over `limit` shows as the limit and a plus (`999+` by default), and `show: "{{ unread > 0 }}"` hides a zero count. With
`anchored: true` the children are the host, and the badge sits over the host's top right corner.

Anchored, a dot overlaps the corner by 4 and a pill starts 12 in from the corner and 4 above it. The badge is hidden from a screen reader: put the
count in the host's label ("Inbox, 3 unread"). The parts a stylesheet can address are `mark` and `label`.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Badge`. A file of the same name in your project replaces it.

### `Badge`

The Material 3 badge: a 6 dp dot (no value) or a 16 dp pill holding a count or short text. Alone it is the mark itself, to place where you like; with `anchored: true` its children are the host (an icon, a button, a tab) and the mark sits over the host's top right corner. The look is in Badge_Stylesheet.yaml; this file is the structure. A count over `limit` shows as `999+`. Hide a zero count with `show: "{{ n > 0 }}"`. The mark is hidden from a screen reader: put the count in the host's label ("Inbox, 3 unread").

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `value` | `any` |  | A number or a few characters. Empty is a dot. |
| `limit` | `int` | `999` | A number over this shows as the limit and a plus. |
| `show` | `bool` | `true` | Whether the badge shows. |
| `anchored` | `bool` | `false` | The children are the host, and the mark sits on its top right corner. |

Children go in the default slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `host` (Container), `mark` (Container), `label` (Text).

Its look is in [`Badge_Stylesheet.yaml`](../stylesheets/badges/badge.md).

## Using it

```yaml
name: nav
widget: Container
style: {flex_direction: horizontal, gap: 24, width: 200, height: 60, padding: 16}
children:
  - widget: Badge
    value: "{{ unread }}"
    show: "{{ unread > 0 }}"
    anchored: true
    children:
      - {widget: Icon, icon: email, style: {width: 24, height: 24, foreground: on_surface}}
  - widget: Badge
    anchored: true
    children:
      - {widget: Icon, icon: home, style: {width: 24, height: 24, foreground: on_surface}}
```

## Using it in Python

```python
from tesserae.widgets import badge

unread = badge(app.window, "3")
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Badge_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Badge
    part: mark
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
