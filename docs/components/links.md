# Links

*Navigation*

## In Material Design 3

A link takes the user somewhere else, or opens a related page. It is text, in the primary colour.

## In Tesserae

`widget: Link` is text that takes focus, and that Enter or a click activates. It is `primary`, in `body_medium` unless you name another type role.

The `text` also names the link for a screen reader. Its `href` is opened in the OS's browser or mail program when the link is activated: `http`, `https`, `mailto` and `tel` only,
anything else is refused. Opening it sets a bound `visited`, and `state: visited` in a rule colours it (`secondary` by default). A disabled link is dimmed, out of the Tab order,
and does nothing. It is underlined while the pointer is over it or keyboard focus is on it (`underline: hover`, the default), always, or never. `handlers: {on_click: ...}` runs
as well as the `href` opens; a link with no `href` just runs its handler.

The type properties of `Text` (`typography_role`, `wrap`, `overflow`, `max_lines`, ...) apply. A link inside a longer text is a `link` run of a `Text` (`runs`, [Rich Text & Links](../guide/rich-text.md)); a `Link` is for a whole line.

## How it is built

### `Link`

Text that can be activated.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `text` | `str` |  | The link's text, which names it for a screen reader. |
| `typography_role` | `str` |  | A type role of the theme, such as body_large or title_large. |
| `font_family` | `str` |  |  |
| `font_size` | `float` |  |  |
| `font_weight` | `any` |  |  |
| `wrap` | `word` or `none` | `word` | 'word' breaks a long line; 'none' never does. |
| `overflow` | `clip` or `ellipsis` | `clip` |  |
| `text_align` | `start` or `center` or `end` | `start` |  |
| `max_lines` | `int` |  | The most lines shown, from 1; a longer text is cut (with `overflow: ellipsis`, an ellipsis ends the last line). |
| `letter_spacing` | `float` |  | Extra space between letters, in pixels (tracking). |
| `href` | `str` |  | A web or mail link (http, https, mailto, tel) opened in the OS's browser or mail program when it is activated. |
| `visited` | `bool` |  | Whether it has been followed; opening its href sets it, and a rule can show it with `state: visited`. Two-way. |
| `disabled` | `bool` |  | Dimmed, and not activated. |
| `underline` | `hover` or `always` or `never` | `hover` | When the text is underlined: while the pointer is over it or it has the keyboard focus, always, or never. |

Its `style:` also takes `foreground`.

## Using it

```yaml
name: help
widget: Container
style: {flex_direction: vertical, gap: 8, width: 300, height: 100}
children:
  - {widget: Link, text: Read the docs, href: "https://example.com/docs", visited: "{{ docs_seen }}"}
  - {widget: Link, text: Not now, disabled: true}
  - {widget: Link, text: Sign in, handlers: {on_click: sign_in}}
```

## Using it in Python

```python
from tesserae.widgets import link

help_link = link(app.window, "Read the docs", 160, on_click=viewmodel.open_docs)
```

## See also

- [Rich Text](../guide/rich-text.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
