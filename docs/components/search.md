# Search

*Navigation*

## In Material Design 3

A search bar is a rounded field that starts a search; the search view is the full-size surface that shows
suggestions and results once it is focused.

## In Tesserae

Two views Tesserae ships. `widget: SearchBar` is a 56 pixel `surface_container_high` pill at level 3 with a leading icon, the text, and trailing parts. `widget: SearchView`
is the docked panel that opens under it with the suggestions, history and results.

| Property | Type | Meaning |
| --- | --- | --- |
| `query` | text; two-way | what has been typed |
| `active` | true or false; two-way | the search is under way; pressing the bar or typing in it sets it, the back arrow clears it |
| `placeholder`, `leading_icon`, `trailing_icon`, `avatar_text` | text, icon names, letters | the hint, the icon at the start (`menu` for a menu button), a microphone at the end, an avatar |
| `on_leading`, `on_trailing`, `on_search` | handlers | the menu button, the trailing icon, Enter |
| `results`, `chosen`, `open`, `anchor` (`SearchView`) | a list; a value, two-way; true or false, two-way; a node's name | `{value, label}` rows (optionally `supporting` and `icon`), the one pressed, whether it shows, the bar it sits under |

A clear button shows once there is text. While active the leading icon is a back arrow. Bind the bar's `active` and the view's `open` to the same name, and the view's `results` to
something that follows `query`. The view says how many results there are, politely, and `empty` text when a query finds none. Escape and a press outside close it. Not built:
the full-screen search view for small windows, and a keyboard shortcut that focuses the bar.

`widget: SearchBar` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: notes
widget: Container
style: {flex_direction: vertical, width: 420, height: 420, padding: 16}
children:
  - {widget: SearchBar, name: bar, query: "{{ q }}", active: "{{ searching }}", placeholder: Search notes, style: {width: 360}}
  - widget: SearchView
    anchor: bar
    open: "{{ searching }}"
    query: "{{ q }}"
    results: "{{ matches }}"
    chosen: "{{ picked }}"
```

## Using it

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
