# NavigationRailItem_Stylesheet.yaml

One destination in a navigation rail: an icon in a pill, with a label under it.

The look of [`NavigationRailItem`](../../components/navigation-rail.md) (in [Navigation rail](../../components/navigation-rail.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# NavigationRailItem: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: 80
      height: 56
      flex_direction: vertical
      align_content: top
      gap: 4
  - id: pill
    style:
      width: 56
      height: 32
      corner_radius: 16
      background:
        if: "{{ selected }}"
        then: secondary_container
        else: transparent
      align_content: center
  - id: icon
    style:
      width: 24
      height: 24
      foreground:
        if: "{{ selected }}"
        then: on_secondary_container
        else: on_surface_variant
  - id: label
    style:
      foreground:
        if: "{{ selected }}"
        then: on_surface
        else: on_surface_variant
```

## How it is tied to the component

`NavigationRailItem_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: NavigationRailItem`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `80` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `align_content` | `top` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `gap` | `4` | Space between its children. |

### `pill` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `32` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `corner_radius` | `16` | Pixels, or a shape token (`none` to `extra_large`). |
| `background` | `secondary_container` if `selected`, else `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_secondary_container` if `selected`, else `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` if `selected`, else `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `label: Go, icon: home, selected: False`, each part's style is:

```yaml
root: {width: 80, height: 56, flex_direction: vertical, align_content: top, gap: 4}
pill: {width: 56, height: 32, corner_radius: 16, background: transparent, align_content: center}
icon: {width: 24, height: 24, foreground: on_surface_variant}
label: {foreground: on_surface_variant}
```

## Changing it

Put a `NavigationRailItem_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: pill
    style: {background: tertiary}
```
