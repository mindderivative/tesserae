# Search

*Navigation*

## In Material Design 3

A search bar is a rounded field that starts a search; the search view is the full-size surface that shows
suggestions and results once it is focused.

## In Tesserae

The bar is a container around a `TextField`; the view is a surface that `tesserae.overlays.SearchView` shows.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: SearchBar` | A search bar: a rounded field with a placeholder. | [`SearchBar_Stylesheet.yaml`](../stylesheets/search/search-bar.md) |
| `component: SearchView` | A search view: the full-size surface search results appear on. | [`SearchView_Stylesheet.yaml`](../stylesheets/search/search-view.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `SearchBar`

A search bar: a rounded field with a placeholder. Its look: [`SearchBar_Stylesheet.yaml`](../stylesheets/search/search-bar.md).

| Parameter | | Default |
| --- | --- | --- |
| `placeholder` | required |  |
| `width` | required |  |
| `corner_radius` | required |  |

```yaml
params: [placeholder, width, corner_radius]
id: root
kind: Container
children:
  - id: field
    kind: TextField
    text:
      content: "{{ placeholder }}"
      font_family: Roboto
      font_weight: 400
      font_size: 16
```

### `SearchView`

A search view: the full-size surface search results appear on. Its look: [`SearchView_Stylesheet.yaml`](../stylesheets/search/search-view.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |

```yaml
params: [width, height]
id: root
kind: Rect
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: search
    component: SearchBar
    with: {placeholder: Search notes, width: 360, corner_radius: 28}
```

In Python:

```python
from tesserae.widgets import search_bar

search = search_bar(app.window, "Search notes", 360)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# SearchBar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
