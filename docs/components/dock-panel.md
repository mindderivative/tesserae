# Dock panel

*Windows and docking*

## In Material Design 3

Material Design 3 has no dock panel. It is one panel of a dock: a titled tab in a zone.

## In Tesserae

`widget: DockPanel`, with `zone` in its `style` and a `title` for its tab (else its name). `closable: true` puts a close button on its tab (see the Dock's `closed`).

A `DockPanel` inside another is a split of it, side by side (`flex_direction: horizontal`, the default) or top and bottom (`vertical`), with a handle between the halves
to resize them. A half with a `width` (or `height`) of its own keeps it, and the others share what is left. A panel has either splits or content, not both, and a half has no
`zone`. Each half is a small zone of its own: a tab strip over it, with a tab for the half's own content (titled by its `title:`, else its name) and one for each panel dropped
on it.

Drag a tab over a half and the highlight shows what a drop will do. The outer quarter of each side of a half is an **edge**: dropping there splits the half, the panel
taking a new half on that side with a handle between the two. The rest, the tab strip included, is the **middle**: dropping there adds the panel to the half as another tab,
and the half shows it. A tab in a half is dragged like any other, to a zone, to another half or to the edge of one. A half that a drop made collapses when its last panel
leaves, and its neighbour takes the room back. You cannot drop a panel on the halves inside it. In the tab menu (right click, the Menu key or Shift+F10) "Move to ..."
lists the halves too.

From Python, with `dock = view.dock_host("root.dock")`. The half and the panel are named by their ids, their paths from the view's root (`root.dock.editor.source`):

| Call | What it does |
| --- | --- |
| `dock.halves()` | each half's panels (their ids) and the one it shows (`None`: the half's own content) |
| `dock.show_in_half(half, panel)` | shows a panel in a half; `panel` of `None` shows the half's own content |
| `dock.half_of(panel)` | the id of the half a panel is in, or `None` if it is in a zone |
| `dock.move(panel, where)` | a panel into a half or a zone (`"left"`) |

`dock.layout()` records the halves, so the arrangement the user made survives a restart: `halves` has, for each half, the titles of the panels in it and the tab it shows,
and `made` has, for each half of the YAML that the user split, the tree of the splits (an `axis` of `x` or `y`, the first part's `size` in pixels, and its `first` and
`second` parts), as plain data you can write to a file. `dock.restore(saved)` takes the user's splits apart, makes the ones in the layout and puts the panels in their
halves; halves and titles the dock does not have are skipped, and a split none of whose panels come back is not made. A half is found by its id, so renaming one in the
file means a saved layout no longer finds it. Editing the YAML while the app runs keeps the strips, the panels dropped on a half and the splits the user made; a half the
file removes sends the panels dropped in it back to their zones. Not built: dragging or closing a half's own content (what the YAML put in it), and reordering tabs.

## How it is built

### `DockPanel`

One panel of a Dock.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `title` | `str` |  | The panel's tab, when its zone has several. |
| `closable` | `bool` |  | Its tab has a close button. |

## Using it

```yaml
name: studio
widget: Window
title: Studio
style: {width: 900, height: 600, flex_direction: vertical}
children:
  - widget: Dock
    children:
      - {widget: DockPanel, name: outline, title: Outline, style: {zone: left, width: 220}}
      - widget: DockPanel
        name: editor
        title: Editor
        style: {zone: center}
        children:
          - {widget: DockPanel, name: source, title: Source, style: {width: 400}}
          - {widget: DockPanel, name: preview, title: Preview}
```

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
