# Menu_Stylesheet.yaml

A menu: a surface listing choices, each a menu item.

The look of [`Menu`](../../components/menus.md) (in [Menus](../../components/menus.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# Menu: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      flex_direction: vertical
      background: surface_container
      corner_radius: extra_small
      elevation: level_2
      padding:
        left: 0
        right: 0
        top: 8
        bottom: 8
```

## How it is tied to the component

`Menu_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: Menu`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `background` | `surface_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `extra_small` | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_2` | A shadow level, 0 to 5. |
| `padding` | left `0`, right `0`, top `8`, bottom `8` | Space inside it: one number, or `{left, right, top, bottom}`. |

## What it makes

With `width: 120`, and a list of items, each part's style is:

```yaml
root:
  width: 120
  flex_direction: vertical
  background: surface_container
  corner_radius: extra_small
  elevation: level_2
  padding: {left: 0, right: 0, top: 8, bottom: 8}
item.0:
  width: 120
  height: 48
  align_content: left
  padding: {left: 12, right: 12, top: 0, bottom: 0}
item.0.label: {foreground: on_surface, flex: expand_horizontal, min_width: 0}
item.1:
  width: 120
  height: 48
  align_content: left
  padding: {left: 12, right: 12, top: 0, bottom: 0}
item.1.label: {foreground: on_surface, flex: expand_horizontal, min_width: 0}
```

## Changing it

Put a `Menu_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
