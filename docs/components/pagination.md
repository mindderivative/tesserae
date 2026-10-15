# Pagination

*Content*

## In Material Design 3

Pagination shows where the user is among pages: a row of dots or numbers.

## In Tesserae

`widget: Pagination` is a view Tesserae ships (`Pagination_View.yaml`): previous and next arrows with the page numbers between them.

`page` (from 1) is two-way: choosing another writes it back. `pages` is how many there are. `compact` shows "3 of 12" between the arrows instead of the numbers, and `dots`
shows a dot for each page, the current one `primary`, for a carousel (best under ten pages).

The first and last pages and the ones beside the current page always show, with an ellipsis for the stretch left out (up to seven pages show whole). The
current page is a filled button, and each number is named "Page n" and marks the current one as the page. Previous is disabled on the first page and next on the
last. Tab visits each control, and Enter or Space chooses. Not built: an items-per-page control, a count of all the items, and a jump-to field.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Pagination`. A file of the same name in your project replaces it.

### `Pagination`

Page navigation (not Material 3 itself, which has page indicators and a pager): previous and next, and between them the page numbers with an ellipsis for the stretches left out, the current page filled. `page` (two-way, from 1) is the page showing and `pages` how many there are; the first, the last and the pages beside the current one always show. `compact` is a "3 of 12" between the arrows, and `dots` is a row of dots, one to a page, for a carousel. Previous is disabled on the first page and next on the last. Tab visits each control; Enter or Space chooses.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `page` | `int` | `1` | The page showing, from 1; choosing another writes it back. Two-way: give it a bare reference and the view writes it back. |
| `pages` | `int` | `1` | How many pages there are. |
| `compact` | `bool` | `false` | Show '3 of 12' instead of the numbers. |
| `dots` | `bool` | `false` | Show a dot for each page instead of the numbers (best under ten pages). |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `previous` (IconButton), `summary` (Text), `dot` (Container), `mark` (Container), `slot` (Container), `gap` (Text), `number` (Button), `next` (IconButton).

Its look is in [`Pagination_Stylesheet.yaml`](../stylesheets/pagination/pagination.md).

## Using it

```yaml
name: results
widget: Container
style: {flex_direction: vertical, gap: 12, width: 480, height: 200}
children:
  - {widget: Pagination, page: "{{ page }}", pages: "{{ total_pages }}"}
  - {widget: Pagination, page: "{{ page }}", pages: "{{ total_pages }}", compact: true}
  - {widget: Pagination, page: "{{ page }}", pages: 5, dots: true}
```

## Using it in Python

```python
from tesserae.widgets import pagination

pages = pagination(app.window, 10, current=0)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Pagination_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Pagination
    part: gap
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
