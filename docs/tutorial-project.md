# Tutorial: The Same App as a Project

The [Tutorial](tutorial.md) builds a Tasks app in one flat folder, naming every file by its path. This tutorial
builds **the same app as a project**: a folder with a place for each kind of file, where
Tesserae finds a file by its name. Read it beside the first one, or instead of it: the app, its screens and its
behaviour are the same, and what changes is where the files are and how little code it takes to join them.

Every step is a project folder in
[`examples/tutorial_project/`](https://github.com/mindderivative/tesserae/tree/main/examples/tutorial_project)
that Tesserae's tests run. The page shows every file a step adds or changes, so each step can be followed on its own; the
[flat Tutorial](tutorial.md) explains the views and ViewModels in more depth.

## Flat or a project?

| | A flat folder | A project |
| --- | --- | --- |
| Made by | you, file by file | `tesserae new tasks`, then your own files |
| Layout | every file side by side | `Views/`, `ViewModels/`, `Themes/`, `Styles/` (and `Components/`, for views in the older syntax) |
| Open a screen | `app.open_view("Tasks")`, with `search=["."]` so views are found in the folder | `app.open_view("Main")` |
| A ViewModel | an `import`, then `app.bind(TasksViewModel)` | `app.bind(app.project.viewmodel("Main"))`: no import |
| A theme or stylesheet | `App(custom_theme=HERE / "Brand_Theme.yaml")` | `App(custom_theme="Brand")` |
| A view of your own | next to the view that uses it | `Views/`, from any view |
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
it (`--no-venv` skips the environment). Its files are in the current view language already; replace the screen and
`app.py` with the Tasks app's:

```text
tasks/
  app.py
  Views/Main_View.yaml
  ViewModels/Main_ViewModel.py
  Components/  Themes/  Styles/       empty for now; Components/ is not used here, a view of your own goes in Views/
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

- **Paired by name.** The view is named `Main` and its ViewModel serves `"Main"`. `app.open_view("Main")` opens
  `Views/Main_View.yaml`, and `app.project.viewmodel("Main")` is the class `MainViewModel` in
  `ViewModels/Main_ViewModel.py`. There is no import and no path: the flat `app.py` needed both.
- **`root=HERE`** says where the project is, so it runs from any folder: `python tasks/app.py`.
- The view and ViewModel are the flat Tutorial's, renamed `Tasks` to `Main`.

## 2. A list of views

A task row is a view of its own, in the same folder as the screen:

```yaml title="Views/TaskItem_View.yaml"
--8<-- "examples/tutorial_project/step2/Views/TaskItem_View.yaml"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step2/Views/Main_View.yaml"
```

```python title="ViewModels/Main_ViewModel.py"
--8<-- "examples/tutorial_project/step2/ViewModels/Main_ViewModel.py"
```

- `widget: TaskItem` finds `Views/TaskItem_View.yaml` by its name, wherever the view that calls it is. The flat version
  needs `search=["."]` to say where its views are.
- The row has no ViewModel: it takes the task and two handlers as params, and `Main`'s ViewModel does the work.

## 3. Styling in files

Themes and stylesheets each have a folder, and the app names them:

```yaml title="Themes/Brand_Theme.yaml"
--8<-- "examples/tutorial_project/step3/Themes/Brand_Theme.yaml"
```

```yaml title="Styles/Tasks_Stylesheet.yaml"
--8<-- "examples/tutorial_project/step3/Styles/Tasks_Stylesheet.yaml"
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
- The stylesheet holds rules for your own views (`widget: TaskItem`) and for ones Tesserae ships (`widget: Button`,
  here a tertiary button), over the shipped look.

## 4. A view of your own

Any view says `widget: Stat`, wherever it is, because every view in `Views/` is found by its name:

```yaml title="Views/Stat_View.yaml"
--8<-- "examples/tutorial_project/step4/Views/Stat_View.yaml"
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

- `Views/Stat_View.yaml` is the structure, and its look is the `widget: Stat` rules in the stylesheet, as in the flat
  Tutorial. One folder holds every view, so reusing one in another screen needs no path.

## 5. A second screen

Add `Views/Settings_View.yaml` and `ViewModels/Settings_ViewModel.py` (`tesserae add screen Settings` writes a starting
pair; [The `tesserae` command](guide/cli.md) says what it makes), then fill them in and share state through the app:

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

- Nothing is imported: `app.project.viewmodel("Settings")` finds the class, and the route `settings` opens the
  screen (`python app.py settings`).
- `state=state` is shared as it is in the flat Tutorial: the app owns it, a view reads `app.state.user` and a ViewModel reads
  `self.state`. `SettingsViewModel` is made with it, so its field can edit the Signal.

## 6. A custom window

The app's frame is one more view, a `widget: Window` file in `Views/`, opened by name. It holds the title bar, a rail, a status
bar, and the two screens as calls with a `route:`:

```yaml title="Views/Window_View.yaml"
--8<-- "examples/tutorial_project/step6/Views/Window_View.yaml"
```

```yaml title="Views/Settings_View.yaml"
--8<-- "examples/tutorial_project/step6/Views/Settings_View.yaml"
```

```yaml title="Views/Main_View.yaml"
--8<-- "examples/tutorial_project/step6/Views/Main_View.yaml"
```

```python title="ViewModels/Window_ViewModel.py"
--8<-- "examples/tutorial_project/step6/ViewModels/Window_ViewModel.py"
```

```python title="app.py"
--8<-- "examples/tutorial_project/step6/app.py"
```

- The rail replaces the Settings button, so the screens lose their Back and Settings buttons.
- `app.open_view("Window")` opens `Views/Window_View.yaml`. Its `widget: Main` and `widget: Settings` calls, with a
  `route:`, are the screens: each is registered under its view's name (`Main`, `Settings`), so `app.py` no longer opens
  or routes them.
- A routed screen has no ViewModel of its own: it reads the names of the one that serves the window, so
  `Main_ViewModel.py` and `Settings_ViewModel.py` are now one, `Window_ViewModel.py`: delete the two old files, which nothing uses any more.
- The window's `borderless: true` and `title_bar:` make the window's own title bar; the rail is a `NavigationRailScreens` whose
  `screen:` names the screens.

## Where next

- [Projects](guide/projects.md): the rest of finding files by name, more folders to search (`search=`), looking
  through the whole project (`recursive=True`), and what a name in two places does.
- [The `tesserae` command](guide/cli.md): `new`, `add screen`, `build`.
- [Tutorial](tutorial.md): the same app with every file named by its path, and its YAML for each step.
