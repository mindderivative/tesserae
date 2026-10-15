# Editor Support: YAML Schemas

Tesserae ships JSON Schemas for its YAML files, for [Red Hat's YAML language
server](https://github.com/redhat-developer/vscode-yaml) (the *YAML*
extension in VS Code, and any editor that runs `yaml-language-server`).
With one set up, an editor suggests keys, style fields, theme colour
roles and layout values as you type, shows what each one means, and underlines
a mistake such as `foregorund`.

| Schema | For |
| --- | --- |
| `tesserae-widget-schema.json` | a view in the current language, `*_View.yaml`: one node, with a branch for each built-in widget and each view Tesserae ships, and its properties |
| `tesserae-stylesheet-schema.json` | a stylesheet of rules, `*_Stylesheet.yaml` |
| `tesserae-theme-schema.json` | a theme, `*_Theme.yaml` |
| `tesserae-yaml-schema.json` | a view written with `kind:` and `id:` (the older syntax) |
| `tesserae-component-schema.json` | a fragment written with `component:` (the older syntax), `*_Component.yaml` |
| `tesserae-style-schema.json` | a style file (the older syntax), `*_Style.yaml` |

They are JSON Schema draft-07, which Red Hat's server supports, and they
come with Tesserae: `tesserae schema` says where.

## What the schemas cover

- **A view in the current language** (`widget:`) is described by `tesserae-widget-schema.json`. It knows the keys every node has
  (`name`, `if`, `for`, `key`, `slot`, `state`, `style`, `classes`, `handlers`, `a11y`, `interaction`, `visible`, `route`,
  `focus_group`, `tooltip`, `params`, `expects`) and, for each built-in widget (`Container`, `Rect`, `Text`, `TextInput`,
  `Checkbox`, `Slider`, `Window`, ...) and each view Tesserae ships (`Button`, `Card`, ...), its properties or params with their types, choices
  and bounds. A value may be an expression (`"{{ width / 2 }}"`) wherever a number or a choice is. `style:` is every style field with what it takes.
- **Your own views** (`widget: TaskItem`) are known once you add them: `tesserae schema --project` writes a copy of the widget schema that has every view the
  project has, with its params, so an editor completes a call of one and flags a misspelt param or a missing one. A view of yours that has the name of one
  Tesserae ships replaces it, as in the loader.
- **A stylesheet of rules** (`widget:`, `variant:`, `size:`, `shape:`, `classes:`, `name:`, `part:`, `state:` and a `style:`) is described by
  `tesserae-stylesheet-schema.json`; the states are the real ones, and `style:` is the same fields as a node's.
- **A theme file** (`seed`, `colors`, `typography`, `components`) by `tesserae-theme-schema.json`.
- **The older syntax** keeps its schemas (`tesserae-yaml-schema.json` for a view, the component and style ones), which `tesserae schema --settings` does
  not map to `*_View.yaml` any more; `tesserae migrate-yaml` moves such a project to the current language.

## Setting it up in VS Code

Install the **YAML** extension (`redhat.vscode-yaml`), then map the schemas
to your files with the extension's `yaml.schemas` setting. Tesserae prints one
for you, with the real paths on your machine:

```bash
tesserae schema --settings --project
```

`--project` (here, or `--project DIR`) writes `.tesserae/tesserae-widget-schema.json` in the project, the widget schema with your views in it, and
maps `**/*_View.yaml` to it; without `--project` the views map to the packaged schema, which does not know your own. Paste what it prints into
your project's `.vscode/settings.json` (or your user settings):

```json
{
  "yaml.schemas": {
    "/path/to/project/.tesserae/tesserae-widget-schema.json": ["**/*_View.yaml"],
    "/path/to/site-packages/tesserae/schema/tesserae-stylesheet-schema.json": ["**/*_Stylesheet.yaml", "**/*stylesheet*.yaml"],
    "/path/to/site-packages/tesserae/schema/tesserae-theme-schema.json": ["**/*_Theme.yaml", "**/*theme*.yaml", "!**/*_View.yaml", "!**/*_Stylesheet.yaml"]
  }
}
```

The project schema is a snapshot: run `tesserae schema --project` again after you add a view or change a view's params (add `.tesserae/` to
`.gitignore`). The packaged paths change if you move to a new virtual environment, so rerun it then too.

### Or one file at a time

The server also reads a comment at the top of a file. A path in it is
resolved from the file's own folder, and a URL works too:

```yaml
# yaml-language-server: $schema=/path/to/site-packages/tesserae/schema/tesserae-widget-schema.json  (or the project's, in .tesserae/)
name: counter
widget: Container
```

## What it knows, and what it can't

It knows what Tesserae accepts of a built-in widget: the keys of a node and of its `a11y:`, every property and what it takes,
every style field and what each takes (a dimension, a spacing, a layout keyword `tre` understands), the theme's colour roles
and type and shape tokens, the icon names and the window buttons. A key it doesn't know is flagged, which is how a typo shows.

It can't know what only your app knows:

- the ViewModel methods a `handlers:` entry names, or what a `{{ }}` expression reads: `app.check()` compares them
  with the ViewModel without a window (see [Components & Embedding](components.md));
- your own views, unless `tesserae schema --project` has written them in (a snapshot);
- your own theme: a colour accepts any CSS colour, and suggests the theme roles.

## For contributors

The schemas are written by `tools/generate_yaml_schema.py` (`tools/generate_widget_schema.py` runs it) from Tesserae's
own code (the widgets, style fields, tokens and icons), and ask
`tre` for the layout keywords, so none of it is typed by hand. Run them again
after changing what a file may hold. The tests check that the committed files are what the tools write. Run the language-server check
(below) as well when a file format changes.

!!! note "How it was checked"
    The tests check the schemas with a standard JSON Schema validator
    against YAML files in the repository. Beyond that,
    `tools/check_schema_in_language_server.py` drives Red Hat's real
    language server over the Language
    Server Protocol, the way VS Code does. It needs node, so CI doesn't run
    it. It doesn't run inside VS Code itself, only the server VS Code uses. If
    completion or a squiggle is wrong in your editor, please
    [open an issue](https://github.com/mindderivative/tesserae/issues) with
    the file.
