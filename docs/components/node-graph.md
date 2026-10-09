# Node graph

*Beyond MD3*

## In Material Design 3

Material Design 3 has no node graph. This is a pannable canvas of titled boxes joined by edges, for tools.

## In Tesserae

The `NodeGraph` kind (`widget: NodeGraph` in a view), with `GraphNode` children at an `x` and a `y`. Drag the background to pan, the wheel zooms about the pointer, drag a node (or
press the arrow keys on a focused one) to move it, and its edges follow.

| Property | Type | Meaning |
| --- | --- | --- |
| `edges` | a list | the links, each `{from: id, to: id}`, the ids of the `GraphNode`s |
| `snap` | pixels | a node the user moves lands on a multiple of this; a key then steps one square; `0` is no grid |
| `arrows` | true or false | each edge ends in an arrowhead |
| `fit` | true or false | when it opens, pan and zoom so every node shows (never past actual size) |

Pressing a node chooses it (a `primary` border, and it is selected to a screen reader); pressing the background chooses none. From Python the widget has `fit_to_view(padding)`,
`zoom`, `offset`, `snap`, `arrows` and `selected` (a `Signal` of the node chosen). Not built: ports and dragging to connect, labels on edges, selecting several, a minimap, undo, and
building only the nodes in view.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: NodeGraph` | A pannable canvas for a node graph: its GraphNodes and the edges between them. | [`NodeGraph_Stylesheet.yaml`](../stylesheets/node-graph/node-graph.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `NodeGraph`

A pannable canvas for a node graph: its GraphNodes and the edges between them. Its look: [`NodeGraph_Stylesheet.yaml`](../stylesheets/node-graph/node-graph.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |

```yaml
params: [width, height]
id: root
kind: Rect
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: graph
    component: NodeGraph
    with: {width: 480, height: 320}
```

In Python:

```python
from tesserae.widgets import graph_node, node_graph

graph = node_graph(app.window, 480, 320)
source = graph_node(app.window, graph, "Source", 40, 40, 120, 60)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# NodeGraph_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
