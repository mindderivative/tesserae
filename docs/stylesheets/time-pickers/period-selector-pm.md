# PeriodSelectorPM_Stylesheet.yaml

A time picker's AM / PM selector, with PM selected.

The look of [`PeriodSelectorPM`](../../components/time-pickers.md) (in [Time picker](../../components/time-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# PeriodSelectorPM: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: vertical
      width: 52
      height: 72
  - id: am
    style:
      width: 52
      height: 36
      background: transparent
      corner_radius: small
      align_content: center
  - id: am_label
    style:
      foreground: on_surface
  - id: pm
    style:
      width: 52
      height: 36
      background: tertiary_container
      corner_radius: small
      align_content: center
  - id: pm_label
    style:
      foreground: on_tertiary_container
```

## How it is tied to the component

`PeriodSelectorPM_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: PeriodSelectorPM`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `width` | `52` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `72` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

### `am` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `52` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `36` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `small` | Pixels, or a shape token (`none` to `extra_large`). |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `am_label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

### `pm` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `52` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `36` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `tertiary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `small` | Pixels, or a shape token (`none` to `extra_large`). |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |

### `pm_label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_tertiary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With ``, each part's style is:

```yaml
root: {flex_direction: vertical, width: 52, height: 72}
am: {width: 52, height: 36, background: transparent, corner_radius: small, align_content: center}
am_label: {foreground: on_surface}
pm: {width: 52, height: 36, background: tertiary_container, corner_radius: small, align_content: center}
pm_label: {foreground: on_tertiary_container}
```

## Changing it

Put a `PeriodSelectorPM_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: am
    style: {background: tertiary}
```
