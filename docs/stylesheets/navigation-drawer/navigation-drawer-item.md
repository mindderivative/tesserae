# NavigationDrawerItem_Stylesheet.yaml

One destination in a navigation drawer: an icon and a label, highlighted when selected.

The look of [`NavigationDrawerItem`](../../components/navigation-drawer.md) (in [Navigation drawer](../../components/navigation-drawer.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# NavigationDrawerItem: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 56
      corner_radius: 28
      background:
        if: "{{ selected }}"
        then: secondary_container
        else: transparent
      flex_direction: horizontal
      align_content: left
      gap: 12
      padding:
        left: 16
        right: 24
        top: 0
        bottom: 0
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
        then: on_secondary_container
        else: on_surface_variant
      flex: expand_horizontal
      min_width: 0
```

## How it is tied to the component

`NavigationDrawerItem_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: NavigationDrawerItem`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `corner_radius` | `28` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square. |
| `background` | `secondary_container` if `selected`, else `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `align_content` | `left` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `gap` | `12` | Space between its children. |
| `padding` | left `16`, right `24`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_secondary_container` if `selected`, else `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_secondary_container` if `selected`, else `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `flex` | `expand_horizontal` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| `min_width` | `0` | The least width it can take. |

## What it makes

With `label: Go, icon: home, width: 120, selected: False`, each part's style is:

```yaml
root:
  width: 120
  height: 56
  corner_radius: 28
  background: transparent
  flex_direction: horizontal
  align_content: left
  gap: 12
  padding: {left: 16, right: 24, top: 0, bottom: 0}
icon: {width: 24, height: 24, foreground: on_surface_variant}
label: {foreground: on_surface_variant, flex: expand_horizontal, min_width: 0}
```

## Changing it

Put a `NavigationDrawerItem_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
