# Tutorial: A Tasks App

Getting Started builds a counter. This tutorial builds a small **Tasks** app in six steps, each a
working program that adds one idea to the last, to show you the options you have: inline styling and
separate files, built-in widgets and your own, one view or several, an ordinary window or your
own frame. Every step is a folder in
[`examples/tutorial/`](https://github.com/mindderivative/tesserae/tree/main/examples/tutorial) that
Tesserae's tests run; the page shows the files a step adds or changes.

The files here sit side by side. [The same app as a project](tutorial-project.md)
puts them in the folders `tesserae new` makes and finds them by name.

You need a working install ([Getting Started](getting-started.md)). Make a folder for the app, and for
each step put its files in it (or run a step straight from a checkout: `python examples/tutorial/step3/app.py`).

## 1. A screen

One screen: a title, a count, and a button. A **view** is the YAML; its **ViewModel** is the Python
that holds the state. The view says which ViewModel serves it with its `name:`, and the ViewModel says which views it
serves with `views`.

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step1/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step1/Tasks_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial/step1/app.py"
```

- **Every node is a `widget:`.** `Container` lays things out, `Text` shows text, and `Button` is MD3's button;
  its keys are that widget's properties (`label`, `variant`), a `style:`, and a `name:` to find the node by.
  [Every widget and component](components/index.md) has a page.
- **Inline styling.** Each node has its own `style:`, with colours named for theme roles
  (`surface`, `on_surface`), not hex codes, so they follow light and dark.
- **State.** `tasks` is a `Signal`; `summary` is a `Computed` that follows it. A Signal reads as its value in
  a view, so `text: "{{ summary }}"` stays up to date, and `handlers:` calls `add_task` on a click.
- **The app.** `app.bind` joins the ViewModel to the views it serves, `app.open_view` opens the view and
  `app.show` puts it in the window. `theme_seed` makes the colours, and `search=["."]` says the app's other views are
  found in this folder, which the next step uses.

```bash
python app.py
```

## 2. A list of views

A task is more than a line of text: it has a checkbox and a remove button. That makes it a view of its own,
`TaskItem`, called once for each task. A view with `params:` is called by its name, with the params as keys, and
`for:` with a `key:` repeats the call for each element of a list, adding and removing rows as the list changes.

```yaml title="TaskItem_View.yaml"
--8<-- "examples/tutorial/step2/TaskItem_View.yaml"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step2/Tasks_View.yaml"
```

```python title="Tasks_ViewModel.py"
--8<-- "examples/tutorial/step2/Tasks_ViewModel.py"
```

- `tasks` holds one dictionary for each task, and is the single source of truth. Each change replaces the
  list, which is how a view notices it. The `key:` is the task's `id`, so a row that stays is kept as it is.
- A view cannot read the names of the view that calls it, so what it needs comes in as a param:
  `task` is the data. `on_toggle` and `on_remove` are `handler` params: the caller writes what to do (`remove(task.id)`
  is written in the caller's names) and the row runs it by name.
- A row removes itself by changing the list; nobody tears the row down by hand.
- A `Checkbox` shows `checked` and runs `on_change` when the user changes it. Its `checked` here is a plain
  expression, so it is one-way, and the ViewModel makes the change.

See [Components & Embedding](guide/components.md) and [Component Views](guide/component-fragments.md).

## 3. Styling in files

Inline `style:` is fine for one node. Two kinds of file take styling out of the views:

```yaml title="Brand_Theme.yaml"
--8<-- "examples/tutorial/step3/Brand_Theme.yaml"
```

```yaml title="Tasks_Stylesheet.yaml"
--8<-- "examples/tutorial/step3/Tasks_Stylesheet.yaml"
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
- **A stylesheet** (`Tasks_Stylesheet.yaml`) is rules. A rule names a `widget` and may narrow it by `classes`,
  a property (`variant`), a `part` (a named node inside that widget) and a `state`, and gives a `style`. A node
  that says `classes: [page]` is styled by the rule with `classes: [page]`. Pass the file as `App(stylesheet=)`.
- **A rule for a view of your own.** `widget: TaskItem` styles the root of every `TaskItem`, so the row's
  layout is no longer written in its file.
- **A rule for a widget Tesserae ships.** The two `Button` rules go over the shipped look of a filled button,
  field by field: here, a tertiary one. `part: label` is the button's text.

A node's own `style:` always wins, then the stylesheet, then the theme. See [Themes](themes/index.md).

## 4. A view of your own

Two numbers in the same shape: that is a view with params. `Stat` is a file like any other, and there is no
other kind of component.

```yaml title="Stat_View.yaml"
--8<-- "examples/tutorial/step4/Stat_View.yaml"
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

- `widget: Stat` finds `Stat_View.yaml` by its name. Its params are `label` and `value`.
- `value` is an expression written where the view is called, so each stat keeps up with its `Computed`. (A text
  property takes a string, so the `Computed`s return strings.)
- Its look is rules for `widget: Stat` in the app's stylesheet: one for the view's root and one for each named part
  (`part: value`).
- A view has no state of its own unless it says `state:`, and no ViewModel of its own: it reads its params, then the
  names of the ViewModel that serves the view at the top. `TaskItem` and `Stat` are the same kind of thing, a
  repeated *look* or a repeated *piece*; the behaviour stays in the one ViewModel.

## 5. A second screen

A **screen** is a view that is opened and registered with the app. Settings is a second one, and the two
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

- `state=state` gives every screen the same `user` `Signal`. A view reads it as `app.state.user`, so the heading on the
  Tasks screen follows the name typed in Settings.
- The Settings field edits the Signal, and a bare reference to a Signal is what makes a property two-way, so
  `SettingsViewModel` is made with the state and holds the Signal as `name`. `app.bind(SettingsViewModel(state))` binds the
  instance you made; `app.bind(TasksViewModel)` has Tesserae make its one instance.
- `app.navigate("Settings")` is a step the user can go back from, and `app.back()` goes back. The Back
  button's `disabled` is bound to `app.can_go_back`, so it greys out when there is nowhere to go.
- `app.route(...)` names screens by strings, so `python app.py settings` opens on Settings.
- `app.set_dark(...)` switches every screen between light and dark, in place.

See [Apps & Screens](guide/apps-and-screens.md).

## 6. A custom window

With `borderless: true` the OS draws no title bar, and the app draws its own frame. The **window view** is that frame:
a `widget: Window` file with a title bar (which gets the window's buttons), a navigation rail that switches screens, a status
bar, and the screens themselves, each a call of a view with a `route:`. The app opens the one file, and the window's file now
brings the two screens in.

```yaml title="Window_View.yaml"
--8<-- "examples/tutorial/step6/Window_View.yaml"
```

```yaml title="Tasks_View.yaml"
--8<-- "examples/tutorial/step6/Tasks_View.yaml"
```

```yaml title="Settings_View.yaml"
--8<-- "examples/tutorial/step6/Settings_View.yaml"
```

```python title="Window_ViewModel.py"
--8<-- "examples/tutorial/step6/Window_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial/step6/app.py"
```

- `style:` on the `Window` is the window's size and colour, and the title bar takes a `style:` too, so its colour is yours to set.
- A call with a `route:` is a screen: `widget: Tasks` is the view `Tasks_View.yaml`, and the app can `navigate("Tasks")`, `show("Tasks")`
  or `navigate_to("")` it. A routed screen is part of the window view, not opened by itself, so it has no `name:` and no ViewModel
  of its own: it reads the names of the ViewModel that serves the window. That is why `Tasks_ViewModel.py` and
  `Settings_ViewModel.py` are now one, `Window_ViewModel.py`, serving `Window`.
- The rail replaces the Settings and Back buttons, so they are gone from the screens.
- The window is still resizable (from its edges), and the title bar still drags it.

See [Windows, Docks & Embedded Views](guide/windows-and-docks.md) and [Custom Title Bars](guide/custom-title-bars.md).

## Where next

- Edit a theme file while the app runs with `app.run(hot_reload=True)` and the colours change at once: see
  [Hot Reload](guide/hot-reload.md) for what it watches.
- `tesserae build --check` turns the app into one executable: [Releasing Your App](guide/releasing.md).
- Browse the [components](components/index.md), and the [YAML](api/yaml.md) and
  [Python](api/python.md) references.
