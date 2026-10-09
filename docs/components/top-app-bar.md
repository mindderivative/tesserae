# Top app bar

*Navigation*

## In Material Design 3

A top app bar sits along the top of a screen with its title and the actions for it: a navigation icon at the
start and up to a few action icons at the end.

## In Tesserae

`widget: TopAppBar` is a view Tesserae ships (`TopAppBar_View.yaml`): a bar as wide as its place, built from `IconButton`s and a title.

| Property | Type | Meaning |
| --- | --- | --- |
| `title` | text | the title |
| `variant` | `small`, `center`, `medium`, `large` | 64 tall with the title beside the icon; 64 with the title in the middle; 112 or 152 with the title under the icons |
| `leading_icon`, `leading_label`, `on_leading` | an icon, text, a handler | the navigation icon (`menu`, `arrow_back`), its name and tooltip, and what it does |
| `actions` | a list | up to three icons at the end, each `{value, icon, label}`; pressing one sets `chosen` to its `value` |
| `chosen` | a value; two-way | the action last pressed |
| `collapsed` | true or false | a medium or large bar shows as a small one (the height eases) |
| `scrolled` | true or false | content is under the bar: its colour goes from `surface` to `surface_container` |

Bind `collapsed` and `scrolled` to how a list under the bar has scrolled (the `at_top` of a `ScrollView`). Every icon is a button with a label, which is its name and its
tooltip. With `App(borderless=True)` a bar can sit in a window's title area; the title bar of a window is `TitleBar`. Not built: the contextual action mode (a selection bar
that replaces it), and a search bar inside it (`SearchBar` is its own view).

`widget: TopAppBar` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: TopAppBar` | A top app bar: the window's title and actions, along the top. | [`TopAppBar_Stylesheet.yaml`](../stylesheets/top-app-bar/top-app-bar.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `TopAppBar`

A top app bar: the window's title and actions, along the top. Its look: [`TopAppBar_Stylesheet.yaml`](../stylesheets/top-app-bar/top-app-bar.md).

| Parameter | | Default |
| --- | --- | --- |
| `title` | required |  |
| `width` | required |  |

```yaml
params: [title, width]
id: root
kind: Container
children:
  - id: title
    kind: Text
    text:
      content: "{{ title }}"
      typography_role: title_large
      wrap: none
      overflow: ellipsis
```

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

## Using it

In Python:

```python
from tesserae.widgets import top_app_bar

bar = top_app_bar(app.window, "Notes", leading_icon="menu", trailing_icons=["settings"])
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# TopAppBar_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Custom Title Bars](../guide/custom-title-bars.md)
- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
