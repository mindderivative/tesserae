# ChipInput_Stylesheet.yaml

An input chip: a piece of information the user entered, such as a tag.

The look of [`ChipInput`](../../components/chips.md) (in [Chips](../../components/chips.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ChipInput: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 32
      align_content: left
      padding:
        left: 16
        right: 16
        top: 0
        bottom: 0
      gap: 8
      background: transparent
      corner_radius: small
      border_color: outline
      border_width: 1.0
  - id: label
    style:
      foreground: on_surface_variant
```

## How it is tied to the component

`ChipInput_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ChipInput`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `32` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `left` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `padding` | left `16`, right `16`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `8` | Space between its children. |
| `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `small` | Pixels, or a shape token (`none` to `extra_large`). |
| `border_color` | `outline` | The colour of its border. |
| `border_width` | `1.0` | The width of its border, in pixels. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `label: Go, width: 120`, each part's style is:

```yaml
root:
  width: 120
  height: 32
  align_content: left
  padding: {left: 16, right: 16, top: 0, bottom: 0}
  gap: 8
  background: transparent
  corner_radius: small
  border_color: outline
  border_width: 1.0
label: {foreground: on_surface_variant}
```

## Changing it

Put a `ChipInput_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
