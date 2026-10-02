# Node graph

*Beyond MD3*

## In Material Design 3

Material Design 3 has no node graph. This is a pannable canvas of titled boxes joined by edges, for tools.

## In Tesserae

The `NodeGraph` kind, with `GraphNode` children.

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
