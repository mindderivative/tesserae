# LoadingIndicator_Stylesheet.yaml

A loading indicator: a shape that morphs while something loads.

The look of [`LoadingIndicator`](../../components/progress-indicators.md) (in [Progress indicators](../../components/progress-indicators.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# LoadingIndicator: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ size }}"
      height: "{{ size }}"
      foreground: "{{ background }}"
```

## How it is tied to the component

`LoadingIndicator_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: LoadingIndicator`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (LoadingIndicator)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `foreground` | the `background` parameter | Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient. |

## What it makes

With `size: 40, background: primary`, each part's style is:

```yaml
root: {width: 40, height: 40, foreground: primary}
```

## Changing it

Put a `LoadingIndicator_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {foreground: tertiary}
```
