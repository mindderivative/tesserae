# StatusBar_Stylesheet.yaml

A status bar: a thin strip of text along the bottom of the window.

The look of [`StatusBar`](../../components/status-bar.md) (in [Status bar](../../components/status-bar.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# StatusBar: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 24
      background: surface_container
      align_content: left
      padding:
        left: 8
        right: 8
        top: 0
        bottom: 0
  - id: text
    style:
      foreground: on_surface_variant
      flex: expand_horizontal
      min_width: 0
```

## How it is tied to the component

`StatusBar_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: StatusBar`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `align_content` | `left` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `padding` | left `8`, right `8`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `text` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `flex` | `expand_horizontal` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| `min_width` | `0` | The least width it can take. |

## What it makes

With `text: Hello, width: 120`, each part's style is:

```yaml
root:
  width: 120
  height: 24
  background: surface_container
  align_content: left
  padding: {left: 8, right: 8, top: 0, bottom: 0}
text: {foreground: on_surface_variant, flex: expand_horizontal, min_width: 0}
```

## Changing it

Put a `StatusBar_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
