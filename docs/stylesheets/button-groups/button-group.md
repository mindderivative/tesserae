# ButtonGroup_Stylesheet.yaml

A row of buttons, each made from the same button fragment.

The look of [`ButtonGroup`](../../components/button-groups.md) (in [Button groups](../../components/button-groups.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ButtonGroup: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: horizontal
      gap: 8
```

## How it is tied to the component

`ButtonGroup_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ButtonGroup`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `gap` | `8` | Space between its children. |

## What it makes

With `width: 120, height: 40, corner_radius: 20, button: ButtonFilled`, and a list of items, each part's style is:

```yaml
root: {flex_direction: horizontal, gap: 8}
b.0:
  width: 120
  height: 40
  align_items: center
  justify_content: center
  background: primary
  corner_radius: 20
  padding: {left: 12, right: 12, top: 0, bottom: 0}
b.0.label: {foreground: on_primary, flex_grow: 1, min_width: 0}
b.1:
  width: 120
  height: 40
  align_items: center
  justify_content: center
  background: primary
  corner_radius: 20
  padding: {left: 12, right: 12, top: 0, bottom: 0}
b.1.label: {foreground: on_primary, flex_grow: 1, min_width: 0}
```

## Changing it

Put a `ButtonGroup_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {flex_direction: tertiary}
```
