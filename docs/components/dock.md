# Dock

*Windows and docking*

## In Material Design 3

Material Design 3 has no dock. A desktop tool often wants panels around its content that the user can move and
resize: files on the left, output below.

## In Tesserae

`widget: Dock` holds `DockPanel`s; each says its zone with the style field `zone`: `left`, `right`, `top`, `bottom` or `center`. A left or right zone's size is its panel's
`width`, and a top or bottom one's its `height` (240 and 180 pixels when the panel gives none). Each zone is a column: a strip of tabs, one for each panel, over the panel
that is showing. The tab is the panel's `title` (else its name). A click or Enter on a tab shows its panel, and the left and right arrow keys move along the strip. The user
drags a tab to another zone, or to a half of a split (see the dock panel), and drags the handles between zones to resize them. Dragging is pointer only, so a tab's context menu
(a right click, the Menu key or Shift+F10) offers "Move to ..." for each zone and each half. A window has one `Dock`, and `zone:` is an error on anything but a `DockPanel` in a `Dock`.

`view.dock_host(id)` reads and sets the layout from Python. A node's id is its path from the view's root, so the dock named `dock` is `view.dock_host("root.dock")`, and
its panel `files` is `"root.dock.files"`:

| Call | What it does |
| --- | --- |
| `set_size(zone, px)`, `size(zone)` | a zone's size, kept between 120 pixels and 70% of the room |
| `layout()` | where every panel is, which tab shows in each zone, the zone sizes, the sizes of the splits, and the halves (see the dock panel), as plain data |
| `restore(saved)` | puts a `layout()` back; titles, zones and halves the dock does not have are skipped |
| `move(panel, where)` | a panel (its id) to the tabs of a zone (`"left"`) or a half (its id), from code |
| `closed()`, `close(panel)`, `reopen(panel)`, `on_closed(fn)` | the closable panels that are shut |

Editing the YAML while the app runs keeps the layout the user made: which zone each panel is in, which tab shows, and the sizes.

A panel with `closable: true` has a close button on its tab. A Dock's `closed` (a list, two-way) holds the names of the closable panels that are shut: a close
button adds its panel's name, and taking a name out opens the panel again, as the last tab of its zone. Putting names in shuts them without the button. Not built: floating
panels, tearing a panel off into a window, maximising a panel, reordering tabs, and layouts saved by name.

## How it is built

### `Dock`

Panels docked around a centre.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `closed` | `list` |  | The names of the closable panels that are shut; a close button adds its panel, and taking a name out opens the panel again. Two-way. |

## Using it

```yaml
name: studio
widget: Window
title: Studio
style: {width: 900, height: 600, flex_direction: vertical}
children:
  - widget: Dock
    closed: "{{ shut }}"
    children:
      - {widget: DockPanel, name: files, title: Files, closable: true, style: {zone: left, width: 220}}
      - {widget: DockPanel, name: editor, title: Editor, style: {zone: center}}
```

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Docking](../guide/docking.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
