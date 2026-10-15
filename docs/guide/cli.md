# The `tesserae` Command

Installing Tesserae installs a `tesserae` command (`python -m tesserae` is the same).
It starts apps and screens from templates, moves a project to the current view syntax, builds an app into one executable, and
finds the editor schemas. `tesserae --version` prints the version, and `tesserae <command> --help` lists a command's options.

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

The template's files are written in the older view syntax (`kind:`, `component: ButtonFilled`). They run, and log once per file
that they are in the older syntax. The [project tutorial](../tutorial-project.md) is the same project written in the current one.

| Option | What it does |
| --- | --- |
| `--no-venv` | Makes the folders and files without the virtual environment, which needs the network to install Tesserae. |
| `--window` | Makes the app one [`Window_View.yaml`](windows-and-docks.md): a title bar, a navigation rail and two routed screens, Main and Settings. |
| `--custom-title-bar` | With `--window`: no OS title bar (`borderless: true`). The window's own [title bar](custom-title-bars.md): it moves the window and has the minimize, maximize and close buttons. The window is at least 640 by 400. |
| `--dir PARENT` | Makes the app in `PARENT` instead of here. |

Nothing is overwritten: a folder that isn't empty is refused with a one-line message (exit code 2).

## Add a screen

```bash
tesserae add screen Settings
```

This writes `Views/Settings_View.yaml` and `ViewModels/Settings_ViewModel.py` (a title and a Back button that
calls `self.app.back()`, in the older syntax like the rest of the template) and adds `app.load("Settings")` and its route (`settings`) to
`app.py`, above the marker comment `tesserae new` left there. Without the marker it
prints the lines to add. A CamelCase name gets a kebab-case route: `UserProfile` is
`user-profile`. `--dir` names the app's folder; a screen whose files exist is refused. In an app with its files
in one folder (no `Views/` and `ViewModels/`), it writes them beside `app.py` and adds the import and path too.

## Move a project to the current syntax

```bash
tesserae migrate-yaml            # reports what would change; writes nothing
tesserae migrate-yaml --write    # writes it, if every file checked out
```

`tesserae migrate-yaml [PATH]` (the project's folder, here by default) reads every `*_View.yaml`, `*_Component.yaml` and
`*_Stylesheet.yaml`, translates each, checks the result with the loader an app uses, and writes only if all of them load. `--force`
with `--write` writes the ones that did. Keep the project in version control: the old files are rewritten and a fragment is
renamed. The report lists the changes each ViewModel and `app.py` need, because Python is not rewritten. A call of a shipped
fragment that became one view with a property (`ButtonFilled` is `widget: Button` with `variant: filled`) is reported, and
written by hand. [Migrating](../migration.md#to-050) has the table of every change and of the shipped names.

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
