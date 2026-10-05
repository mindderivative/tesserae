# SideSheetModal_Stylesheet.yaml

A modal side sheet: a panel at the side of the window, over a scrim.

The look of [`SideSheetModal`](../../components/side-sheets.md) (in [Side sheets](../../components/side-sheets.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# SideSheetModal: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ scrim_width }}"
      height: "{{ scrim_height }}"
      background: '#00000052'
      align_content: top_right
  - id: panel
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      background: surface_container_low
      corner_radius: large
      elevation: level_1
```

## How it is tied to the component

`SideSheetModal_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: SideSheetModal`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `scrim_width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `scrim_height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `#00000052` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `align_content` | `top_right` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `panel` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_container_low` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `large` | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_1` | A shadow level, 0 to 5. |

## What it makes

With `width: 120, height: 40, scrim_width: 400, scrim_height: 300`, each part's style is:

```yaml
root: {width: 400, height: 300, background: '#00000052', align_content: top_right}
panel: {width: 120, height: 40, background: surface_container_low, corner_radius: large, elevation: level_1}
```

## Changing it

Put a `SideSheetModal_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
