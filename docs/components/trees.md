# Trees

*Containment*

## In Material Design 3

Material Design 3 has no tree view; this is MD3's list row, indented by depth, with a chevron on the rows
that open.

## In Tesserae

Views Tesserae ships: `Tree` (the whole tree from data), `TreeNode` (one row, a branch with a chevron or a leaf) and `TreeLevel` (the rows of one level, which calls itself for
the children of an open branch).

The `nodes` are rows, `{value, label}` and optionally `{icon, children, disabled}`, where `children` is a list of the same shape. `expanded` (the values of the open branches)
and `selected` (the value of the chosen row) are two-way. Rows are 56 pixels tall, or 40 with `compact`.

A row is indented 16 pixels plus 24 for each level, has a 24 pixel chevron that turns a quarter when its branch opens (a leaf keeps the room), an optional icon and a `body_large`
label; the chosen row is `secondary_container`. A press chooses a row and opens or closes a branch. One Tab stop; the up and down arrows move through the rows that show, Right
opens a branch and Left closes it, and typing the start of a label jumps to a row. A screen reader hears a tree whose items have their level, and a branch says whether it is
expanded. `TreeNode` can be used alone for a custom tree. Not built: loading children when a branch first opens, selecting several, dragging to reorder, a context menu, and
building only the rows in view for a very large tree.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Tree`. A file of the same name in your project replaces it.

### `Tree`

A tree (the WAI-ARIA tree pattern in Material 3's list terms): rows that open to show their children, one level inside the next. `nodes` is a list of {value, label} and optionally {icon, children, disabled}, the children being the same shape. `expanded` is the list of values of the open branches and `selected` the value of the chosen row; both are two-way. A press on a row chooses it, and on a branch opens or closes it too. One Tab stop; the up and down arrows move through the rows that show, Right opens a branch and Left closes one, and typing the start of a label jumps to a row.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `nodes` | `list` | `[]` | The rows: {value, label} and optionally {icon, children, disabled}; children are the same shape. |
| `expanded` | `list` | `[]` | The values of the branches that are open. Two-way: give it a bare reference and the view writes it back. |
| `selected` | `any` |  | The value of the chosen row. Two-way: give it a bare reference and the view writes it back. |
| `compact` | `bool` | `false` | 40 pixel rows instead of 56. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `top` (TreeLevel).

### `TreeNode`

One row of a tree: a leaf or a branch with a chevron that turns a quarter when it opens. 56 pixels tall (40 when `compact`), indented 16 pixels plus 24 for each `level`, with an optional 24 pixel icon and a `body_large` label; a selected row is `secondary_container`. A screen reader hears a tree item at level `level + 1`, a branch saying whether it is expanded. It is pressable; `handlers: {on_click: ...}` on the call is what a press does. `Tree` puts the rows together.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The row's text. |
| `icon` | `str` |  | A leading icon. |
| `level` | `int` | `0` | How deep it is: 0 for the top. |
| `branch` | `bool` | `false` | It has children: a chevron shows. |
| `expanded` | `bool` | `false` | For a branch: whether its children show. |
| `selected` | `bool` | `false` | Whether this is the chosen row. |
| `compact` | `bool` | `false` | A 40 pixel row instead of 56. |
| `disabled` | `bool` | `false` | Dimmed and not pressable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `chevron` (Icon), `chevron_space` (Container), `icon` (Icon), `label` (Text).

Its look is in [`TreeNode_Stylesheet.yaml`](../stylesheets/trees/tree-node.md).

### `TreeLevel`

The rows of one level of a tree, each followed by its children's level while it is open (this view calls itself). `Tree` is the one to use; this is its part.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `nodes` | `list` | `[]` | The rows: {value, label} and optionally {icon, children, disabled}. |
| `level` | `int` | `0` | How deep this level is. |
| `expanded` | `list` | `[]` | The values of the branches that are open. Two-way: give it a bare reference and the view writes it back. |
| `selected` | `any` |  | The value of the chosen row. Two-way: give it a bare reference and the view writes it back. |
| `compact` | `bool` | `false` | 40 pixel rows. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `entry` (Container), `row` (TreeNode), `children` (TreeLevel).

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

## Using it in Python

```python
from tesserae.widgets import tree_node

folder = tree_node(app.window, "src", depth=0, expanded=True)
file = tree_node(app.window, "app.py", depth=1, leaf=True)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# TreeNode_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: TreeNode
    part: chevron
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
