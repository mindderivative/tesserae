# Tutorial: A Tasks App

Getting Started builds a counter. This tutorial builds a small **Tasks** app in six steps, each a
working program that adds one idea to the last, to show you the options you have: inline styling and
separate files, built-in components and your own, one view or several, an ordinary window or your
own frame. Every step is a folder in
[`examples/tutorial/`](https://github.com/mindderivative/tesserae/tree/main/examples/tutorial) that
Tesserae's tests run; the page shows the files a step adds or changes.

The files here sit side by side and are named by their paths. [The same app as a project](tutorial-project.md)
puts them in the folders `tesserae new` makes and finds them by name.

You need a working install ([Getting Started](getting-started.md)). Make a folder for the app, and for
each step put its files in it (or run a step straight from a checkout: `python examples/tutorial/step3/app.py`).

## 1. A screen

One screen: a title, a count, and a button. A **view** is the YAML; its **ViewModel** is the Python
that holds the state. They are paired by name, `Tasks_View.yaml` and `Tasks_ViewModel.py`.

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step1/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step1/Tasks_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial/step1/app.py"
```

- **Inline styling.** Each node has its own `style:`, with colours named for theme roles
  (`surface`, `on_surface`), not hex codes, so they follow light and dark.
- **A built-in component.** `component: ButtonFilled` puts MD3's filled button in place; `with:` fills its
  parameters. [Every component](components/index.md) has a page.
- **State.** `tasks` is a `Signal`; `summary` is a `Computed` that follows it. The view's
  `bindings:` keeps the text showing it, and `handlers:` calls `add_task` on a click.
- **The app.** `app.load` pairs the two files by name; `theme_seed` makes the colours.

```bash
python app.py
```

## 2. A list of components

A task is more than a line of text: it has a checkbox and a remove button, and state of its own. That
makes it a **component**: another view and ViewModel pair, embedded once for each task. A `Repeater`
keeps one alive for each entry of a list `Signal`, adding and removing them as the list changes.

```yaml title="TaskItem_View.yaml"
--8<-- "examples/tutorial/step2/TaskItem_View.yaml"
```

```python title="TaskItem_ViewModel.py"
--8<-- "examples/tutorial/step2/TaskItem_ViewModel.py"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step2/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step2/Tasks_ViewModel.py"
```

- `tasks` holds the ids and is the single source of truth. The `Repeater` makes a
  `TaskItem` for each id, and `args` hands its ViewModel the id and the list.
- A row removes itself by changing the list; nobody tears the row down by hand.
- `two_way: checked` writes the checkbox back to the row's `done` `Signal`.

See [Components & Embedding](guide/components.md) and [Repeater](guide/repeater.md).

## 3. Styling in files

Inline `style:` is fine for one node. Three kinds of file take styling out of the views:

```yaml title="Brand_Theme.yaml"
--8<-- "examples/tutorial/step3/Brand_Theme.yaml"
```

```yaml title="Tasks_Stylesheet.yaml"
--8<-- "examples/tutorial/step3/Tasks_Stylesheet.yaml"
```

```yaml title="row_Style.yaml"
--8<-- "examples/tutorial/step3/row_Style.yaml"
```

```yaml title="ButtonFilled_Stylesheet.yaml"
--8<-- "examples/tutorial/step3/ButtonFilled_Stylesheet.yaml"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step3/Tasks_View.yaml"
```

```yaml title="TaskItem_View.yaml"
--8<-- "examples/tutorial/step3/TaskItem_View.yaml"
```

```python title="app.py"
--8<-- "examples/tutorial/step3/app.py"
```

- **A theme** (`Brand_Theme.yaml`) is app-wide: one `seed` colour makes the whole palette, and
  `typography:` changes a type style. Pass it as `App(custom_theme=)`.
- **A stylesheet** (`Tasks_Stylesheet.yaml`) is rules. A node says `classes: [page]` and a rule
  `classes: [page]` styles it; rules can also match a `kind` or an `id`. Pass it as `App(stylesheet=)`.
- **A style file** (`row_Style.yaml`) is one node's `style:`, shared: `style: row_Style.yaml`.
- **A component's own stylesheet.** Built-in components keep their look in a
  [stylesheet](stylesheets/index.md). A `ButtonFilled_Stylesheet.yaml` next to the views goes over it,
  field by field: here, a tertiary button.

The checkbox keeps its inline `style:`: mix as you like. A node's own `style:` always wins, then the
stylesheet, then the theme. See [Themes](themes/index.md).

## 4. A component of your own

Two numbers in the same shape: that is a component. A `*_Component.yaml` is a **fragment**: structure
with `{{ parameters }}`, and its look in a stylesheet of the same name.

```yaml title="Stat_Component.yaml"
--8<-- "examples/tutorial/step4/Stat_Component.yaml"
```

```yaml title="Stat_Stylesheet.yaml"
--8<-- "examples/tutorial/step4/Stat_Stylesheet.yaml"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step4/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step4/Tasks_ViewModel.py"
```

```yaml title="Tasks_Stylesheet.yaml"
--8<-- "examples/tutorial/step4/Tasks_Stylesheet.yaml"
```

- `component: Stat` finds `Stat_Component.yaml` next to the view. Its parameters are `label` and `value`.
- `value` is a binding expression, so each stat keeps up with its `Computed`. (A binding to text needs a
  string, so the `Computed`s return strings.)
- A fragment has no ViewModel and no state of its own, which is what separates it from the components of
  step 2. Use a fragment for a repeated *look*, a view and ViewModel pair for repeated *behaviour*.

See [Component Fragments](guide/component-fragments.md).

## 5. A second screen

A **screen** is a view and ViewModel pair registered with the app. Settings is a second one, and the two
share state: the app owns it, and any ViewModel reads it as `self.state`.

```yaml title="Settings_View.yaml"
--8<-- "examples/tutorial/step5/Settings_View.yaml"
```

```python title="Settings_ViewModel.py"
--8<-- "examples/tutorial/step5/Settings_ViewModel.py"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step5/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step5/Tasks_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial/step5/app.py"
```

- `state=AppState()` gives every screen the same `user` `Signal`. Change the name in Settings and the
  heading on the Tasks screen follows.
- `app.navigate("Settings")` is a step the user can go back from, and `app.back()` goes back. The Back
  button's `disabled` is bound to `app.can_go_back`, so it greys out when there is nowhere to go.
- `app.route(...)` names screens by strings, so `python app.py settings` opens on Settings.
- `app.set_dark(...)` switches every screen between light and dark, in place.

See [Apps & Screens](guide/apps-and-screens.md).

## 6. A custom window

With `decorations=False` the OS draws no title bar, and the app draws its own frame. An **app shell**
is that frame: a top bar (which becomes the title bar and gets the window's buttons), a navigation
rail that switches screens, and a status bar. It is one more file.

```yaml title="Tasks_Shell.yaml"
--8<-- "examples/tutorial/step6/Tasks_Shell.yaml"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step6/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step6/Tasks_ViewModel.py"
```

```yaml title="Settings_View.yaml"
--8<-- "examples/tutorial/step6/Settings_View.yaml"
```

```python title="Settings_ViewModel.py"
--8<-- "examples/tutorial/step6/Settings_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial/step6/app.py"
```

- Every part of a shell takes a `style:`, so the top bar's height and colour are yours to set.
- The rail replaces the Settings and Back buttons, so they are gone from the screens.
- The window is still resizable (from its edges), and the top bar still drags it.

See [App Shell & Docking](guide/app-shell.md) and [Custom Title Bars](guide/custom-title-bars.md).

## Where next

- Run with `app.run(hot_reload=True)` and edit any view, stylesheet or theme while the app is open:
  the window updates and keeps its state. See [Hot Reload](guide/hot-reload.md).
- `tesserae build --check` turns the app into one executable: [Releasing Your App](guide/releasing.md).
- Browse the [components](components/index.md), and the [YAML](api/yaml.md) and
  [Python](api/python.md) references.
