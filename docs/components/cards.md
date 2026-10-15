# Cards

*Containment*

## In Material Design 3

A card holds content and actions about one subject. It comes **elevated** (a shadow), **filled** (a
higher surface) or **outlined** (a border). All have a medium (12dp) corner radius.

## In Tesserae

`widget: Card` is a view Tesserae ships (`Card_View.yaml`): a surface with 12 pixel corners that is as tall as what is in it.

The `variant` is a shadow (`elevated`, level 1), a higher surface (`filled`) or a 1 pixel `outline_variant` border (`outlined`). The `headline` is `title_large`, the `subhead`
`title_small` and the `text` `body_medium`, with 16 pixels around them. A `media` picture runs across the top, clipped to the corners (160 pixels tall unless `media_height` says
otherwise). An `actionable` card is one pressable surface: a state layer, a ripple, Enter, and a lift to level 2 for the elevated one when hovered. A `selected` card is
`secondary_container` (an outlined one gets an `outline` border instead); the caller decides when, as in `on_click: "picked = not picked"`. A `disabled` card is dimmed.

Your own content goes in the default slot, after the text, and buttons in the `actions` slot (a row at the end). `handlers: {on_click: ...}` on the call is
what a press of an actionable card does. A plain card is a group and takes no focus. Not built: dragging and swiping a card, and the dragged state.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Card`. A file of the same name in your project replaces it.

### `Card`

The Material 3 card: a surface that holds content about one subject. `variant` is elevated, filled or outlined. It can have a `media` picture across the top, a `headline`, a `subhead` and supporting `text`; your own content goes in the default slot, and a row of `actions` (buttons) in the `actions` slot. An `actionable` card is one pressable surface (a state layer, a ripple, Enter, a lift for the elevated one): `handlers: {on_click: open}` on the call is what a press does, and the buttons inside one are a conflict MD3 asks you to avoid. `selected` shows a chosen card; the caller decides when (`on_click: "picked = not picked"`). Colours, corners and how it lifts are in Card_Stylesheet.yaml.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `variant` | `elevated` or `filled` or `outlined` | `elevated` | elevated has a shadow, filled a higher surface, outlined a border. |
| `headline` | `str` |  | The title. |
| `subhead` | `str` |  | A line under the title. |
| `text` | `str` |  | Supporting text. |
| `media` | `str` |  | A picture across the top, relative to the view. |
| `media_height` | `float` | `160` | How tall the picture is. |
| `actionable` | `bool` | `false` | The whole card is one pressable surface. |
| `selected` | `bool` | `false` | Whether the card is chosen (the caller decides when). |
| `disabled` | `bool` | `false` | Dimmed, and an actionable card does not respond. |

Children go in the default slot, the `actions` slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `picture` (Image), `body` (Container), `headline` (Text), `subhead` (Text), `text` (Text), `actions` (Container).

Its look is in [`Card_Stylesheet.yaml`](../stylesheets/cards/card.md).

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

## Using it in Python

```python
from tesserae.widgets import card

summary = card(app.window, 240, 120, variant="elevated")
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Card_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Card
    part: headline
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
