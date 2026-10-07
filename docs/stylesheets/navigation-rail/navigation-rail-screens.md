# NavigationRailScreens_Stylesheet.yaml

A navigation rail whose destinations go to screens of the app: a narrow column of `NavigationRailScreen`s.

The look of [`NavigationRailScreens`](../../components/navigation-rail.md) (in [Navigation rail](../../components/navigation-rail.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# NavigationRailScreens: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: 80
      flex_direction: vertical
      align_content: top
      gap: 12
      padding:
        left: 0
        right: 0
        top: 12
        bottom: 12
      background: surface
```

## How it is tied to the component

`NavigationRailScreens_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: NavigationRailScreens`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `80` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `align_content` | `top` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `gap` | `12` | Space between its children. |
| `padding` | left `0`, right `0`, top `12`, bottom `12` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |

## What it makes

With ``, and a list of items, each part's style is:

```yaml
root:
  width: 80
  flex_direction: vertical
  align_content: top
  gap: 12
  padding: {left: 0, right: 0, top: 12, bottom: 12}
  background: surface
item.0: {width: 80, height: 56, flex_direction: vertical, align_content: top, gap: 4}
item.0.pill: {width: 56, height: 32, corner_radius: 16, background: transparent, align_content: center}
item.0.icon: {width: 24, height: 24, foreground: on_surface_variant}
item.0.label: {foreground: on_surface_variant}
item.1: {width: 80, height: 56, flex_direction: vertical, align_content: top, gap: 4}
item.1.pill: {width: 56, height: 32, corner_radius: 16, background: transparent, align_content: center}
item.1.icon: {width: 24, height: 24, foreground: on_surface_variant}
item.1.label: {foreground: on_surface_variant}
```

## Changing it

Put a `NavigationRailScreens_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
