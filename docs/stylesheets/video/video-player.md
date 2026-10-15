# VideoPlayer_Stylesheet.yaml

The look of VideoPlayer: the picture sits on a dark stage; the time labels are on_surface_variant; the subtitle band is white on a darkened scrim.

The look of [`VideoPlayer`](../../components/video.md) (in [Video](../../components/video.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of VideoPlayer: the picture sits on a dark stage; the time labels are on_surface_variant; the subtitle band is white on a darkened scrim.
styles:
  - {widget: VideoPlayer, part: elapsed, style: {foreground: on_surface_variant}}
  - {widget: VideoPlayer, part: total, style: {foreground: on_surface_variant}}
  - {widget: VideoPlayer, part: caption_text, style: {foreground: "#ffffff"}}
```

## How it reaches the view

Each rule names `widget: VideoPlayer` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties and classes matched, then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `elapsed` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `total` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `caption_text` (Text)

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `foreground` | `#ffffff` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: VideoPlayer
    part: elapsed
    style: {foreground: tertiary}
```
