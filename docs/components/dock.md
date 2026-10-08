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

This component has no `component:` fragment: build it in Python.

## Using it

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
