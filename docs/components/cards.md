# Cards

*Containment*

## In Material Design 3

A card holds content and actions about one subject. It comes **elevated** (a shadow), **filled** (a
higher surface) or **outlined** (a border). All have a medium (12dp) corner radius.

## In Tesserae

`widget: Card` is a view Tesserae ships (`Card_View.yaml`): a surface with 12 pixel corners that is as tall as what is in it.

| Property | Type | Meaning |
| --- | --- | --- |
| `variant` | `elevated`, `filled`, `outlined` | a shadow, a higher surface, or a 1 pixel border |
| `headline`, `subhead`, `text` | text | a `title_large` title, a `title_small` line, `body_medium` supporting text, with 16 pixels around them |
| `media`, `media_height` | a picture, a number | a picture across the top, clipped to the corners (default 160 tall) |
| `actionable` | true or false | the whole card is one pressable surface: a state layer, a ripple, Enter, and a lift for the elevated one |
| `selected` | true or false | a chosen card: `secondary_container` (an outlined one gets an `outline` border); the caller decides when |
| `disabled` | true or false | dimmed |

Your own content goes in the default slot, after the text, and buttons in the `actions` slot (a row at the end). `handlers: {on_click: ...}` on the call is
what a press of an actionable card does. A plain card is a group and takes no focus. Not built: dragging and swiping a card, and the dragged state.

`widget: Card` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: CardElevated` | An elevated card: a container on a tinted surface with a shadow. | [`CardElevated_Stylesheet.yaml`](../stylesheets/cards/card-elevated.md) |
| `component: CardFilled` | A filled card: a container on a higher surface, with no shadow or border. | [`CardFilled_Stylesheet.yaml`](../stylesheets/cards/card-filled.md) |
| `component: CardOutlined` | An outlined card: a container with a border and no fill. | [`CardOutlined_Stylesheet.yaml`](../stylesheets/cards/card-outlined.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `CardElevated`, `CardFilled`, `CardOutlined`

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |

These 3 have one structure; only their stylesheets, above, differ.

```yaml
params: [width, height]
id: root
kind: Rect
```

## Using it

```yaml
name: trips
widget: Container
style: {flex_direction: horizontal, gap: 16, padding: 16, width: 560, height: 360}
children:
  - widget: Card
    headline: Paris
    subhead: Three days
    text: Flights and a hotel.
    media: paris.png
    style: {width: 240}
    children:
      - {widget: Button, label: Book, variant: text, slot: actions}
  - {widget: Card, variant: outlined, headline: Rome, actionable: true, selected: "{{ picked }}", style: {width: 240}, handlers: {on_click: pick}}
```

## Using it

In Python:

```python
from tesserae.widgets import card

summary = card(app.window, 240, 120, variant="elevated")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# CardElevated_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
