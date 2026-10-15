# Node graph

*Beyond MD3*

## In Material Design 3

Material Design 3 has no node graph. This is a pannable canvas of titled boxes joined by edges, for tools.

## In Tesserae

The `NodeGraph` kind (`widget: NodeGraph` in a view), with `GraphNode` children at an `x` and a `y`. Drag the background to pan, the wheel zooms about the pointer, drag a node (or
press the arrow keys on a focused one) to move it, and its edges follow.

`edges` are the links, each `{from: id, to: id}`, the ids of the `GraphNode`s: their path from the view's root, as `root.graph.load` for the node `load` in the graph `graph`; an edge runs from the right side of one node to the left of the other, as a curve. `snap`
makes a node the user moves land on a multiple of that many pixels (an arrow key steps one square, or 8 pixels with no grid; `0` is no grid), `arrows` ends each edge in an arrowhead, and `fit`
pans and zooms when it opens so every node shows (never past actual size). A `GraphNode` has a `label` (its title), an `x` and a `y` in the graph's own coordinates, and its
size from `style`; what it holds goes in its body.

Pressing a node chooses it (a `primary` border, and it is selected to a screen reader); pressing the background chooses none. From Python the widget has `fit_to_view(padding)`,
`zoom`, `offset`, `snap`, `arrows` and `selected` (a `Signal` of the node chosen). Not built: ports and dragging to connect, labels on edges, selecting several, a minimap, undo, and
building only the nodes in view.

## How it is built

### `NodeGraph`

A canvas of linked nodes you can pan, zoom and move.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `edges` | `list` |  | The links: each {from: id, to: id}, the ids of the GraphNodes. |
| `snap` | `float` |  | A node the user moves lands on a multiple of this many pixels; 0 is no grid. |
| `arrows` | `bool` |  | Each edge ends in an arrowhead. |
| `fit` | `bool` |  | Pan and zoom, when it opens, so every node shows (never beyond actual size). |

### `GraphNode`

A node of a NodeGraph.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  |  |
| `x` | `float` |  |  |
| `y` | `float` |  |  |

## Using it

```yaml
name: pipeline
widget: Container
style: {width: 640, height: 360}
children:
  - widget: NodeGraph
    name: graph
    arrows: true
    fit: true
    snap: 20
    edges: [{from: root.graph.load, to: root.graph.clean}, {from: root.graph.clean, to: root.graph.save}]
    style: {width: 640, height: 360}
    children:
      - {widget: GraphNode, name: load, label: Load, x: 20, y: 40, style: {width: 140, height: 80}}
      - {widget: GraphNode, name: clean, label: Clean, x: 240, y: 100, style: {width: 140, height: 80}}
      - {widget: GraphNode, name: save, label: Save, x: 460, y: 40, style: {width: 140, height: 80}}
```

## Using it in Python

```python
from tesserae.widgets import graph_node, node_graph

graph = node_graph(app.window, 480, 320)
source = graph_node(app.window, graph, "Source", 40, 40, 120, 60)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
