# Dock panel

*Windows and docking*

## In Material Design 3

Material Design 3 has no dock panel. It is one panel of a dock: a titled tab in a zone.

## In Tesserae

The `DockPanel` kind, with `zone` in its `style`. A `DockPanel` inside another is a split of it, side by side
(`flex_direction: horizontal`) or top and bottom (`vertical`), with a handle to resize.

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
      - id: editor
        kind: DockPanel
        title: Editor
        style: {zone: center}
        children:
          - id: source
            kind: DockPanel
            title: Source
            children: []
          - id: preview
            kind: DockPanel
            title: Preview
            children: []
```

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
