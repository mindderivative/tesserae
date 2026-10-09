# ButtonOutlined_Stylesheet.yaml

An outlined button: a medium-emphasis button with a border and no fill.

The look of [`ButtonOutlined`](../../components/buttons.md) (in [Buttons](../../components/buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ButtonOutlined: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      align_content: center
      background: transparent
      corner_radius: "{{ corner_radius }}"
      border_color: outline
      border_width: 1.0
      padding:
        left: 12
        right: 12
        top: 0
        bottom: 0
  - id: label
    style:
      foreground: primary
```

## How it is tied to the component

`ButtonOutlined_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ButtonOutlined`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `border_color` | `outline` | The colour of its border: a colour or a gradient. |
| `border_width` | `1.0` | The width of its border, in pixels. |
| `padding` | left `12`, right `12`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `label: Go, width: 120, height: 40, corner_radius: 20`, each part's style is:

```yaml
root:
  width: 120
  height: 40
  align_content: center
  background: transparent
  corner_radius: 20
  border_color: outline
  border_width: 1.0
  padding: {left: 12, right: 12, top: 0, bottom: 0}
label: {foreground: primary}
```

## Changing it

Put a `ButtonOutlined_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
