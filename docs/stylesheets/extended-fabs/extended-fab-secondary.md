# ExtendedFabSecondary_Stylesheet.yaml

An extended floating action button in the secondary colour.

The look of [`ExtendedFabSecondary`](../../components/extended-fabs.md) (in [Extended FABs](../../components/extended-fabs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# ExtendedFabSecondary: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: horizontal
      width: "{{ width }}"
      height: 56
      background: secondary_container
      corner_radius: large
      elevation: level_3
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
      align_content:
        if: "{{ icon }}"
        then: left
        else: center
      gap: 8
  - id: icon
    style:
      width: 24
      height: 24
      foreground: on_secondary_container
  - id: label
    style:
      foreground: on_secondary_container
```

## How it is tied to the component

`ExtendedFabSecondary_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: ExtendedFabSecondary`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `secondary_container` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `large` | Pixels, or a shape token (`none` to `extra_large`). |
| `elevation` | `level_3` | A shadow level, 0 to 5. |
| `padding` | left `16`, right `20`, top `0`, bottom `0` if `icon`, else left `20`, right `20`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `align_content` | `left` if `icon`, else `center` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `gap` | `8` | Space between its children. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_secondary_container` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `label: Go, width: 120, icon: home`, each part's style is:

```yaml
root:
  flex_direction: horizontal
  width: 120
  height: 56
  background: secondary_container
  corner_radius: large
  elevation: level_3
  padding: {left: 16, right: 20, top: 0, bottom: 0}
  align_content: left
  gap: 8
icon: {width: 24, height: 24, foreground: on_secondary_container}
label: {foreground: on_secondary_container}
```

## Changing it

Put a `ExtendedFabSecondary_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
