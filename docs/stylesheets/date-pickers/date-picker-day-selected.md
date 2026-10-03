# DatePickerDaySelected_Stylesheet.yaml

The selected day in a date picker's grid: a filled circle.

The look of [`DatePickerDaySelected`](../../components/date-pickers.md) (in [Date picker](../../components/date-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# DatePickerDaySelected: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: 48
      height: 48
      background: primary
      corner_radius: 24
      justify_content: center
      align_items: center
  - id: label
    style:
      foreground: on_primary
```

## How it is tied to the component

`DatePickerDaySelected_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: DatePickerDaySelected`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `primary` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`). |
| `justify_content` | `center` | Where its children sit along the layout axis. |
| `align_items` | `center` | Where its children sit across the layout axis. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_primary` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `day: 7`, each part's style is:

```yaml
root: {width: 48, height: 48, background: primary, corner_radius: 24, justify_content: center, align_items: center}
label: {foreground: on_primary}
```

## Changing it

Put a `DatePickerDaySelected_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
