# Top app bar

*Navigation*

## In Material Design 3

A top app bar sits along the top of a screen with its title and the actions for it: a navigation icon at the
start and up to a few action icons at the end.

## In Tesserae

The fragment is the bar and its title; `top_app_bar()` adds the icon buttons, and keeps the bar's height
when the window is short. With `App(borderless=True)` it can also be the window's own title bar.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: TopAppBar` | A top app bar: the window's title and actions, along the top. | [`TopAppBar_Stylesheet.yaml`](../stylesheets/top-app-bar/top-app-bar.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `TopAppBar`

A top app bar: the window's title and actions, along the top. Its look: [`TopAppBar_Stylesheet.yaml`](../stylesheets/top-app-bar/top-app-bar.md).

| Parameter | | Default |
| --- | --- | --- |
| `title` | required |  |
| `width` | required |  |

```yaml
params: [title, width]
id: root
kind: Container
children:
  - id: title
    kind: Text
    text:
      content: "{{ title }}"
      typography_role: title_large
      wrap: none
      overflow: ellipsis
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: bar
    component: TopAppBar
    with: {title: Notes, width: 640}
```

In Python:

```python
from tesserae.widgets import top_app_bar

bar = top_app_bar(app.window, "Notes", leading_icon="menu", trailing_icons=["settings"])
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# TopAppBar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Custom Title Bars](../guide/custom-title-bars.md)
- [App Shell](../guide/app-shell.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
