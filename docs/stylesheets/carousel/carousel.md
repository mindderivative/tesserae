# Carousel_Stylesheet.yaml

The look of Carousel: the item captions in white over a darkened band.

The look of [`Carousel`](../../components/carousel.md) (in [Carousel](../../components/carousel.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Carousel: the item captions in white over a darkened band.
styles:
  - {widget: Carousel, part: title, style: {foreground: "#FFFFFF"}}
  - {widget: Carousel, part: supporting, style: {foreground: "#FFFFFFCC"}}
```

## How it reaches the view

Each rule names `widget: Carousel` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `title` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `#FFFFFF` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `supporting` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `#FFFFFFCC` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Carousel
    part: title
    style: {foreground: tertiary}
```
