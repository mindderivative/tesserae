# Dock

*Windows and docking*

## In Material Design 3

Material Design 3 has no dock. A desktop tool often wants panels around its content that the user can move and
resize: files on the left, output below.

## In Tesserae

The `Dock` kind holds `DockPanel`s; each says its zone with the style field `zone`. Panels in one zone are tabs, and
the user drags a tab to another zone or the handles between zones. `view.dock_host(id)` reads and sets the zone
sizes and saves and restores the layout: `dock = view.dock_host("dock")`, then `dock.set_size("left", 280)`,
`saved = dock.layout()` and `dock.restore(saved)`.

A panel with `closable: true` has a close button on its tab. A Dock's `closed` (a list, two-way) holds the names of the closable panels that are shut: a close
button adds its panel's name, and taking a name out opens the panel again, as the last tab of its zone. Putting names in shuts them without the button. `dock.closed()`,
`dock.close(id)` and `dock.reopen(id)` do the same from Python. Not built: floating panels, tearing a panel off into a window, maximising a panel, reordering tabs,
and layouts saved by name.

This component has no `component:` fragment: build it in Python.

## Using it

```yaml
name: studio
widget: Window
style: {width: 900, height: 600, flex_direction: vertical}
children:
  - widget: Dock
    closed: "{{ shut }}"
    children:
      - {widget: DockPanel, name: files, title: Files, closable: true, style: {zone: left, width: 220}}
      - {widget: DockPanel, name: editor, title: Editor, style: {zone: center}}
```

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: dock
    kind: Dock
    style: {flex: fill}
    children:
      - {id: files, kind: DockPanel, title: Files, style: {zone: left, width: 220}, children: []}
      - {id: editor, kind: DockPanel, title: Editor, style: {zone: center}, children: []}
```

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Docking](../guide/docking.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
