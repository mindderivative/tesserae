# ExtendedFabSurface_Stylesheet.yaml

An extended floating action button on the surface colour.

The look of [`ExtendedFabSurface`](../../components/extended-fabs.md) (in [Extended FABs](../../components/extended-fabs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ExtendedFabSurface: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: horizontal
      width: "{{ width }}"
      height: 56
      background: surface_container_high
      corner_radius: large
      elevation: level_3
      align_items: center
      padding:
        if: "{{ icon }}"
        then:
          left: 16
          right: 20
          top: 0
          bottom: 0
        else:
          left: 20
          right: 20
          top: 0
          bottom: 0
      justify_content:
        if: "{{ icon }}"
        then: flex_start
        else: center
      gap: 8
  - id: icon
    style:
      width: 24
      height: 24
      foreground: primary
  - id: label
    style:
      foreground: primary
```

## How it is tied to the component

`ExtendedFabSurface_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ExtendedFabSurface`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_container_high` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `corner_radius` | `large` | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_3` | A shadow level, 0 to 5. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `padding` | left `16`, right `20`, top `0`, bottom `0` if `icon`, else left `20`, right `20`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `justify_content` | `flex_start` if `icon`, else `center` | Where its children sit along the layout axis. |
| `gap` | `8` | Space between its children. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `primary` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `label: Go, width: 120, icon: home`, each part's style is:

```yaml
root:
  flex_direction: horizontal
  width: 120
  height: 56
  background: surface_container_high
  corner_radius: large
  elevation: level_3
  align_items: center
  padding: {left: 16, right: 20, top: 0, bottom: 0}
  justify_content: flex_start
  gap: 8
icon: {width: 24, height: 24, foreground: primary}
label: {foreground: primary}
```

## Changing it

Put a `ExtendedFabSurface_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
