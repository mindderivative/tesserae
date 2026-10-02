# TimePickerDial_Stylesheet.yaml

A time picker dial: a clock face for picking the hour, then the minute.

The look of [`TimePickerDial`](../../components/time-pickers.md) (in [Time picker](../../components/time-pickers.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# TimePickerDial: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ size }}"
      height: "{{ size }}"
```

## How it is tied to the component

`TimePickerDial_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: TimePickerDial`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (TimePickerDial)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `size` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |

## What it makes

With `size: 40, hour: 3, minute: 15`, each part's style is:

```yaml
root: {width: 40, height: 40}
```

## Changing it

Put a `TimePickerDial_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {width: tertiary}
```
