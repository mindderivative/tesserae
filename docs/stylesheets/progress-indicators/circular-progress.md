# CircularProgress_Stylesheet.yaml

A circular progress indicator: determinate with a value, indeterminate without.

The look of [`CircularProgress`](../../components/progress-indicators.md) (in [Progress indicators](../../components/progress-indicators.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# CircularProgress: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ size }}"
      height: "{{ size }}"
```

## How it is tied to the component

`CircularProgress_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: CircularProgress`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (CircularProgress)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

## What it makes

With `size: 40, value: 0.5`, each part's style is:

```yaml
root: {width: 40, height: 40}
```

## Changing it

Put a `CircularProgress_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {width: tertiary}
```
