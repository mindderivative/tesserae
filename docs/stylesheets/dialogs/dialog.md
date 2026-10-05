# Dialog_Stylesheet.yaml

A dialog: a headline and text on a raised panel, over a scrim.

The look of [`Dialog`](../../components/dialogs.md) (in [Dialogs](../../components/dialogs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# Dialog: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ scrim_width }}"
      height: "{{ scrim_height }}"
      background: '#00000052'
      align_content: center
  - id: panel
    style:
      flex_direction: vertical
      width: "{{ width }}"
      height: "{{ height }}"
      background: surface_container_high
      corner_radius: extra_large
      elevation: level_3
      padding: 24
      gap: 16
  - id: headline
    style:
      foreground: on_surface
  - id: body
    style:
      foreground: on_surface_variant
      flex: expand_vertical
```

## How it is tied to the component

`Dialog_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: Dialog`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `scrim_width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `scrim_height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `#00000052` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `panel` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_container_high` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `extra_large` | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_3` | A shadow level, 0 to 5. |
| `padding` | `24` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `16` | Space between its children. |

### `headline` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `body` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `flex` | `expand_vertical` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |

## What it makes

With `headline: Headline, text: Hello, width: 120, height: 40, scrim_width: 400, scrim_height: 300`, each part's style is:

```yaml
root: {width: 400, height: 300, background: '#00000052', align_content: center}
panel: {flex_direction: vertical, width: 120, height: 40, background: surface_container_high, corner_radius: extra_large,
  elevation: level_3, padding: 24, gap: 16}
headline: {foreground: on_surface}
body: {foreground: on_surface_variant, flex: expand_vertical}
```

## Changing it

Put a `Dialog_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
