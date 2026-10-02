# AccordionHeader_Stylesheet.yaml

A section header that expands and collapses its content: a title and a chevron.

The look of [`AccordionHeader`](../../components/accordions.md) (in [Accordions](../../components/accordions.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# AccordionHeader: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: 56
      align_items: center
      padding: 16
      gap: 12
  - id: title
    style:
      foreground: on_surface
      flex_grow: 1
  - id: chevron
    style:
      width: 24
      height: 24
      foreground: on_surface_variant
```

## How it is tied to the component

`AccordionHeader_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: AccordionHeader`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Container)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `56` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `align_items` | `center` | Where its children sit across the layout axis. |
| `padding` | `16` | Space inside it: one number, or `{left, right, top, bottom}`. |
| `gap` | `12` | Space between its children. |

### `title` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | `on_surface` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |
| `flex_grow` | `1` | How much of the spare room it takes, relative to its siblings. |

### `chevron` (Icon)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | `24` | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | `on_surface_variant` | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `title: Title, width: 120`, each part's style is:

```yaml
root: {width: 120, height: 56, align_items: center, padding: 16, gap: 12}
title: {foreground: on_surface, flex_grow: 1}
chevron: {width: 24, height: 24, foreground: on_surface_variant}
```

## Changing it

Put a `AccordionHeader_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: title
    style: {foreground: tertiary}
```
