# ButtonFilled_Stylesheet.yaml

A filled button: the highest-emphasis button, for a screen's main action.

The look of [`ButtonFilled`](../../components/buttons.md) (in [Buttons](../../components/buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ButtonFilled: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      align_items: center
      justify_content: center
      background: primary
      corner_radius: "{{ corner_radius }}"
      padding:
        left: 12
        right: 12
        top: 0
        bottom: 0
  - id: label
    style:
      foreground: on_primary
```

## How it is tied to the component

`ButtonFilled_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ButtonFilled`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `justify_content` | `center` | Where its children sit along the layout axis. |
| `background` | `primary` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`). |
| `padding` | left `12`, right `12`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_primary` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `label: Go, width: 120, height: 40, corner_radius: 20`, each part's style is:

```yaml
root:
  width: 120
  height: 40
  align_items: center
  justify_content: center
  background: primary
  corner_radius: 20
  padding: {left: 12, right: 12, top: 0, bottom: 0}
label: {foreground: on_primary}
```

## Changing it

Put a `ButtonFilled_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
