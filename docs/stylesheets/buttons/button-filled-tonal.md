# ButtonFilledTonal_Stylesheet.yaml

A filled tonal button: a medium-emphasis button in the secondary container colour.

The look of [`ButtonFilledTonal`](../../components/buttons.md) (in [Buttons](../../components/buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ButtonFilledTonal: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      align_content: center
      background: secondary_container
      corner_radius: "{{ corner_radius }}"
      padding:
        left: 12
        right: 12
        top: 0
        bottom: 0
  - id: label
    style:
      foreground: on_secondary_container
```

## How it is tied to the component

`ButtonFilledTonal_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ButtonFilledTonal`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `background` | `secondary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `padding` | left `12`, right `12`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `label: Go, width: 120, height: 40, corner_radius: 20`, each part's style is:

```yaml
root:
  width: 120
  height: 40
  align_content: center
  background: secondary_container
  corner_radius: 20
  padding: {left: 12, right: 12, top: 0, bottom: 0}
label: {foreground: on_secondary_container}
```

## Changing it

Put a `ButtonFilledTonal_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
