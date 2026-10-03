# The `tesserae` Command

Installing Tesserae installs a `tesserae` command (`python -m tesserae` is the same).
It starts apps and screens from templates, builds an app into one executable, and finds
the editor schemas.

## Start an app

```bash
tesserae new notes
cd notes
source .venv/bin/activate     # Windows: .venv\Scripts\activate
python app.py
```

`notes/` is a [project](projects.md): a virtual environment with Tesserae installed in it, the folders `Views/`,
`ViewModels/`, `Components/`, `Themes/` and `Styles/`, `app.py`, and a `Main` screen, `Views/Main_View.yaml` and
`ViewModels/Main_ViewModel.py`, that follow the [naming convention](naming-convention.md): a greeting from the app's
[shared state](apps-and-screens.md#shared-state) and a button that counts its clicks.
`app.py` gives Main the route `""`, so `python app.py <route>` opens on a screen by its
route (a [deep link](apps-and-screens.md#routes-and-deep-links)).

| Option | What it does |
| --- | --- |
| `--no-venv` | Makes the folders and files without the virtual environment, which needs the network to install Tesserae. |
| `--shell` | Adds an [app shell](app-shell.md) file, `Views/Notes_Shell.yaml` (a top bar, a navigation rail over Main and Settings, a status bar), and a Settings screen. |
| `--custom-title-bar` | With `--shell`: no OS title bar. The shell's top bar is the [title bar](custom-title-bars.md): it moves the window and has the minimize, maximize and close buttons. The window is at least 640 by 400. |
| `--dir PARENT` | Makes the app in `PARENT` instead of here. |

Nothing is overwritten: a folder that isn't empty is refused with a one-line message (exit code 2).

## Add a screen

```bash
tesserae add screen Settings
```

This writes `Views/Settings_View.yaml` and `ViewModels/Settings_ViewModel.py` (a title and a Back button that
calls `self.app.back()`) and adds `app.load("Settings")` and its route (`settings`) to
`app.py`, above the marker comment `tesserae new` left there. Without the marker it
prints the lines to add. A CamelCase name gets a kebab-case route: `UserProfile` is
`user-profile`. `--dir` names the app's folder; a screen whose files exist is refused. In an app with its files
in one folder (no `Views/` and `ViewModels/`), it writes them beside `app.py` and adds the import and path too.

## Build an executable

```bash
pip install "tesserae-ui[build]"
tesserae build --check
```

Makes one file in `dist/` with every file under the app's folder inside it, and `--check` runs it
briefly to see it start. Options: `--name`, `--icon`, `--console`, `--include GLOB`,
`--exclude GLOB`, and for an installer `--installer` with `--app-version`, `--identifier`,
`--publisher` and `--description`. See [Releasing Your App](releasing.md).

## Find the editor schemas

```bash
tesserae schema            # where the YAML schemas are
tesserae schema --settings # the `yaml.schemas` setting for Red Hat's YAML language server
```

See [Editor Support](editor-support.md).
