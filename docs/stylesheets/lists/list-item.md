# ListItem_Stylesheet.yaml

A list row: a headline, and room for more.

The look of [`ListItem`](../../components/lists.md) (in [Lists](../../components/lists.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ListItem: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 56
      align_content: left
      padding: 16
  - id: headline
    style:
      foreground: on_surface
      flex: expand_horizontal
      min_width: 0
```

## How it is tied to the component

`ListItem_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ListItem`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `left` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `padding` | `16` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `headline` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |
| `flex` | `expand_horizontal` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |
| `min_width` | `0` | The least width it can take. |

## What it makes

With `headline: Headline, width: 120`, each part's style is:

```yaml
root: {width: 120, height: 56, align_content: left, padding: 16}
headline: {foreground: on_surface, flex: expand_horizontal, min_width: 0}
```

## Changing it

Put a `ListItem_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: headline
    style: {foreground: tertiary}
```
