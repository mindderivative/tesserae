# CardOutlined_Stylesheet.yaml

An outlined card: a container with a border and no fill.

The look of [`CardOutlined`](../../components/cards.md) (in [Cards](../../components/cards.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# CardOutlined: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      background: surface
      corner_radius: medium
      border_color: outline_variant
      border_width: 1.0
```

## How it is tied to the component

`CardOutlined_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: CardOutlined`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `medium` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). |
| `border_color` | `outline_variant` | The colour of its border: a colour or a gradient. |
| `border_width` | `1.0` | The width of its border, in pixels. |

## What it makes

With `width: 120, height: 40`, each part's style is:

```yaml
root: {width: 120, height: 40, background: surface, corner_radius: medium, border_color: outline_variant,
  border_width: 1.0}
```

## Changing it

Put a `CardOutlined_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
