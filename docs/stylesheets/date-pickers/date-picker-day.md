# DatePickerDay_Stylesheet.yaml

One day in a date picker's month grid.

The look of [`DatePickerDay`](../../components/date-pickers.md) (in [Date picker](../../components/date-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# DatePickerDay: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: 48
      height: 48
      background: transparent
      corner_radius: 24
      align_content: center
  - id: label
    style:
      foreground: on_surface
```

## How it is tied to the component

`DatePickerDay_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: DatePickerDay`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`). |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `day: 7`, each part's style is:

```yaml
root: {width: 48, height: 48, background: transparent, corner_radius: 24, align_content: center}
label: {foreground: on_surface}
```

## Changing it

Put a `DatePickerDay_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
