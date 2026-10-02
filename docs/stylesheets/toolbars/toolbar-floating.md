# ToolbarFloating_Stylesheet.yaml

A floating toolbar: a rounded bar of actions over the content.

The look of [`ToolbarFloating`](../../components/toolbars.md) (in [Toolbars](../../components/toolbars.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ToolbarFloating: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: horizontal
      width: "{{ width }}"
      height: 64
      background: "{{ background }}"
      corner_radius: "{{ corner_radius }}"
      elevation: level_3
      align_items: center
      justify_content: center
      padding: 16
      gap: 32
```

## How it is tied to the component

`ToolbarFloating_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ToolbarFloating`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `64` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | the `background` parameter | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_3` | A shadow level, 0 to 5. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `justify_content` | `center` | Where its children sit along the layout axis. |
| `padding` | `16` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `32` | Space between its children. |

## What it makes

With `background: primary, width: 120, corner_radius: 20`, each part's style is:

```yaml
root: {flex_direction: horizontal, width: 120, height: 64, background: primary, corner_radius: 20, elevation: level_3,
  align_items: center, justify_content: center, padding: 16, gap: 32}
```

## Changing it

Put a `ToolbarFloating_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
