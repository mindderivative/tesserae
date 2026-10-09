# DatePickerDayToday_Stylesheet.yaml

Today in a date picker's grid: an outlined circle.

The look of [`DatePickerDayToday`](../../components/date-pickers.md) (in [Date picker](../../components/date-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# DatePickerDayToday: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: 48
      height: 48
      background: transparent
      corner_radius: 24
      border_color: primary
      border_width: 1.0
      align_content: center
  - id: label
    style:
      foreground: primary
```

## How it is tied to the component

`DatePickerDayToday_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: DatePickerDayToday`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `24` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). |
| `border_color` | `primary` | The colour of its border: a colour or a gradient. |
| `border_width` | `1.0` | The width of its border, in pixels. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `day: 7`, each part's style is:

```yaml
root: {width: 48, height: 48, background: transparent, corner_radius: 24, border_color: primary, border_width: 1.0,
  align_content: center}
label: {foreground: primary}
```

## Changing it

Put a `DatePickerDayToday_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
