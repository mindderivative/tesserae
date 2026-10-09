# IconButtonFilledTonal_Stylesheet.yaml

A filled tonal icon button: a medium-emphasis action shown as an icon.

The look of [`IconButtonFilledTonal`](../../components/icon-buttons.md) (in [Icon buttons](../../components/icon-buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# IconButtonFilledTonal: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ size }}"
      height: "{{ size }}"
      align_content: center
      background: secondary_container
      corner_radius: "{{ corner_radius }}"
  - id: icon
    style:
      width: 24
      height: 24
      foreground: on_secondary_container
```

## How it is tied to the component

`IconButtonFilledTonal_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: IconButtonFilledTonal`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `background` | `secondary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `icon: home, size: 40, corner_radius: 20`, each part's style is:

```yaml
root: {width: 40, height: 40, align_content: center, background: secondary_container, corner_radius: 20}
icon: {width: 24, height: 24, foreground: on_secondary_container}
```

## Changing it

Put a `IconButtonFilledTonal_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
