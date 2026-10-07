# Tutorial: The Same App as a Project

The [Tutorial](tutorial.md) builds a Tasks app in one flat folder, naming every file by its path. This tutorial
builds **the same app as a project**: the folder `tesserae new` makes, with a place for each kind of file, where
Tesserae finds a file by its name. Read it beside the first one, or instead of it: the app, its screens and its
behaviour are the same, and what changes is where the files are and how little code it takes to join them.

Every step is a project folder in
[`examples/tutorial_project/`](https://github.com/mindderivative/tesserae/tree/main/examples/tutorial_project)
that Tesserae's tests run. The page shows every file a step adds or changes, so each step can be followed on its own; the
[flat Tutorial](tutorial.md) explains the views and ViewModels in more depth.

## Flat or a project?

| | A flat folder | A project |
| --- | --- | --- |
| Made by | you, file by file | `tesserae new tasks` |
| Layout | every file side by side | `Views/`, `ViewModels/`, `Components/`, `Themes/`, `Styles/` |
| Load a screen | `app.load(HERE / "Tasks_View.yaml", TasksViewModel)` and an `import` | `app.load("Main")` |
| Rows of a list | `Repeater(view, items, HERE / "TaskItem_View.yaml", TaskItemViewModel, into=...)` | `Repeater(view, items, "TaskItem", into=...)` |
| A theme or stylesheet | `App(custom_theme=HERE / "Brand_Theme.yaml")` | `App(custom_theme="Brand")` |
| A component of your own | next to the view that uses it | `Components/`, from any view |
| A new screen | write a view, a ViewModel, the import and the route | `tesserae add screen Settings` |
| Good for | one screen, a sketch, a single file to share | an app with several screens and its own look |

Neither is a mode: a project is a flat folder with the files sorted, and paths still work in a project. Start flat
and sort the files into folders when there are too many to find; or start with `tesserae new` and never write a
path.

## 1. A new project

```bash
tesserae new tasks
cd tasks
source .venv/bin/activate     # Windows: .venv\Scripts\activate
python app.py
```

`tesserae new` makes the folders, a `Main` screen that counts clicks, and a virtual environment with Tesserae in
it (`--no-venv` skips the environment). Replace the screen with the Tasks app's:

```text
tasks/
  app.py
  Views/Main_View.yaml
  ViewModels/Main_ViewModel.py
  Components/  Themes/  Styles/       empty for now
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step1/Views/Main_View.yaml"
```

```python title="ViewModels/Main_ViewModel.py"
--8<-- "examples/tutorial_project/step1/ViewModels/Main_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial_project/step1/app.py"
```

- **Paired by name.** `app.load("Main")` opens `Views/Main_View.yaml` and the class `MainViewModel` in
  `ViewModels/Main_ViewModel.py`. There is no import and no path: the flat `app.py` needed both.
- **`root=HERE`** says where the project is, so it runs from any folder: `python tasks/app.py`.
- The view and ViewModel are the flat Tutorial's, renamed `Tasks` to `Main`.

## 2. A list of components

A task row is a view and ViewModel pair of its own, in the same two folders:

```yaml title="Views/TaskItem_View.yaml"
--8<-- "examples/tutorial_project/step2/Views/TaskItem_View.yaml"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step2/Views/Main_View.yaml"
```

```python title="ViewModels/TaskItem_ViewModel.py"
--8<-- "examples/tutorial_project/step2/ViewModels/TaskItem_ViewModel.py"
```

```python title="ViewModels/Main_ViewModel.py"
--8<-- "examples/tutorial_project/step2/ViewModels/Main_ViewModel.py"
```

- `Repeater(view, self.tasks, "TaskItem", into=...)` finds `Views/TaskItem_View.yaml` and `TaskItemViewModel` by
  the name. The flat version spells out the path and imports the class.
- The folders keep views and Python apart, so a screen's ViewModel never imports another file's path.

## 3. Styling in files

Themes, stylesheets and style files each have a folder, and an app or a view names them:

```yaml title="Themes/Brand_Theme.yaml"
--8<-- "examples/tutorial_project/step3/Themes/Brand_Theme.yaml"
```

```yaml title="Styles/Tasks_Stylesheet.yaml"
--8<-- "examples/tutorial_project/step3/Styles/Tasks_Stylesheet.yaml"
```

```yaml title="Styles/row_Style.yaml"
--8<-- "examples/tutorial_project/step3/Styles/row_Style.yaml"
```

```yaml title="Components/ButtonFilled_Stylesheet.yaml"
--8<-- "examples/tutorial_project/step3/Components/ButtonFilled_Stylesheet.yaml"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step3/Views/Main_View.yaml"
```

```yaml title="Views/TaskItem_View.yaml"
--8<-- "examples/tutorial_project/step3/Views/TaskItem_View.yaml"
```

```python title="app.py"
--8<-- "examples/tutorial_project/step3/app.py"
```

- `custom_theme="Brand"` is `Themes/Brand_Theme.yaml`, and `stylesheet="Tasks"` is `Styles/Tasks_Stylesheet.yaml`.
- `style: row_Style.yaml` in a view is found in `Styles/` (a style file next to the view is still found first).
- A built-in component's stylesheet goes over its own when it is in `Components/`: the tertiary button.

## 4. A component of your own

A fragment goes in `Components/`, and any view says `component: Stat`, wherever the view is:

```yaml title="Components/Stat_Component.yaml"
--8<-- "examples/tutorial_project/step4/Components/Stat_Component.yaml"
```

```yaml title="Components/Stat_Stylesheet.yaml"
--8<-- "examples/tutorial_project/step4/Components/Stat_Stylesheet.yaml"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step4/Views/Main_View.yaml"
```

```yaml title="Styles/Tasks_Stylesheet.yaml"
--8<-- "examples/tutorial_project/step4/Styles/Tasks_Stylesheet.yaml"
```

```python title="ViewModels/Main_ViewModel.py"
--8<-- "examples/tutorial_project/step4/ViewModels/Main_ViewModel.py"
```

- `Components/Stat_Component.yaml` is the structure and `Components/Stat_Stylesheet.yaml` its look, as in the flat
  Tutorial, but one folder holds every component, so reusing one in another screen needs no path.

## 5. A second screen

```bash
tesserae add screen Settings
```

writes `Views/Settings_View.yaml` and `ViewModels/Settings_ViewModel.py`, and adds `app.load("Settings")` and its
route to `app.py`. Fill them in, and share state through the app:

```yaml title="Views/Settings_View.yaml"
--8<-- "examples/tutorial_project/step5/Views/Settings_View.yaml"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step5/Views/Main_View.yaml"
```

```python title="ViewModels/Settings_ViewModel.py"
--8<-- "examples/tutorial_project/step5/ViewModels/Settings_ViewModel.py"
```

```python title="ViewModels/Main_ViewModel.py"
--8<-- "examples/tutorial_project/step5/ViewModels/Main_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial_project/step5/app.py"
```

- Nothing is imported: `app.load("Settings")` pairs the two files, and the route `settings` opens it
  (`python app.py settings`).
- `state=AppState()` is shared as it is in the flat Tutorial: the app owns it and a ViewModel reads `self.state`.

## 6. A custom window

The app's frame is one more view, a `kind: Window` file in `Views/`, loaded by name. It holds the title bar, a rail, a status
bar, and the two screens as `view:` nodes with a `route:`:

```yaml title="Views/Window_View.yaml"
--8<-- "examples/tutorial_project/step6/Views/Window_View.yaml"
```

```yaml title="Views/Settings_View.yaml"
--8<-- "examples/tutorial_project/step6/Views/Settings_View.yaml"
```

```python title="ViewModels/Settings_ViewModel.py"
--8<-- "examples/tutorial_project/step6/ViewModels/Settings_ViewModel.py"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step6/Views/Main_View.yaml"
```

```python title="app.py"
--8<-- "examples/tutorial_project/step6/app.py"
```

```python title="ViewModels/Main_ViewModel.py"
--8<-- "examples/tutorial_project/step6/ViewModels/Main_ViewModel.py"
```

- The rail replaces the Settings button, so `Main_ViewModel.py` loses `open_settings`.
- `app.load("Window")` opens `Views/Window_View.yaml`. Its `view: Main_View.yaml` and `view: Settings_View.yaml` nodes, with a
  `route:`, are the screens: each is registered under its file's name (`Main`, `Settings`) and finds its ViewModel in
  `ViewModels/`, so `app.py` no longer loads or routes them.
- The window's `borderless: true` and `title_bar:` replace `decorations=False`; the rail is a `NavigationRailScreens` whose
  `screen:` names the screens.

## Where next

- [Projects](guide/projects.md): the rest of finding files by name, more folders to search (`search=`), looking
  through the whole project (`recursive=True`), and what a name in two places does.
- [The `tesserae` command](guide/cli.md): `new`, `add screen`, `build`.
- [Tutorial](tutorial.md): the same app with every file named by its path, and its YAML for each step.
