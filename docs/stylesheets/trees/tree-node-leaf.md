# TreeNodeLeaf_Stylesheet.yaml

A tree row with nothing under it: a title, indented by its depth.

The look of [`TreeNodeLeaf`](../../components/trees.md) (in [Trees](../../components/trees.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# TreeNodeLeaf: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 56
      align_items: center
      padding:
        left: "{{ left_padding }}"
        right: 16
        top: 0
        bottom: 0
  - id: title
    style:
      foreground: on_surface
      flex_grow: 1
      min_width: 0
```

## How it is tied to the component

`TreeNodeLeaf_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: TreeNodeLeaf`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `padding` | left the `left_padding` parameter, right `16`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `title` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |
| `flex_grow` | `1` | How much of the spare room it takes, relative to its siblings. |
| `min_width` | `0` | The least width it can take. |

## What it makes

With `title: Title, width: 120, left_padding: 16`, each part's style is:

```yaml
root:
  width: 120
  height: 56
  align_items: center
  padding: {left: 16, right: 16, top: 0, bottom: 0}
title: {foreground: on_surface, flex_grow: 1, min_width: 0}
```

## Changing it

Put a `TreeNodeLeaf_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: title
    style: {foreground: tertiary}
```
