# Top app bar

*Navigation*

## In Material Design 3

A top app bar sits along the top of a screen with its title and the actions for it: a navigation icon at the
start and up to a few action icons at the end.

## In Tesserae

`widget: TopAppBar` is a view Tesserae ships (`TopAppBar_View.yaml`): a bar as wide as its place, built from `IconButton`s and a title.

The `variant` is `small` (64 tall, the title beside the icon, the default), `center` (64, the title in the middle), `medium` (112) or `large` (152), the last two with the title under
the icons. `leading_icon` is the navigation icon (`menu` or `arrow_back`), `leading_label` its name and tooltip, and `on_leading` what it does. `actions` are up to three icons at the
end, each `{value, icon, label}`; pressing one sets `chosen` to its `value`. `collapsed` makes a medium or large bar show as a small one (the height eases), and `scrolled` says content
is under the bar: its colour goes from `surface` to `surface_container`. `frosted: true` makes the surface translucent and blurred.

Bind `collapsed` and `scrolled` to how a list under the bar has scrolled (the `at_top` of a `ScrollView`). Every icon is a button with a label, which is its name and its
tooltip. With `App(borderless=True)` a bar can sit in a window's title area; the title bar of a window is `TitleBar`. Not built: the contextual action mode (a selection bar
that replaces it), and a search bar inside it (`SearchBar` is its own view).

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: TopAppBar`. A file of the same name in your project replaces it.

### `TopAppBar`

The Material 3 top app bar: a navigation icon, a title and up to three action icons across the top of a screen. `variant`: `small` (64 tall, the title beside the icon), `center` (64, the title in the middle), `medium` (112, the title under the row of icons) and `large` (152, a bigger title under them). The medium and large collapse to the small form while `collapsed` is true (bind it to the way a list under it has scrolled), and `scrolled` (true once content is under the bar) turns its colour from `surface` to `surface_container`. `leading_icon` is the navigation icon (`menu` or `arrow_back`) and its `on_leading` handler; `actions` is a list of {value, icon, label}, pressing one sets `chosen` to its `value`. Every icon has a label (its name and its tooltip). Role: a group.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `frosted` | `bool` | `false` | A translucent surface that blurs what is behind it (72% of its colour, a 20 pixel backdrop blur). |
| `title` | `str` |  | The title. |
| `variant` | `small` or `center` or `medium` or `large` | `small` | How tall it is and where the title sits. |
| `leading_icon` | `str` |  | The navigation icon (menu, arrow_back). |
| `leading_label` | `str` | `Navigation` | The navigation icon's name and tooltip. |
| `on_leading` | `handler` |  | What the navigation icon does. |
| `actions` | `list` | `[]` | Up to three icons at the end, each {value, icon, label}. |
| `chosen` | `any` |  | The value of the action last pressed. Two-way: give it a bare reference and the view writes it back. |
| `collapsed` | `bool` | `false` | A medium or large bar shows as a small one. |
| `scrolled` | `bool` | `false` | Content is under the bar: its colour changes. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `row` (Container), `leading` (IconButton), `lead_space` (Container), `lead_filler` (Container), `title` (Text), `filler` (Container), `action` (IconButton), `big_title` (Text).

Its look is in [`TopAppBar_Stylesheet.yaml`](../stylesheets/top-app-bar/top-app-bar.md).

## Using it

```yaml
name: inbox
widget: Container
style: {flex_direction: vertical, width: 480, height: 400}
children:
  - widget: TopAppBar
    title: Inbox
    variant: large
    leading_icon: menu
    on_leading: open_drawer
    collapsed: "{{ not at_top }}"
    scrolled: "{{ not at_top }}"
    chosen: "{{ command }}"
    actions: [{value: search, icon: magnify, label: Search}, {value: more, icon: dots_vertical, label: More}]
  - {widget: ScrollView, at_top: "{{ at_top }}", style: {flex: fill}}
```

## Using it in Python

```python
from tesserae.widgets import top_app_bar

bar = top_app_bar(app.window, "Notes", leading_icon="menu", trailing_icons=["settings"])
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# TopAppBar_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: TopAppBar
    part: title
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Custom Title Bars](../guide/custom-title-bars.md)
- [Windows And Docks](../guide/windows-and-docks.md)
- [Effects](../guide/effects.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
