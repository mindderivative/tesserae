# Divider_Stylesheet.yaml

The look of Divider (Material 3): a line in outline_variant that fills the length it is in (in a container that does not set `align_content`). The insets are margins at the ends it keeps clear.

The look of [`Divider`](../../components/dividers.md) (in [Dividers](../../components/dividers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# The look of Divider (Material 3): a line in outline_variant that fills the length it is in (in a container that does not set `align_content`). The insets are margins at the ends it keeps clear.
styles:
  - widget: Divider
    style:
      background: outline_variant
      width: "{{ thickness if orientation == 'vertical' else 'auto' }}"
      height: "{{ thickness if orientation == 'horizontal' else 'auto' }}"

  - widget: Divider
    variant: inset
    style:
      margin: "{{ {'left': 16} if orientation == 'horizontal' else {'top': 16} }}"

  - widget: Divider
    variant: middle
    style:
      margin: "{{ {'left': 16, 'right': 16} if orientation == 'horizontal' else {'top': 16, 'bottom': 16} }}"
```

## How it reaches the view

Each rule names `widget: Divider` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` beats every rule for the fields it sets.

## The rules

### `Divider` itself

| When | Field | Value | What it does |
| --- | --- | --- | --- |
| always | `background` | `outline_variant` | Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as `linear-gradient(90deg, primary, tertiary)`. |
| always | `width` | `{{ thickness if orientation == 'vertical' else 'auto' }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| always | `height` | `{{ thickness if orientation == 'horizontal' else 'auto' }}` | Pixels, `auto` (its content's size, or stretched), `fit-content`, a percentage of the parent such as `50%`, or a sum such as `calc(100% - 16)` or `100% - 16` (a space each side of `+` and `-`; `16px` may be written inside a sum). |
| `variant: inset` | `margin` | `{{ {'left': 16} if orientation == 'horizontal' else {'top': 16} }}` | Space outside it: one number, or `{left, right, top, bottom}`. |
| `variant: middle` | `margin` | `{{ {'left': 16, 'right': 16} if orientation == 'horizontal' else {'top': 16, 'bottom': 16} }}` | Space outside it: one number, or `{left, right, top, bottom}`. |

## Changing it

Write a rule of your own; it goes over this file's, field by field:

```yaml
styles:
  - widget: Divider
    style: {background: tertiary}
```
