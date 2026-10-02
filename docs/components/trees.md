# Trees

*Containment*

## In Material Design 3

Material Design 3 has no tree view; this is MD3's list row, indented by depth, with a chevron on the rows
that open.

## In Tesserae

Two fragments, a branch (with the chevron) and a leaf. `left_padding` is the indent for the row's depth.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: TreeNodeBranch` | A tree row that can be expanded: a title and a chevron, indented by its depth. | [`TreeNodeBranch_Stylesheet.yaml`](../stylesheets/trees/tree-node-branch.md) |
| `component: TreeNodeLeaf` | A tree row with nothing under it: a title, indented by its depth. | [`TreeNodeLeaf_Stylesheet.yaml`](../stylesheets/trees/tree-node-leaf.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `TreeNodeBranch`

A tree row that can be expanded: a title and a chevron, indented by its depth. Its look: [`TreeNodeBranch_Stylesheet.yaml`](../stylesheets/trees/tree-node-branch.md).

| Parameter | | Default |
| --- | --- | --- |
| `title` | required |  |
| `width` | required |  |
| `left_padding` | required |  |

```yaml
params: [title, width, left_padding]
id: root
kind: Container
children:
  - id: title
    kind: Text
    text:
      content: "{{ title }}"
      typography_role: label_large
  - id: chevron
    kind: Icon
    icon: {name: expand_more}
```

### `TreeNodeLeaf`

A tree row with nothing under it: a title, indented by its depth. Its look: [`TreeNodeLeaf_Stylesheet.yaml`](../stylesheets/trees/tree-node-leaf.md).

| Parameter | | Default |
| --- | --- | --- |
| `title` | required |  |
| `width` | required |  |
| `left_padding` | required |  |

```yaml
params: [title, width, left_padding]
id: root
kind: Container
children:
  - id: title
    kind: Text
    text:
      content: "{{ title }}"
      typography_role: label_large
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: folder
    component: TreeNodeBranch
    with: {title: src, width: 280, left_padding: 8}
  - id: file
    component: TreeNodeLeaf
    with: {title: app.py, width: 280, left_padding: 32}
```

In Python:

```python
from tesserae.widgets import tree_node

folder = tree_node(app.window, "src", depth=0, expanded=True)
file = tree_node(app.window, "app.py", depth=1, leaf=True)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# TreeNodeBranch_Stylesheet.yaml, next to your views
styles:
  - id: title
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
