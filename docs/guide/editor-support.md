# Editor Support: YAML Schemas

Tesserae ships JSON Schemas for its YAML files, for [Red Hat's YAML language
server](https://github.com/redhat-developer/vscode-yaml) (the *YAML*
extension in VS Code, and any editor that runs `yaml-language-server`).
With one set up, an editor suggests node kinds, style fields, theme colour
roles, layout values and a built-in fragment's parameters as you type, shows
what each one means, and underlines a mistake such as `foregorund`.

| Schema | For |
| --- | --- |
| `tesserae-yaml-schema.json` | a view, `*_View.yaml` |
| `tesserae-shell-schema.json` | an app shell, `*_Shell.yaml` |
| `tesserae-component-schema.json` | a component fragment, `*_Component.yaml` |
| `tesserae-theme-schema.json` | a theme or a stylesheet |

They are JSON Schema draft-07, which Red Hat's server supports, and they
come with Tesserae (`tesserae schema` says where) and are published on this
site at `https://mindderivative.github.io/tesserae/schema/<name>`.

## Setting it up in VS Code

Install the **YAML** extension (`redhat.vscode-yaml`), then map the schemas
to your files with the extension's `yaml.schemas` setting. Tesserae prints it
for you, with the real paths on your machine:

```bash
tesserae schema --settings
```

Paste what it prints into your project's `.vscode/settings.json` (or your
user settings):

```json
{
  "yaml.schemas": {
    "/path/to/site-packages/tesserae/schema/tesserae-yaml-schema.json": ["**/*_View.yaml"],
    "/path/to/site-packages/tesserae/schema/tesserae-shell-schema.json": ["**/*_Shell.yaml"],
    "/path/to/site-packages/tesserae/schema/tesserae-component-schema.json": ["**/*_Component.yaml"]
  }
}
```

(`tesserae schema --settings` also maps `tesserae-theme-schema.json`. A
theme or stylesheet has no naming convention, so the globs it uses are a
guess, `**/*theme*.yaml` and `**/*stylesheet*.yaml`: change them to match
yours.)

The path changes if you move to a new virtual environment, so rerun the
command then. To avoid that, use the published URL instead. It needs a
connection, but it doesn't change:

```json
{
  "yaml.schemas": {
    "https://mindderivative.github.io/tesserae/schema/tesserae-yaml-schema.json": ["**/*_View.yaml"]
  }
}
```

### Or one file at a time

The server also reads a comment at the top of a file. A path in it is
resolved from the file's own folder, and a URL works too:

```yaml
# yaml-language-server: $schema=https://mindderivative.github.io/tesserae/schema/tesserae-yaml-schema.json
id: root
kind: Container
```

## What it knows, and what it can't

It knows what Tesserae accepts: the kinds, the keys of a node and of its
`text:`, `a11y:` and `handlers:`, every style field and what each takes (a
dimension, a spacing, a layout keyword `tre` understands), the theme's colour
roles and type and shape tokens, the icon names, the window buttons, and each
built-in fragment's `with:` parameters, with the defaults of the optional
ones. A key it doesn't know is flagged, which is how a typo shows.

It can't know what only your app knows:

- the ViewModel methods a `handlers:` entry names, or what a `bindings:`
  expression reads;
- your own fragments (`component: MyCard`): it accepts any name, and
  suggests the built-in ones;
- your own theme: a colour accepts any CSS colour, and suggests the theme
  roles.

In a fragment (`*_Component.yaml`), where a value can also be a
`{{ parameter }}` or chosen by one (`{if: ..., then: ..., else: ...}`), the
component schema allows that where the view schema does not.

## For contributors

The schemas are written by `tools/generate_yaml_schema.py` from Tesserae's
own code (the kinds, style fields, tokens, icons and fragments), and ask
`tre` for the layout keywords, so none of it is typed by hand. Run it again
after changing what a file may hold; the tests check that every YAML file in
the repository validates, that the mistakes above are rejected, and that the
committed files are what it writes. Run the language-server check
(below) as well when a file format changes.

!!! note "How it was checked"
    The tests check the schemas with a standard JSON Schema validator
    against every YAML file in the repository. Beyond that,
    `tools/check_schema_in_language_server.py` drives Red Hat's real
    language server (version 1.24.0 when this was written) over the Language
    Server Protocol, the way VS Code does: every view, shell, fragment and
    theme file in the repository opens with no diagnostics, kinds, style
    fields, handlers, colour roles and a fragment's parameters are suggested,
    and a typo or a wrong value is flagged. It needs node, so CI doesn't run
    it. It was not run inside VS Code itself, only the server it uses. If
    completion or a squiggle is wrong in your editor, please
    [open an issue](https://github.com/mindderivative/tesserae/issues) with
    the file.
