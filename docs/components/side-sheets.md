# Side sheets

*Containment*

## In Material Design 3

A side sheet holds secondary content beside the main content. A **standard** one shares the window with it;
a **modal** one covers it over a scrim and must be dismissed.

## In Tesserae

The standard sheet is a `Rect`; the modal one adds the scrim. `tesserae.overlays.SideSheet` shows either.

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

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: filters
    component: SideSheetStandard
    with: {width: 280, height: 400}
```

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
