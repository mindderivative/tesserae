# Carousel

*Content*

## In Material Design 3

A carousel shows a row of items that scroll, with the focused one largest. MD3 has multi-browse, uncontained,
hero and full-screen layouts.

## In Tesserae

`widget: Carousel` is a view Tesserae ships (`Carousel_View.yaml`): a `ScrollView` that scrolls sideways (`orientation: horizontal`) and settles on an item
(`snap`, with each item's `snap_align`), of items with 28 pixel corners, 8 pixels apart, with a title on a darkened band.

Each of `items` is `{value, title}` and optionally `{image, supporting}`. `variant` sets how big the items are: `uncontained` (the default; every item `item_width` wide),
`multi_browse` (a large item, a medium one, then small ones), `hero` (large items with a peek of the next) or `center_hero` (the middle item large, with a peek of each
neighbour). `width` and `height` are the carousel's own size (360 by 200 by default). Pressing an item sets `chosen` (two-way) to its `value`.

The wheel and a drag scroll it; when it stops it settles with an item at the start (the middle for `center_hero`). The items are focusable and the arrow keys move along
them. A `ScrollView` takes `snap` (`none`, `start`, `center`, `end`) and any node a `snap_align` style, so other strips can do the same. Not built: the sizes changing as
it scrolls (a multi-browse carousel's large item is the first one), parallax on the pictures, dot indicators, full-screen, autoplay.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Carousel`. A file of the same name in your project replaces it.

### `Carousel`

The Material 3 carousel: a row of rounded items that scrolls sideways and settles with an item lined up (the scroll view's `snap`). `items` is a list of {value, title} and optionally {image, supporting}; `variant` sets how big they are: `uncontained` (every item `item_width` wide), `multi_browse` (a large item, a medium one, then small ones), `hero` (large items with a peek of the next) and `center_hero` (the item in the middle large, with a peek of the ones either side). `width` and `height` are the carousel's own. Pressing an item sets `chosen` to its `value`; the items are focusable and the arrows move along them. The wheel and a drag scroll it, and so do the arrows once an item is focused.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `items` | `list` | `[]` | The items, each {value, title} and optionally {image, supporting}. |
| `variant` | `uncontained` or `multi_browse` or `hero` or `center_hero` | `uncontained` | How big the items are. |
| `chosen` | `any` |  | The value of the item last pressed. Two-way: give it a bare reference and the view writes it back. |
| `width` | `float` | `360` | How wide the carousel is. |
| `height` | `float` | `200` | How tall the items are. |
| `item_width` | `float` | `200` | uncontained: how wide each item is. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `item` (Container), `picture` (Image), `caption` (Container), `title` (Text), `supporting` (Text).

Its look is in [`Carousel_Stylesheet.yaml`](../stylesheets/carousel/carousel.md).

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

## Using it in Python

```python
from tesserae.widgets import carousel

gallery = carousel(app.window, 480, 180, layout="multi_browse", items=[])
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Carousel_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Carousel
    part: title
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
