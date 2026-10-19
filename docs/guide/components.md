# Components & Embedding

A screen is built from views, and there are three ways for views to meet:

| You want | Use |
| --- | --- |
| A reusable piece inside a view: a button, a card, a row | [call it](#a-view-inside-a-view): `widget: Name`, with params and children |
| A list of such pieces that follows the data | [`for:`](#a-list-of-views) on the call |
| Several screens, or windows, that share data | [one ViewModel for several views](#one-viewmodel-several-views) |

Writing a component is covered in [Component Views](component-fragments.md); this page is about putting views together and what each part
can see.

## A view inside a view

A view found by name is built where it is written:

```yaml
name: notes
widget: Container
style: {flex_direction: horizontal, width: 480, height: 200, gap: 16}
children:
  - {widget: Card, name: summary, headline: Summary, text: Three notes today, style: {width: 160}}
  - {widget: Button, name: add, label: Add note, handlers: {on_click: add_note}}
```

- `Card` and `Button` are views Tesserae ships. A view of your own is called the same way: `Sidebar` is `Views/Sidebar_View.yaml` (or a file in
  a folder the app searches: [Projects](projects.md)). There is no file path and no separate kind of embedded view: any view can be called, and a view with `params:`
  takes them as keys (`- {widget: Counter, name: counter, start: 5}`).
- Its nodes have ids under the call (`root.counter.label`), so a view can be called as often as you like.
- `style:` on the call places the view in its parent, as on any node.
- It takes the host's theme and stylesheet, and follows them as they change.
- A called view has **no ViewModel of its own**. Its expressions read, in this order: its own loop variables and local `state:`, its
  params, then the names of the ViewModel that serves the view at the top, then `app`. It cannot see the names of the view that calls it
  except through params. A name it needs from the caller is a param:

```yaml
# Counter_View.yaml
params:
  start: {type: int, default: 0}
state: {count: "{{ start }}"}
widget: Container
style: {flex_direction: horizontal, gap: 8, align_content: center}
children:
  - {widget: Text, name: label, text: "{{ count }}", typography_role: title_medium, style: {foreground: on_surface}}
  - {widget: Button, name: add, label: Add, handlers: {on_click: "count += 1"}}
```

A called view with a `name:` that some ViewModel serves is **not** bound to that ViewModel by being called: the binding is for a view
you open (see below).

### A list of views

Build the pieces from the data with `for:`. This is how a to-do list of rows that each remove themselves is written, with no
bookkeeping of added and removed rows:

```yaml
# TodoItem_View.yaml
params:
  label: {type: str, required: true}
  on_remove: {type: handler}
widget: Container
style: {flex_direction: horizontal, width: 260, height: 40, gap: 8, align_content: center}
children:
  - {widget: Text, name: label, text: "{{ label }}", typography_role: body_large, style: {foreground: on_surface, flex: fill}}
  - {widget: IconButton, name: remove, icon: close, label: Remove, handlers: {on_click: on_remove}}
```

```yaml
# in Main_View.yaml, under children:
- widget: TodoItem
  for: item in items
  key: item.id
  name: item
  label: "{{ item.title }}"
  on_remove: "items = [i for i in items if i.id != item.id]"
```

```python
class MainViewModel(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.items = Signal([{"id": 1, "title": "Write the docs"}, {"id": 2, "title": "Ship it"}])
```

The `key:` is what makes the list reactive: when `items` is replaced, rows whose key stays are kept (with their local state), new keys are
built, removed keys are gone, and the order follows the list. For a very long list, use a `VirtualList`
([The View Language](view-language.md#long-lists)).

## One ViewModel, several views

A ViewModel serves **named** views. A view is named by its root `name:`, and the ViewModel lists the names it serves:

```python
from tesserae import App, Signal, ViewModel


class DataViewModel(ViewModel):
    views = ["data_pie", "data_list"]          # the views it serves (a string means one)

    def __init__(self):
        super().__init__()
        self.rows = Signal([("a", 3), ("b", 5)])


app = App(root=".")
app.bind(DataViewModel)
app.open_view("DataPie")                       # Views/DataPie_View.yaml, named data_pie
app.open_view("DataList")
app.show("data_pie")                           # the window shows one screen at a time
```

- **One instance serves every view that names it**, so a pie chart and a list of the same rows are two views of one Signal.
  `app.bind(DataViewModel)` makes it once, when the first view opens; `app.bind(instance)` uses an instance you made;
  `app.bind(factory=DataViewModel)` makes one for each view that opens (and `views=[...]` names the views when the factory is a function).
- `app.open_view(name)` builds the view and registers it as a screen under its `name:`. `app.show(name)` puts it in the window. The
  window shows one screen at a time; the views of a [window view](windows-and-docks.md) are screens inside it, and
  [`app.open_window`](windows-and-docks.md#several-windows) shows a view in a window of its own, so two windows can show two views of
  one ViewModel.
- A ViewModel takes no constructor arguments here (it is made for you); `bind(instance)` or a `factory=` function is how it gets some.
- A view with no `name:` is not bound to any ViewModel. Use it for something static, and call it from a view that is.
- The ViewModel finds its open views in `self.views[name]`: `.node(name)` (a node of the view, by its `name:`), `.state(var)` (a local
  `state:` name), `.show()` and `.hide()`. `self.show("data_phone", "data_list")` shows one view and hides the other. A name that is
  declared but not open is a `KeyError` that says so.
- `on_attached(handle)` and `on_detached(handle)` are called as a ViewModel's views open and close.

`app.check()` compares every name, action and `expects:` entry of the open views with their ViewModels without a window, and lists
what does not match, so a test can assert that it is empty:

```python
assert app.check() == []
```

`expects:` is optional data in a view's header, `expects: {count: int, rows: list, add: handler}`, for a view that is checked before any
ViewModel exists.

## Routed views

A call with a `route:` inside the [window view](windows-and-docks.md#routed-views) is a screen of the app, not just a part of the layout:
the screen's name is the view it calls, it is shown while its route is current, and the others are hidden with their state kept.
`navigate.Settings`, `navigate.back` and `navigate_to('Note', {'id': 3})` are the handlers that move between them.
[Windows, Docks & Embedded Views](windows-and-docks.md#routed-views) has the rest.

## Views in the older syntax

A view written with `kind:` and `id:` (the syntax before `widget:`) is loaded by the compatibility loader, and has its own API for being
placed under a node from Python:

```python
from tesserae import instantiate

component, viewmodel = instantiate(view, "Card", into=container)   # Views/Card_View.yaml and CardViewModel, found by name
component.remove()
```

`instantiate(parent, path, viewmodel_cls, into, *args, **kwargs)` and [`Repeater`](repeater.md), which keeps one such instance for each
item of a list Signal, take a view in the **older syntax** only: handed a file written with `widget:`, `instantiate` refuses it
(`every widget needs an id`). The ViewModel of such a view is the older `ViewModel(view)`. A project moves over with
`tesserae migrate-yaml` ([Migrating](../migration.md)), after which `for:` and a call replace `Repeater` and `instantiate`.
