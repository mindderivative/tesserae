# Text

*Content*

## In Material Design 3

Text is set in Material Design 3's type scale: 15 styles in five groups (display, headline, title, body and
label), each large, medium or small, with a font, size, weight, line height and tracking.

## In Tesserae

`widget: Text`. Name a `typography_role` (or a `font_family`) and Tesserae fills in the rest; a theme's `typography:` can change
what a role means. A `Text` needs one of them and a `style.foreground`: without either the view does not build, and the error says which.

`text` can be an expression, and follows the Signals it reads. `font_family`, `font_size` and `font_weight` replace what the role gives. `wrap` is `word` or `none`,
`runs` gives pieces of one text their own style and links ([Rich Text & Links](../guide/rich-text.md)). `overflow` is `clip` or `ellipsis`, `text_align` is `start`, `center` or `end`, and `max_lines` cuts a longer text to that many lines (with `overflow: ellipsis` the last
one ends in an ellipsis). `letter_spacing` adds space between letters, in pixels. `selectable: true` lets the text be selected and copied, and `heading: 1` to `6` makes it a heading of that level for a screen reader.

The colour is `style.foreground` (required). Tracking: the roles are drawn with none, as the engine draws them; Material 3's per-role values are
`tokens.MD3_TRACKING`, and a theme turns them on with `typography: tokens.MD3_TRACKING_TYPOGRAPHY` (or one role at a time:
`typography: {body_large: {tracking: 0.5}}`). A node's own `letter_spacing` wins.

## How it is built

### `Text`

A run of text.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `text` | `str` |  | The text shown. |
| `typography_role` | `str` |  | A type role of the theme, such as body_large or title_large. |
| `font_family` | `str` |  |  |
| `font_size` | `float` |  |  |
| `font_weight` | `any` |  |  |
| `wrap` | `word` or `none` | `word` | 'word' breaks a long line; 'none' never does. |
| `overflow` | `clip` or `ellipsis` | `clip` |  |
| `text_align` | `start` or `center` or `end` | `start` |  |
| `max_lines` | `int` |  | The most lines shown, from 1; a longer text is cut (with `overflow: ellipsis`, an ellipsis ends the last line). |
| `letter_spacing` | `float` |  | Extra space between letters, in pixels (tracking). |
| `selectable` | `bool` |  | The text can be selected and copied. |
| `runs` | `list` |  | Pieces of one text in different styles, instead of `text`: each a string, or `{text, color, weight, italic, underline, strikethrough, font_size, font_family, link}`. A piece with a `link` is the theme's `primary` and underlined, and `on_link` runs with `event.href` when it is pressed. |
| `heading` | `1` or `2` or `3` or `4` or `5` or `6` |  | Makes it a heading of this level for a screen reader. |

Its `style:` also takes `foreground`.

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

## Using it in Python

```python
from tesserae.widgets import text

heading = text(app.window, "Notes", typography_role="headline_medium")
```

## See also

- [Index](../themes/index.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
