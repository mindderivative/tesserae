# Trees

*Containment*

## In Material Design 3

Material Design 3 has no tree view; this is MD3's list row, indented by depth, with a chevron on the rows
that open.

## In Tesserae

Views Tesserae ships: `Tree` (the whole tree from data), `TreeNode` (one row, a branch with a chevron or a leaf) and `TreeLevel` (the rows of one level, which calls itself for
the children of an open branch).

| Property | Type | Meaning |
| --- | --- | --- |
| `nodes` | a list | rows: `{value, label}` and optionally `{icon, children, disabled}`; `children` is the same shape |
| `expanded` | a list; two-way | the values of the open branches |
| `selected` | a value; two-way | the chosen row |
| `compact` | true or false | 40 pixel rows instead of 56 |

A row is indented 16 pixels plus 24 for each level, has a 24 pixel chevron that turns a quarter when its branch opens (a leaf keeps the room), an optional icon and a `body_large`
label; the chosen row is `secondary_container`. A press chooses a row and opens or closes a branch. One Tab stop; the up and down arrows move through the rows that show, Right
opens a branch and Left closes it, and typing the start of a label jumps to a row. A screen reader hears a tree whose items have their level, and a branch says whether it is
expanded. `TreeNode` can be used alone for a custom tree. Not built: loading children when a branch first opens, selecting several, dragging to reorder, a context menu, and
building only the rows in view for a very large tree.

`widget: Tree` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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
      wrap: none
      overflow: ellipsis
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
      wrap: none
      overflow: ellipsis
```

## Using it

```yaml
name: files
widget: Container
style: {width: 360, height: 420}
children:
  - widget: Tree
    expanded: "{{ open }}"
    selected: "{{ current }}"
    nodes:
      - value: docs
        label: Documents
        icon: folder
        children:
          - {value: a, label: Letter}
          - {value: b, label: Reports, children: [{value: q, label: Q1}]}
      - {value: readme, label: Readme, icon: file}
```

## Using it

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
