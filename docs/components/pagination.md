# Pagination

*Content*

## In Material Design 3

Pagination shows where the user is among pages: a row of dots or numbers.

## In Tesserae

`widget: Pagination` is a view Tesserae ships (`Pagination_View.yaml`): previous and next arrows with the page numbers between them.

| Property | Type | Meaning |
| --- | --- | --- |
| `page` | a whole number from 1; two-way | the page showing; choosing another writes it back |
| `pages` | a whole number | how many pages there are |
| `compact` | true or false | "3 of 12" between the arrows instead of the numbers |
| `dots` | true or false | a dot for each page, the current one `primary`, for a carousel |

The first and last pages and the ones beside the current page always show, with an ellipsis for the stretch left out (up to seven pages show whole). The
current page is a filled button, and each number is named "Page n" and marks the current one as the page. Previous is disabled on the first page and next on the
last. Not built: an items-per-page control, a total, and a jump-to field.

This component is a view Tesserae ships: use `widget: Pagination` in a view (see [The View Language](../guide/view-language.md)).

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

## Using it

In Python:

```python
from tesserae.widgets import pagination

pages = pagination(app.window, 10, current=0)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
