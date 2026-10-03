# BadgeLabeled_Stylesheet.yaml

A small pill carrying a short count or label.

The look of [`BadgeLabeled`](../../components/badges.md) (in [Badges](../../components/badges.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# BadgeLabeled: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 16
      background: error
      corner_radius: small
      justify_content: center
      align_items: center
  - id: label
    style:
      foreground: on_error
      flex_grow: 1
      min_width: 0
```

## How it is tied to the component

`BadgeLabeled_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: BadgeLabeled`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `16` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `error` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `small` | Pixels, or a shape token (`none` to `extra_large`). |
| `justify_content` | `center` | Where its children sit along the layout axis. |
| `align_items` | `center` | Where its children sit across the layout axis. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_error` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |
| `flex_grow` | `1` | How much of the spare room it takes, relative to its siblings. |
| `min_width` | `0` | The least width it can take. |

## What it makes

With `label: Go, width: 120`, each part's style is:

```yaml
root: {width: 120, height: 16, background: error, corner_radius: small, justify_content: center, align_items: center}
label: {foreground: on_error, flex_grow: 1, min_width: 0}
```

## Changing it

Put a `BadgeLabeled_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
