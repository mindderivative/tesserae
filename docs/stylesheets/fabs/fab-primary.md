# FabPrimary_Stylesheet.yaml

A floating action button in the primary colour: the screen's main action.

The look of [`FabPrimary`](../../components/fabs.md) (in [Floating action buttons](../../components/fabs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# FabPrimary: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ size }}"
      height: "{{ size }}"
      align_content: center
      background: primary_container
      corner_radius: "{{ corner_radius }}"
      elevation: level_3
  - id: icon
    style:
      width: 24
      height: 24
      foreground: on_primary_container
```

## How it is tied to the component

`FabPrimary_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: FabPrimary`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `background` | `primary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_3` | A shadow level, 0 to 5. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_primary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `icon: home, size: 40, corner_radius: 20, fab_size: default`, each part's style is:

```yaml
root: {width: 40, height: 40, align_content: center, background: primary_container, corner_radius: 20,
  elevation: level_3}
icon: {width: 24, height: 24, foreground: on_primary_container}
```

## Changing it

Put a `FabPrimary_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
