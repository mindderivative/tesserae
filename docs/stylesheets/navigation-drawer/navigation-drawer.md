# NavigationDrawer_Stylesheet.yaml

A navigation drawer: a vertical list of destinations.

The look of [`NavigationDrawer`](../../components/navigation-drawer.md) (in [Navigation drawer](../../components/navigation-drawer.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# NavigationDrawer: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      flex_direction: vertical
      padding: 12
      background: surface_container_low
```

## How it is tied to the component

`NavigationDrawer_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: NavigationDrawer`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `padding` | `12` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `background` | `surface_container_low` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |

## What it makes

With `width: 120, item_width: 100`, and a list of items, each part's style is:

```yaml
root: {width: 120, flex_direction: vertical, padding: 12, background: surface_container_low}
item.0:
  width: 100
  height: 56
  corner_radius: 28
  background: secondary_container
  flex_direction: horizontal
  align_items: center
  gap: 12
  padding: {left: 16, right: 24, top: 0, bottom: 0}
item.0.icon: {width: 24, height: 24, foreground: on_secondary_container}
item.0.label: {foreground: on_secondary_container, flex_grow: 1, min_width: 0}
item.1:
  width: 100
  height: 56
  corner_radius: 28
  background: transparent
  flex_direction: horizontal
  align_items: center
  gap: 12
  padding: {left: 16, right: 24, top: 0, bottom: 0}
item.1.icon: {width: 24, height: 24, foreground: on_surface_variant}
item.1.label: {foreground: on_surface_variant, flex_grow: 1, min_width: 0}
```

## Changing it

Put a `NavigationDrawer_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
