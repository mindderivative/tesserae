# Text fields

*Selection and input*

## In Material Design 3

A text field lets people enter and edit text. Material Design 3 has two kinds: a **filled** field, a tinted
container with a line under it, and an **outlined** one, a field with a border. The label, supporting text and
icons are part of the field; what is typed is `on_surface`, and the caret is `primary`.

## In Tesserae

The `TextField` node kind: a box (the field's container) holding the engine's text input. The box takes the
`style:`, so `background` is the container's colour and `corner_radius` and `border_color` shape it, and the typed
text is the theme's `on_surface`, which follows light and dark, unless `style.foreground` says another. The
caret is the theme's `primary`. `text:` gives the starting `content` and the type (`typography_role`,
`font_family`, `font_size`), and the field is one line that scrolls: it has no `text_align`, `wrap`, `overflow`,
`runs` or `selectable`. A `TextField` needs a `background` and a size.

Bind `text` and add `two_way: text` to write what is typed back to the ViewModel, and `on_change` to hear each
change. Give it an `a11y: {label: ...}`, since the field has no label of its own.

This component is the `TextField` node kind, not a fragment: use `kind: TextField` in a view (the [YAML reference](../api/yaml.md#the-kinds)).

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: name
    kind: TextField
    text: {content: "", typography_role: body_large}
    style: {width: 240, height: 48, background: surface_container_highest, corner_radius: 8,
            padding: {left: 12, right: 12, top: 0, bottom: 0}}
    bindings: {text: "{{ name.get() }}"}
    two_way: text
    a11y: {label: Your name}
```

## See also

- [Bindings](../guide/bindings.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
