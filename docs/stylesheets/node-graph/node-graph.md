# NodeGraph_Stylesheet.yaml

A pannable canvas for a node graph: its GraphNodes and the edges between them.

The look of [`NodeGraph`](../../components/node-graph.md) (in [Node graph](../../components/node-graph.md)). [How component stylesheets work](../index.md).

## The stylesheet

```yaml
# NodeGraph: the look of each part of the component, by the part's id.
# A value in {{ }} is one of the component's parameters.
styles:
  - id: root
    style:
      width: "{{ width }}"
      height: "{{ height }}"
      background: surface_container_low
```

## How it is tied to the component

`NodeGraph_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: each rule's `id` names a part, and its `style` is what that part looks like. When a view uses `component: NodeGraph`, Tesserae fills in the parameters (a value like `"{{ width }}"` becomes the `width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part already has, so a part's own `style:` always wins.

## The parts

### `root` (Rect)

| Field | Value | What it does |
| --- | --- | --- |
| `width` | the `width` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `height` | the `height` parameter | Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`. |
| `background` | `surface_container_low` | Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour. |

## What it makes

With `width: 120, height: 40`, each part's style is:

```yaml
root: {width: 120, height: 40, background: surface_container_low}
```

## Changing it

Put a `NodeGraph_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:

```yaml
styles:
  - id: root
    style: {background: tertiary}
```
