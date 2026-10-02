# Text

*Content*

## In Material Design 3

Text is set in Material Design 3's type scale: 15 styles in five groups (display, headline, title, body and
label), each large, medium or small, with a font, size, weight and line height.

## In Tesserae

The `Text` kind. Name a `typography_role` and Tesserae fills in the rest; a theme's `typography:` can change
what a role means.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Text` | Text in one of MD3's type styles and a colour. | [`Text_Stylesheet.yaml`](../stylesheets/text/text.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Text`

Text in one of MD3's type styles and a colour. Its look: [`Text_Stylesheet.yaml`](../stylesheets/text/text.md).

| Parameter | | Default |
| --- | --- | --- |
| `text` | required |  |
| `typography_role` | optional | `body_medium` |
| `color` | optional | `on_surface` |

```yaml
params:
  - text
  - {typography_role: body_medium}
  - {color: on_surface}
id: root
kind: Text
text:
  content: "{{ text }}"
  typography_role: "{{ typography_role }}"
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: heading
    component: Text
    with: {text: Notes, typography_role: headline_medium, color: on_surface}
```

In Python:

```python
from tesserae.widgets import text

heading = text(app.window, "Notes", typography_role="headline_medium")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Text_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Index](../themes/index.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
