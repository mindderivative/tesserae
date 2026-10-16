# Search

*Navigation*

## In Material Design 3

A search bar is a rounded field that starts a search; the search view is the full-size surface that shows
suggestions and results once it is focused.

## In Tesserae

Two views Tesserae ships. `widget: SearchBar` is a 56 pixel `surface_container_high` pill at level 3 with a leading icon, the text, and trailing parts. `widget: SearchView`
is the docked panel that opens under it with the suggestions, history and results.

`query` is what has been typed. `active` says the search is under way: pressing the bar or typing in it sets it, and the back arrow clears it. The bar has a `placeholder`, a
`leading_icon` (a search glass; `menu` makes it a menu button that runs `on_leading`), an optional `trailing_icon` (a microphone, say, that runs `on_trailing` and shows
while the field is empty) and an optional avatar (`avatar_text`); Enter calls `on_search`. The `results` of a `SearchView` are `{value, label}` rows, optionally with `supporting` and
`icon`; the row pressed goes to `chosen`, `open` says whether the view shows, and `anchor` names the bar it sits under. `frosted: true` makes the bar and the view translucent
and blurred.

A clear button shows once there is text. While active the leading icon is a back arrow. Bind the bar's `active` and the view's `open` to the same name, and the view's `results` to
something that follows `query`. The view says how many results there are, politely, and `empty` text when a query finds none. Escape and a press outside close it. Not built:
the full-screen search view for small windows, and a keyboard shortcut that focuses the bar.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: SearchBar`. A file of the same name in your project replaces it.

### `SearchBar`

The Material 3 search bar: a 56 pixel `surface_container_high` pill with a leading icon (a search glass, or a menu button), the text being typed, and trailing parts: a clear button once there is a `query`, an optional `trailing_icon` (a microphone) and an optional avatar (`avatar_text`). Pressing it, or typing in it, makes it `active` (two-way; a `SearchView` shows while it is), and while it is active the leading icon becomes a back arrow that deactivates it. Enter calls `on_search`. `query` is two-way.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `query` | `str` |  | What has been typed. Two-way: give it a bare reference and the view writes it back. |
| `placeholder` | `str` | `Search` | Shown while the field is empty. |
| `active` | `bool` | `false` | Whether the search is under way (the view shows); focusing the bar sets it, the back arrow clears it. Two-way: give it a bare reference and the view writes it back. |
| `leading_icon` | `str` | `magnify` | The icon at the start while it is not active (menu, for a menu button). |
| `on_leading` | `handler` |  | What the leading icon does when it is not a search glass (open a drawer). |
| `trailing_icon` | `str` |  | An icon at the end, such as a microphone. |
| `on_trailing` | `handler` |  | What the trailing icon does. |
| `avatar_text` | `str` |  | Letters in a circle at the end. |
| `on_search` | `handler` |  | Called when Enter is pressed. |
| `disabled` | `bool` | `false` | Dimmed and not editable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `back` (Container), `back_icon` (Icon), `leading` (Container), `leading_glyph` (Icon), `input` (TextInput), `clear` (Container), `clear_icon` (Icon), `trailing` (Container), `trailing_glyph` (Icon), `avatar` (Container), `avatar_text` (Text).

Its look is in [`SearchBar_Stylesheet.yaml`](../stylesheets/search/search-bar.md).

### `SearchView`

The Material 3 docked search view: the panel that opens under a search bar (`anchor`, the bar's name in the calling view) and shows suggestions, history and results as list rows. `results` is a list of {value, label} and optionally {supporting, icon}; pressing a row sets `chosen` to its `value` and closes the view. With a `query` and no results the `empty` text shows. Escape and a press outside close it (writing false to `open`). The number of results is announced politely. Bind `open` to the bar's `active`.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `open` | `bool` | `false` | Whether the view is showing; Escape and a press outside write false. Two-way: give it a bare reference and the view writes it back. |
| `anchor` | `str` |  | The name of the search bar in the calling view. |
| `results` | `list` | `[]` | The rows: {value, label} and optionally {supporting, icon}. |
| `query` | `str` |  | What is typed, so the empty state can say there is nothing. |
| `chosen` | `any` |  | The value of the row pressed. Two-way: give it a bare reference and the view writes it back. |
| `empty` | `str` | `No results` | Shown when there is a query and no rows. |
| `width` | `float` | `360` | How wide the view is (the bar's width). |
| `max_height` | `float` | `400` | The rows scroll beyond this. |
| `history_icon` | `str` | `history` | The icon of a row that gives none. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `panel` (Container), `count` (Text), `none` (Text), `rows` (ScrollView), `row` (ListItem).

Its look is in [`SearchView_Stylesheet.yaml`](../stylesheets/search/search-view.md).

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

## Using it in Python

```python
from tesserae.widgets import search_bar

search = search_bar(app.window, "Search notes", 360)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# SearchBar_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: SearchBar
    part: back_icon
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Effects](../guide/effects.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
