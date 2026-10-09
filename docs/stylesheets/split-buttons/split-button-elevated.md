# SplitButtonElevated_Stylesheet.yaml

An elevated split button: an action, and a menu of related ones.

The look of [`SplitButtonElevated`](../../components/split-buttons.md) (in [Split buttons](../../components/split-buttons.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# SplitButtonElevated: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: horizontal
      gap: 2
  - id: leading
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      align_content: center
      background: surface_container_low
      corner_radius: "{{ corner_radius }}"
      elevation: level_1
      padding:
        left: 12
        right: 12
        top: 0
        bottom: 0
  - id: label
    style:
      foreground: primary
  - id: trailing
    style:
      width: "{{ height }}"
      height: "{{ height }}"
      align_content: center
      background: surface_container_low
      corner_radius: "{{ corner_radius }}"
      elevation: level_1
  - id: chevron
    style:
      width: 22
      height: 22
      foreground: primary
```

## How it is tied to the component

`SplitButtonElevated_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: SplitButtonElevated`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `gap` | `2` | Space between its children. |

### `leading` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `background` | `surface_container_low` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). |
| `elevation` | `level_1` | A shadow level, 0 to 5. |
| `padding` | left `12`, right `12`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `trailing` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_content` | `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `background` | `surface_container_low` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | the `corner_radius` parameter | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). |
| `elevation` | `level_1` | A shadow level, 0 to 5. |

### `chevron` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `22` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `22` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `label: Go, width: 120, height: 40, corner_radius: 20`, each part's style is:

```yaml
root: {flex_direction: horizontal, gap: 2}
leading:
  width: 120
  height: 40
  align_content: center
  background: surface_container_low
  corner_radius: 20
  elevation: level_1
  padding: {left: 12, right: 12, top: 0, bottom: 0}
label: {foreground: primary}
trailing: {width: 40, height: 40, align_content: center, background: surface_container_low, corner_radius: 20,
  elevation: level_1}
chevron: {width: 22, height: 22, foreground: primary}
```

## Changing it

Put a `SplitButtonElevated_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: leading
    style: {background: tertiary}
```
