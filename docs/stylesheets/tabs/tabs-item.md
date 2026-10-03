# TabsItem_Stylesheet.yaml

One tab: a label, and an icon if you want one, with an indicator when selected.

The look of [`TabsItem`](../../components/tabs.md) (in [Tabs](../../components/tabs.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# TabsItem: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height:
        if: "{{ icon }}"
        then: 64
        else: 48
      background: surface
      flex_direction: vertical
      align_items: center
      justify_content: center
  - id: tab
    style:
      height:
        if: "{{ icon }}"
        then: 64
        else: 48
      flex_direction: vertical
      align_items: stretch
  - id: top
    style:
      height: 3
      background: transparent
  - id: content
    style:
      flex_grow: 1
      flex_direction: vertical
      align_items: center
      justify_content: center
      gap: 2
  - id: icon
    style:
      width: 24
      height: 24
      foreground:
        if: "{{ selected }}"
        then: primary
        else: on_surface_variant
  - id: label
    style:
      foreground:
        if: "{{ selected }}"
        then: primary
        else: on_surface_variant
      flex_shrink: 0
  - id: indicator
    style:
      height: 3
      corner_radius: 3
      background:
        if: "{{ selected }}"
        then: primary
        else: transparent
```

## How it is tied to the component

`TabsItem_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: TabsItem`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `64` if `icon`, else `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `justify_content` | `center` | Where its children sit along the layout axis. |

### `tab` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `height` | `64` if `icon`, else `48` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `align_items` | `stretch` | Where its children sit across the layout axis. |

### `top` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `height` | `3` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |

### `content` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `flex_grow` | `1` | How much of the spare room it takes, relative to its siblings. |
| `flex_direction` | `vertical` | How its children are laid out: `horizontal` (the default) or `vertical`. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `justify_content` | `center` | Where its children sit along the layout axis. |
| `gap` | `2` | Space between its children. |

### `icon` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `primary` if `selected`, else `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

### `label` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `primary` if `selected`, else `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |
| `flex_shrink` | `0` | How much it gives up when there is too little room. |

### `indicator` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `height` | `3` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `corner_radius` | `3` | Pixels, or a shape token (`none` to `extra_large`). |
| `background` | `primary` if `selected`, else `transparent` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |

## What it makes

With `label: Go, width: 120, icon: home, selected: False`, each part's style is:

```yaml
root: {width: 120, height: 64, background: surface, flex_direction: vertical, align_items: center, justify_content: center}
tab: {height: 64, flex_direction: vertical, align_items: stretch}
top: {height: 3, background: transparent}
content: {flex_grow: 1, flex_direction: vertical, align_items: center, justify_content: center, gap: 2}
icon: {width: 24, height: 24, foreground: on_surface_variant}
label: {foreground: on_surface_variant, flex_shrink: 0}
indicator: {height: 3, corner_radius: 3, background: transparent}
```

## Changing it

Put a `TabsItem_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
