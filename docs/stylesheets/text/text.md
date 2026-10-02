# Text_Stylesheet.yaml

Text in one of MD3's type styles and a colour.

The look of [`Text`](../../components/text.md) (in [Text](../../components/text.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# Text: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      foreground: "{{ color }}"
```

## How it is tied to the component

`Text_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: Text`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Text)

| Field | Value | What it does |
| --- | --- | --- |
| `foreground` | the `color` parameter | Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour. |

## What it makes

With `text: Hello, typography_role: body_large, color: primary`, each part's style is:

```yaml
root: {foreground: primary}
```

## Changing it

Put a `Text_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {foreground: tertiary}
```
