# Floating action buttons

*Actions*

## In Material Design 3

A floating action button (FAB) is the screen's most important action, as an icon in a prominent container.
There are four colours (primary, secondary, tertiary and surface) and three sizes: small (40dp), the
default (56dp) and large (96dp).

## In Tesserae

`widget: Fab` is a view Tesserae ships (`Fab_View.yaml`): one widget for the four colours and three sizes, and for the extended form too (give it a
`label`).

| Property | Type | Meaning |
| --- | --- | --- |
| `icon` | an icon name | the glyph (24 pixels, 36 on a large FAB) |
| `label` | text | the text beside the icon, which makes it extended; also the accessible name |
| `variant` | `primary`, `secondary`, `tertiary`, `surface` | the container colour |
| `size` | `small`, `medium`, `large` | 40, 56 or 96 pixels, with 12, 16 and 28 pixel corners |
| `collapsed` | true or false | an extended FAB shows only its icon (and its label becomes its tooltip) |
| `disabled` | true or false | dimmed, not focusable, handlers do not run |

It rests at elevation level 3, lifts to 4 when hovered and settles to 3 when pressed. To collapse as a list scrolls down and extend as it scrolls up, bind
`collapsed: "{{ way == 'down' }}"` to the `scroll_direction` of the list. Not built: extending animates only as far as the engine lets a width go to `auto`
(the collapse eases, the extend is at once), and the FAB menu.

`widget: Fab` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: FabPrimary` | A floating action button in the primary colour: the screen's main action. | [`FabPrimary_Stylesheet.yaml`](../stylesheets/fabs/fab-primary.md) |
| `component: FabSecondary` | A floating action button in the secondary colour. | [`FabSecondary_Stylesheet.yaml`](../stylesheets/fabs/fab-secondary.md) |
| `component: FabTertiary` | A floating action button in the tertiary colour. | [`FabTertiary_Stylesheet.yaml`](../stylesheets/fabs/fab-tertiary.md) |
| `component: FabSurface` | A floating action button on the surface colour. | [`FabSurface_Stylesheet.yaml`](../stylesheets/fabs/fab-surface.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `FabPrimary`, `FabSecondary`, `FabTertiary`, `FabSurface`

| Parameter | | Default |
| --- | --- | --- |
| `icon` | required |  |
| `size` | required |  |
| `corner_radius` | required |  |
| `fab_size` | optional | `default` |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params:
  - icon
  - size
  - corner_radius
  - {fab_size: default}
id: root
component_of: "fab.{{ fab_size }}"
kind: Rect
children:
  - id: icon
    kind: Icon
    icon:
      name: "{{ icon }}"
```

## Using it

```yaml
name: inbox
widget: Container
style: {flex_direction: vertical, width: 360, height: 480}
children:
  - widget: ScrollView
    scroll_direction: "{{ way }}"
    style: {height: 400}
    children: [{widget: Text, text: Messages}]
  - widget: Fab
    icon: add
    label: Compose
    collapsed: "{{ way == 'down' }}"
    handlers: {on_click: compose}
```

## Using it

In Python:

```python
from tesserae.widgets import fab

add = fab(app.window, "add", size="default", variant="primary")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# FabPrimary_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
