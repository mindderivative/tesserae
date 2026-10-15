# Editor Support: YAML Schemas

Tesserae ships JSON Schemas for its YAML files, for [Red Hat's YAML language
server](https://github.com/redhat-developer/vscode-yaml) (the *YAML*
extension in VS Code, and any editor that runs `yaml-language-server`).
With one set up, an editor suggests keys, style fields, theme colour
roles and layout values as you type, shows what each one means, and underlines
a mistake such as `foregorund`.

| Schema | For |
| --- | --- |
| `tesserae-widget-schema.json` | a view in the current language: one node, with a branch for each built-in widget and its properties |
| `tesserae-theme-schema.json` | a theme (`*_Theme.yaml`) |
| `tesserae-yaml-schema.json` | a view written with `kind:` and `id:` (the older syntax), `*_View.yaml` |
| `tesserae-component-schema.json` | a fragment written with `component:` (the older syntax), `*_Component.yaml` |
| `tesserae-style-schema.json` | a style file, `*_Style.yaml` |

They are JSON Schema draft-07, which Red Hat's server supports, and they
come with Tesserae: `tesserae schema` says where.

## What the schemas cover today

- **A view in the current language** (`widget:`) is described by `tesserae-widget-schema.json`. It knows the keys every node has
  (`name`, `if`, `for`, `key`, `slot`, `state`, `style`, `classes`, `handlers`, `a11y`, `interaction`, `visible`, `route`,
  `focus_group`, `tooltip`, `params`, `expects`) and, for each built-in widget (`Container`, `Rect`, `Text`, `TextInput`,
  `Checkbox`, `Slider`, `Window`, ...), its properties with their types and choices. A widget that is a view, the ones Tesserae
  ships (`Button`, `Card`, ...) and your own, is not in it: an editor will flag a call of one. The
  loader is the check that knows them, and says the file, line and column.
- **`tesserae schema` and `--settings`** map `**/*_View.yaml` to the older view schema (`tesserae-yaml-schema.json`), so a view in the
  current language is flagged all over by it. Map `**/*_View.yaml` to the widget schema yourself, as below.
- **A stylesheet of rules** (`widget:`, `variant:`, `part:`, `state:`) is not described by the theme schema, which knows
  the older rule keys (`kind`, `classes`, `id`). A theme file (`seed`, `colors`, `typography`, `components`) is.

## Setting it up in VS Code

Install the **YAML** extension (`redhat.vscode-yaml`), then map the schemas
to your files with the extension's `yaml.schemas` setting. Tesserae prints one
for you, with the real paths on your machine:

```bash
tesserae schema --settings
```

Paste what it prints into your project's `.vscode/settings.json` (or your
user settings), and point the views at the widget schema, which sits in the same folder:

```json
{
  "yaml.schemas": {
    "/path/to/site-packages/tesserae/schema/tesserae-widget-schema.json": ["**/*_View.yaml"],
    "/path/to/site-packages/tesserae/schema/tesserae-theme-schema.json": ["**/*_Theme.yaml"]
  }
}
```

The path changes if you move to a new virtual environment, so rerun `tesserae schema` then to read the folder.

### Or one file at a time

The server also reads a comment at the top of a file. A path in it is
resolved from the file's own folder, and a URL works too:

```yaml
# yaml-language-server: $schema=/path/to/site-packages/tesserae/schema/tesserae-widget-schema.json
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
- your own views (`widget: TaskItem`) and the ones Tesserae ships;
- your own theme: a colour accepts any CSS colour, and suggests the theme roles.

## For contributors

The schemas are written by `tools/generate_yaml_schema.py` and `tools/generate_widget_schema.py` from Tesserae's
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
