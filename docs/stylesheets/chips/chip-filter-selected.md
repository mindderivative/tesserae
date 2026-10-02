# ChipFilterSelected_Stylesheet.yaml

A filter chip, selected: shows a check mark and the selected colour.

The look of [`ChipFilterSelected`](../../components/chips.md) (in [Chips](../../components/chips.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ChipFilterSelected: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 32
      align_items: center
      padding:
        left: 16
        right: 16
        top: 0
        bottom: 0
      gap: 8
      background: secondary_container
      corner_radius: small
  - id: check
    style:
      width: 18
      height: 18
      foreground: on_secondary_container
  - id: label
    style:
      foreground: on_secondary_container
```

## How it is tied to the component

`ChipFilterSelected_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ChipFilterSelected`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `32` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `padding` | left `16`, right `16`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `8` | Space between its children. |
| `background` | `secondary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `small` | Pixels, or a shape token (`none` to `extra_large`). |

### `check` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `18` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `18` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `label: Go, width: 120`, each part's style is:

```yaml
root:
  width: 120
  height: 32
  align_items: center
  padding: {left: 16, right: 16, top: 0, bottom: 0}
  gap: 8
  background: secondary_container
  corner_radius: small
check: {width: 18, height: 18, foreground: on_secondary_container}
label: {foreground: on_secondary_container}
```

## Changing it

Put a `ChipFilterSelected_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
