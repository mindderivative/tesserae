# SearchView_Stylesheet.yaml

A search view: the full-size surface search results appear on.

The look of [`SearchView`](../../components/search.md) (in [Search](../../components/search.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# SearchView: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      background: surface_container_high
      corner_radius: extra_large
      elevation: level_3
```

## How it is tied to the component

`SearchView_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: SearchView`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_container_high` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `extra_large` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `elevation` | `level_3` | A shadow level, 0 to 5. |

## What it makes

With `width: 120, height: 40`, each part's style is:

```yaml
root: {width: 120, height: 40, background: surface_container_high, corner_radius: extra_large, elevation: level_3}
```

## Changing it

Put a `SearchView_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
