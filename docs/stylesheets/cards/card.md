# Card_Stylesheet.yaml

The look of Card (Material 3): 12 pixel corners, 16 pixels of padding around the text. Elevated is surface_container_low at level 1 (2 when an actionable one is hovered), filled is surface_container_highest, outlined is surface with a 1 pixel outline_variant border. A selected outlined card has an outline border; a selected filled or elevated one is secondary_container.

The look of [`Card`](../../components/cards.md) (in [Cards](../../components/cards.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Card (Material 3): 12 pixel corners, 16 pixels of padding around the text. Elevated is surface_container_low at level 1 (2 when an
# actionable one is hovered), filled is surface_container_highest, outlined is surface with a 1 pixel outline_variant border. A selected outlined card has
# an outline border; a selected filled or elevated one is secondary_container.
styles:
  - widget: Card
    style:
      corner_radius: 12
      transition: {elevation: 200, background: 150}
  - widget: Card
    variant: elevated
    style: {background: "{{ 'secondary_container' if selected else 'surface_container_low' }}", elevation: 1}
  - {widget: Card, variant: elevated, state: hovered, style: {elevation: "{{ 2 if actionable else 1 }}"}}
  - {widget: Card, variant: filled, style: {background: "{{ 'secondary_container' if selected else 'surface_container_highest' }}"}}
  - widget: Card
    variant: outlined
    style:
      background: surface
      border_width: 1
      border_color: "{{ 'outline' if selected else 'outline_variant' }}"
  - {widget: Card, part: body, style: {padding: 16, gap: 4}}
  - {widget: Card, part: headline, style: {foreground: on_surface}}
  - {widget: Card, part: subhead, style: {foreground: on_surface_variant}}
  - {widget: Card, part: text, style: {foreground: on_surface_variant}}
```

## How it reaches the view

Each rule names `widget: Card` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Card` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `corner_radius` | `12` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| always | `transition` | `{background: 150, elevation: 200}` | Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. `all` covers every one that can. A node is where it says when first drawn; only a change eases. |
| `variant: elevated` | `background` | `{{ 'secondary_container' if selected else 'surface_container_low' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: elevated` | `elevation` | `1` | A shadow level, 0 to 5. |
| `variant: elevated`, state `hovered` | `elevation` | `{{ 2 if actionable else 1 }}` | A shadow level, 0 to 5. |
| `variant: filled` | `background` | `{{ 'secondary_container' if selected else 'surface_container_highest' }}` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: outlined` | `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `variant: outlined` | `border_width` | `1` | The width of its border, in pixels. |
| `variant: outlined` | `border_color` | `{{ 'outline' if selected else 'outline_variant' }}` | The colour of its border: a colour or a gradient. |

### `body` (Container)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `padding` | `16` | Space inside it: one number, or `{left, right, top, bottom}`. |
| always | `gap` | `4` | Space between its children. |

### `headline` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `subhead` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Card
    variant: elevated
    style: {background: tertiary}
```
