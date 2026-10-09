# Snackbar_Stylesheet.yaml

A snackbar: a short message about a process, at the bottom of the window.

The look of [`Snackbar`](../../components/snackbars.md) (in [Snackbars](../../components/snackbars.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# Snackbar: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 48
      background: inverse_surface
      corner_radius: extra_small
      elevation: level_3
      align_content: left
      padding:
        left: 16
        right: 16
        top: 0
        bottom: 0
  - id: text
    style:
      foreground: inverse_on_surface
      flex: expand_horizontal
```

## How it is tied to the component

`Snackbar_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: Snackbar`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `inverse_surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| `corner_radius` | `extra_small` | Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). |
| `elevation` | `level_3` | A shadow level, 0 to 5. |
| `align_content` | `left` | Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom` or `bottom_right`. Not set, they fill the space across the layout. |
| `padding` | left `16`, right `16`, top `0`, bottom `0` | Space inside it: one number, or `{left, right, top, bottom}`. |

### `text` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `inverse_on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |
| `flex` | `expand_horizontal` | How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, `expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both. |

## What it makes

With `text: Hello, width: 120`, each part's style is:

```yaml
root:
  width: 120
  height: 48
  background: inverse_surface
  corner_radius: extra_small
  elevation: level_3
  align_content: left
  padding: {left: 16, right: 16, top: 0, bottom: 0}
text: {foreground: inverse_on_surface, flex: expand_horizontal}
```

## Changing it

Put a `Snackbar_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
