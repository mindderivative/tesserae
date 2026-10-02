# LinearProgress_Stylesheet.yaml

A linear progress indicator: determinate with a value, indeterminate without.

The look of [`LinearProgress`](../../components/progress-indicators.md) (in [Progress indicators](../../components/progress-indicators.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# LinearProgress: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
```

## How it is tied to the component

`LinearProgress_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: LinearProgress`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (LinearProgress)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

## What it makes

With `width: 120, height: 40, value: 0.5`, each part's style is:

```yaml
root: {width: 120, height: 40}
```

## Changing it

Put a `LinearProgress_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {width: tertiary}
```
