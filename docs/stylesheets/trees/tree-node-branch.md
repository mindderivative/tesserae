# TreeNodeBranch_Stylesheet.yaml

A tree row that can be expanded: a title and a chevron, indented by its depth.

The look of [`TreeNodeBranch`](../../components/trees.md) (in [Trees](../../components/trees.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# TreeNodeBranch: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 56
      align_content: left
      padding:
        left: "{{ left_padding }}"
        right: 16
        top: 0
        bottom: 0
      gap: 12
  - id: title
    style:
      foreground: on_surface
      flex: expand_horizontal
      min_width: 0
  - id: chevron
    style:
      width: 24
      height: 24
      foreground: on_surface_variant
```

## How it is tied to the component

`TreeNodeBranch_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: TreeNodeBranch`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `left` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `padding` | left the `left_padding` parameter, right `16`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `12` | Space between its children. |

### `title` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |
| `flex` | `expand_horizontal` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| `min_width` | `0` | The least width it can take. |

### `chevron` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `title: Title, width: 120, left_padding: 16`, each part's style is:

```yaml
root:
  width: 120
  height: 56
  align_content: left
  padding: {left: 16, right: 16, top: 0, bottom: 0}
  gap: 12
title: {foreground: on_surface, flex: expand_horizontal, min_width: 0}
chevron: {width: 24, height: 24, foreground: on_surface_variant}
```

## Changing it

Put a `TreeNodeBranch_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: title
    style: {foreground: tertiary}
```
