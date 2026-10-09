# Side sheets

*Containment*

## In Material Design 3

A side sheet holds secondary content beside the main content. A **standard** one shares the window with it;
a **modal** one covers it over a scrim and must be dismissed.

## In Tesserae

Three views Tesserae ships: `SideSheet` (standard, inline), `SideSheetModal` (over a scrim) and `SideSheetPanel` (the inside they share).

| Property | Type | Meaning |
| --- | --- | --- |
| `open` | true or false; two-way | whether it is showing; the close button, and for a modal one Escape and a press on the scrim, write `false` |
| `title`, `back`, `on_back`, `closable` | text, true or false, a handler, true or false | the header: a `title_large` title, a back button that runs `on_back`, a close button |
| `width` | a number | held between 256 and 400 pixels (default 360) |
| `side`, `dismissible` | `start` or `end`; true or false | modal only: the edge it comes from, and whether Escape and the scrim close it |

Children are the content, which scrolls (a line shows over the actions once it has); children with `slot: actions` are the buttons, in a row at the bottom right.
A standard sheet is inline: it takes room from the content while `open` and its width eases open and shut; put it first in its row for the start side and last for
the end. A modal sheet is `surface_container_low` at level 1 with 16 pixel corners on the open side, over the content. Not built: the detached sheet, and the modal
sheet sliding in from the edge.

`widget: SideSheet` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: SideSheetStandard` | A standard side sheet: a panel at the side that shares the window with the content. | [`SideSheetStandard_Stylesheet.yaml`](../stylesheets/side-sheets/side-sheet-standard.md) |
| `component: SideSheetModal` | A modal side sheet: a panel at the side of the window, over a scrim. | [`SideSheetModal_Stylesheet.yaml`](../stylesheets/side-sheets/side-sheet-modal.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `SideSheetStandard`

A standard side sheet: a panel at the side that shares the window with the content. Its look: [`SideSheetStandard_Stylesheet.yaml`](../stylesheets/side-sheets/side-sheet-standard.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |

```yaml
params: [width, height]
id: root
kind: Rect
```

### `SideSheetModal`

A modal side sheet: a panel at the side of the window, over a scrim. Its look: [`SideSheetModal_Stylesheet.yaml`](../stylesheets/side-sheets/side-sheet-modal.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |
| `scrim_width` | required |  |
| `scrim_height` | required |  |

```yaml
params: [width, height, scrim_width, scrim_height]
id: root
kind: Container
children:
  - {id: panel, kind: Rect}
```

## Using it

```yaml
name: editor
widget: Container
style: {flex_direction: horizontal, width: 720, height: 420}
children:
  - {widget: Container, name: page, style: {flex: fill, height: 100%}}
  - widget: SideSheet
    open: "{{ filtering }}"
    title: Filters
    children:
      - {widget: Switch, label: Only mine}
      - {widget: Button, slot: actions, label: Apply, handlers: {on_click: apply}}
```

## Using it

In Python:

```python
from tesserae.widgets import side_sheet

sheet = side_sheet(app.window, 280, modal=True)
sheet.open()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# SideSheetStandard_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Overlays](../guide/overlays.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
