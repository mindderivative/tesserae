# BadgeDot_Stylesheet.yaml

A small dot that marks something as having news, with no number.

The look of [`BadgeDot`](../../components/badges.md) (in [Badges](../../components/badges.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# BadgeDot: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: 6
      height: 6
      background: error
      corner_radius: 3
```

## How it is tied to the component

`BadgeDot_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: BadgeDot`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `6` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `6` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `error` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `3` | Pixels, or a shape token (`none` to `extra_large`). |

## What it makes

With ``, each part's style is:

```yaml
root: {width: 6, height: 6, background: error, corner_radius: 3}
```

## Changing it

Put a `BadgeDot_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
