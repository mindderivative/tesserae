# Tabs_Stylesheet.yaml

Tabs: a row of destinations in one view, with the selected one marked.

The look of [`Tabs`](../../components/tabs.md) (in [Tabs](../../components/tabs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# Tabs: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      flex_direction: vertical
      background: surface
  - id: row
    style:
      flex_direction: horizontal
  - id: divider
    style:
      width: 100%
      height: 1
      background: surface_variant
```

## How it is tied to the component

`Tabs_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: Tabs`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |

### `row` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_direction` | `horizontal` | How its children are laid out: `horizontal` (the default) or `vertical`. |

### `divider` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `100%` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `1` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_variant` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |

## What it makes

With `item_width: 100`, and a list of items, each part's style is:

```yaml
root: {flex_direction: vertical, background: surface}
row: {flex_direction: horizontal}
item.0: {width: 100, height: 48, background: surface, flex_direction: vertical, align_content: center}
item.0.tab: {height: 48, flex_direction: vertical}
item.0.top: {height: 3, background: transparent}
item.0.content: {flex: expand_vertical, flex_direction: vertical, align_content: center, gap: 2}
item.0.label: {foreground: primary}
item.0.indicator: {height: 3, corner_radius: 3, background: primary}
item.1: {width: 100, height: 48, background: surface, flex_direction: vertical, align_content: center}
item.1.tab: {height: 48, flex_direction: vertical}
item.1.top: {height: 3, background: transparent}
item.1.content: {flex: expand_vertical, flex_direction: vertical, align_content: center, gap: 2}
item.1.label: {foreground: on_surface_variant}
item.1.indicator: {height: 3, corner_radius: 3, background: transparent}
divider: {width: 100%, height: 1, background: surface_variant}
```

## Changing it

Put a `Tabs_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
