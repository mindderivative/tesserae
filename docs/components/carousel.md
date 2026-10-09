# Carousel

*Content*

## In Material Design 3

A carousel shows a row of items that scroll, with the focused one largest. MD3 has multi-browse, uncontained,
hero and full-screen layouts.

## In Tesserae

`widget: Carousel` is a view Tesserae ships (`Carousel_View.yaml`): a `ScrollView` that scrolls sideways (`orientation: horizontal`) and settles on an item
(`snap`, with each item's `snap_align`), of rounded items 8 pixels apart with a title on a darkened band.

| Property | Type | Meaning |
| --- | --- | --- |
| `items` | a list | `{value, title}` and optionally `{image, supporting}` |
| `variant` | `uncontained`, `multi_browse`, `hero`, `center_hero` | every item `item_width` wide; a large, a medium and then small items; large items with a peek of the next; the middle item large with a peek of each neighbour |
| `width`, `height`, `item_width` | numbers | the carousel's size (default 360 by 200) and an uncontained item's width |
| `chosen` | a value; two-way | the item pressed |

The wheel and a drag scroll it; when it stops it settles with an item at the start (the middle for `center_hero`). The items are focusable and the arrow keys move along
them. A `ScrollView` takes `snap` (`none`, `start`, `center`, `end`) and any node a `snap_align` style, so other strips can do the same. Not built: the sizes changing as
it scrolls (a multi-browse carousel's large item is the first one), parallax on the pictures, dot indicators, full-screen, autoplay.

This component is a view Tesserae ships: use `widget: Carousel` in a view (see [The View Language](../guide/view-language.md)).

## Using it

```yaml
name: gallery
widget: Container
style: {width: 420, height: 260}
children:
  - widget: Carousel
    variant: hero
    chosen: "{{ opened }}"
    items:
      - {value: a, title: Paris, supporting: Three days}
      - {value: b, title: Rome}
      - {value: c, title: Lisbon}
```

## Using it

In Python:

```python
from tesserae.widgets import carousel

gallery = carousel(app.window, 480, 180, layout="multi_browse", items=[])
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
