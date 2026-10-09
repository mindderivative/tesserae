# Switch

*Selection and input*

## In Material Design 3

A switch toggles one setting on or off, and takes effect at once. It has a track and a thumb that grows when
it is on.

## In Tesserae

`widget: Switch`, a Tesserae control: a 52 by 32 pixel track and a handle that slides across it and grows when pressed.

| Property | Type | Meaning |
| --- | --- | --- |
| `selected` | true or false, two-way | whether it is on |
| `label` | text | beside the track, part of what you press, and what a screen reader calls it |
| `icons` | true or false | a check on the handle when on and a cross when off (the off handle is then as big as the on one) |
| `disabled` | true or false | dimmed and does nothing |

`widget: Switch` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Switch` | A switch: a setting that is on or off, and takes effect at once. | [`Switch_Stylesheet.yaml`](../stylesheets/switches/switch.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Switch`

A switch: a setting that is on or off, and takes effect at once. Its look: [`Switch_Stylesheet.yaml`](../stylesheets/switches/switch.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |
| `selected` | required |  |

```yaml
params: [width, height, selected]
id: root
kind: Switch
selected: "{{ selected }}"
```

## Using it

```yaml
name: settings
widget: Container
style: {flex_direction: vertical, gap: 8, width: 240, height: 140, padding: 16}
children:
  - {widget: Switch, selected: "{{ wifi }}", label: Wi-Fi}
  - {widget: Switch, selected: "{{ dark }}", label: Dark mode, icons: true}
```

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: dark
    component: Switch
    with: {width: 52, height: 32, selected: false}
```

In Python:

```python
from tesserae.widgets import switch

dark = switch(app.window, selected=False)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Switch_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
