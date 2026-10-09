# Split buttons

*Actions*

## In Material Design 3

A split button joins a main action to a menu of related ones: the leading part does the usual thing, and the
trailing chevron opens the others.

## In Tesserae

`widget: SplitButton` is a view Tesserae ships (`SplitButton_View.yaml`): two `Button`s 2 pixels apart and a `Menu` for the trailing one. One widget covers all five types.

| Property | Type | Meaning |
| --- | --- | --- |
| `label`, `icon` | text, an icon | the main part's text and leading icon |
| `variant`, `size` | as on `Button` | `filled`, `tonal`, `elevated`, `outlined`, `text`; `xs` to `xl`; both parts take them |
| `items` | a list | the menu's rows, as `Menu` takes them |
| `chosen` | a value; two-way | the value of the menu row pressed |
| `on_click` | a handler | what the main part does |
| `disabled` | true or false | both parts are dimmed and do not respond |

The inner corners are small (4 pixels) and the outer ones round; while the menu is open the trailing part is round on every corner and its chevron is turned over. Each part is its
own Tab stop; the trailing part says it is expanded while its menu shows. Arrow-down on either part opens the menu and moves the focus to its first row (a press opens it
without moving the focus). Not built: a toggle form.

`widget: SplitButton` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: SplitButtonFilled` | A filled split button: an action, and a menu of related ones. | [`SplitButtonFilled_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-filled.md) |
| `component: SplitButtonFilledTonal` | A filled tonal split button: an action, and a menu of related ones. | [`SplitButtonFilledTonal_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-filled-tonal.md) |
| `component: SplitButtonElevated` | An elevated split button: an action, and a menu of related ones. | [`SplitButtonElevated_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-elevated.md) |
| `component: SplitButtonOutlined` | An outlined split button: an action, and a menu of related ones. | [`SplitButtonOutlined_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-outlined.md) |
| `component: SplitButtonText` | A text split button: an action, and a menu of related ones. | [`SplitButtonText_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-text.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `SplitButtonFilled`, `SplitButtonFilledTonal`, `SplitButtonElevated`, `SplitButtonOutlined`, `SplitButtonText`

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |
| `height` | required |  |
| `corner_radius` | required |  |

These 5 have one structure; only their stylesheets, above, differ.

```yaml
params: [label, width, height, corner_radius]
id: root
kind: Container
children:
  - id: leading
    kind: Rect
    children:
      - id: label
        kind: Text
        text:
          content: "{{ label }}"
          typography_role: label_large
          text_align: center
  - id: trailing
    kind: Rect
    children:
      - id: chevron
        kind: Icon
        icon: {name: expand_more}
```

## Using it

```yaml
name: compose
widget: Container
style: {width: 420, height: 240, padding: 16}
children:
  - widget: SplitButton
    label: Send
    icon: send
    on_click: send_now
    chosen: "{{ when }}"
    items:
      - {value: later, label: Send later}
      - {value: draft, label: Save as draft}
```

## Using it

In Python:

```python
from tesserae.widgets import split_button

send = split_button(app.window, "Send", 160, 40, variant="filled")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# SplitButtonFilled_Stylesheet.yaml, next to your views
styles:
  - id: leading
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
