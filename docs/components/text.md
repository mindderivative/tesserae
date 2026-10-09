# Text

*Content*

## In Material Design 3

Text is set in Material Design 3's type scale: 15 styles in five groups (display, headline, title, body and
label), each large, medium or small, with a font, size, weight, line height and tracking.

## In Tesserae

`widget: Text`. Name a `typography_role` and Tesserae fills in the rest; a theme's `typography:` can change
what a role means.

| Property | Type | Meaning |
| --- | --- | --- |
| `text` | text | what is shown; an expression follows the Signals it reads |
| `typography_role` | a role such as `body_large` | the font, size, weight and line height |
| `font_family`, `font_size`, `font_weight` | | replace what the role gives |
| `wrap`, `overflow`, `text_align` | | `word` or `none`; `clip` or `ellipsis`; `start`, `center`, `end` |
| `max_lines` | whole number | the most lines shown; with `overflow: ellipsis` the last one ends in an ellipsis |
| `letter_spacing` | number | extra space between letters, in pixels |
| `selectable` | true or false | the text can be selected and copied |
| `heading` | 1 to 6 | makes it a heading of that level for a screen reader |

The colour is `style.foreground`. Tracking: the roles are drawn with none, as the engine draws them; Material 3's per-role values are
`tokens.MD3_TRACKING`, and a theme turns them on with `typography: tokens.MD3_TRACKING_TYPOGRAPHY` (or one role at a time:
`typography: {body_large: {tracking: 0.5}}`). A node's own `letter_spacing` wins.

`widget: Text` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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
| `wrap` | optional | `word` |
| `overflow` | optional | `clip` |

```yaml
params:
  - text
  - {typography_role: body_medium}
  - {color: on_surface}
  - {wrap: word}
  - {overflow: clip}
id: root
kind: Text
text:
  content: "{{ text }}"
  typography_role: "{{ typography_role }}"
  wrap: "{{ wrap }}"
  overflow: "{{ overflow }}"
```

## Using it

```yaml
name: article
widget: Container
style: {flex_direction: vertical, gap: 8, width: 360, height: 200}
children:
  - {widget: Text, text: Notes, typography_role: headline_medium, heading: 1, style: {foreground: on_surface}}
  - widget: Text
    text: "{{ summary }}"
    typography_role: body_large
    max_lines: 3
    overflow: ellipsis
    selectable: true
    style: {foreground: on_surface_variant}
```

## Using the fragment

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
