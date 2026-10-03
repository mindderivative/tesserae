# ToolbarDocked_Stylesheet.yaml

A docked toolbar: a bar of actions fixed to an edge of the window.

The look of [`ToolbarDocked`](../../components/toolbars.md) (in [Toolbars](../../components/toolbars.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ToolbarDocked: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: horizontal
      width: "{{ width }}"
      height: 64
      background: "{{ background }}"
      align_content: center
      padding: 16
      gap: 32
```

## How it is tied to the component

`ToolbarDocked_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ToolbarDocked`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `64` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | the `background` parameter | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `padding` | `16` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `32` | Space between its children. |

## What it makes

With `background: primary, width: 120`, each part's style is:

```yaml
root: {flex_direction: horizontal, width: 120, height: 64, background: primary, align_content: center,
  padding: 16, gap: 32}
```

## Changing it

Put a `ToolbarDocked_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
