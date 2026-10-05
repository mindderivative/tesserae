# SideSheetStandard_Stylesheet.yaml

A standard side sheet: a panel at the side that shares the window with the content.

The look of [`SideSheetStandard`](../../components/side-sheets.md) (in [Side sheets](../../components/side-sheets.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# SideSheetStandard: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      background: surface
      corner_radius: large
```

## How it is tied to the component

`SideSheetStandard_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: SideSheetStandard`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `large` | Pixels, or a shape token (`none` to `extra_large`). |

## What it makes

With `width: 120, height: 40`, each part's style is:

```yaml
root: {width: 120, height: 40, background: surface, corner_radius: large}
```

## Changing it

Put a `SideSheetStandard_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
