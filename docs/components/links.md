# Links

*Navigation*

## In Material Design 3

A link takes the user somewhere else, or opens a related page. It is text, in the primary colour.

## In Tesserae

`widget: Link` is text that takes focus, and that Enter or a click activates. It is `primary`, in `body_medium` unless you name another type role.

| Property | Type | Meaning |
| --- | --- | --- |
| `text` | text | what it says; it also names the link for a screen reader |
| `href` | a link | opened in the OS's browser or mail program when it is activated: `http`, `https`, `mailto` and `tel` only, anything else is refused |
| `visited` | true or false, two-way | whether it has been followed; opening its `href` sets a bound one, and `state: visited` in a rule colours it (`secondary` by default) |
| `disabled` | true or false | dimmed, out of the Tab order, and does nothing |
| `underline` | `hover`, `always` or `never` | underlined while the pointer is over it or keyboard focus is on it (the default), always, or never |
| `handlers` | | `on_click` runs as well as the `href` opens |

The type properties of `Text` (`typography_role`, `wrap`, `overflow`, `max_lines`, ...) apply. Inside a longer text, use `text.runs` with a `link`.

`widget: Link` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Link` | Text that opens something when it is clicked. | [`Link_Stylesheet.yaml`](../stylesheets/links/link.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Link`

Text that opens something when it is clicked. Its look: [`Link_Stylesheet.yaml`](../stylesheets/links/link.md).

| Parameter | | Default |
| --- | --- | --- |
| `text` | required |  |
| `width` | required |  |
| `height` | required |  |
| `wrap` | optional | `none` |
| `overflow` | optional | `ellipsis` |

```yaml
params:
  - text
  - width
  - height
  - {wrap: none}
  - {overflow: ellipsis}
id: root
kind: Link
text:
  content: "{{ text }}"
  typography_role: body_large
  wrap: "{{ wrap }}"
  overflow: "{{ overflow }}"
```

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

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: help
    component: Link
    with: {text: Read the docs, width: 160, height: 24}
    handlers: {on_click: open_docs}
```

In Python:

```python
from tesserae.widgets import link

help_link = link(app.window, "Read the docs", 160, on_click=viewmodel.open_docs)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Link_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
