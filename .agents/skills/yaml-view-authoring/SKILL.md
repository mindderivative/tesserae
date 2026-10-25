---
name: yaml-view-authoring
description: Use when writing or changing a Tesserae view, stylesheet, theme or component (*_View.yaml, *_Stylesheet.yaml, *_Theme.yaml), a ViewModel that serves one, or the loader/schema code that reads them. Gives the file and naming rules, the node keys, how to validate without opening a window, the old-syntax traps, the known gaps, and which generated files to regenerate.
---

# Writing views, stylesheets and themes

The language is documented in `docs/guide/view-language.md` (the whole language), `docs/guide/naming-convention.md`, `docs/guide/layout.md`, `docs/guide/bindings.md` (expressions) and `design/yaml-language.md` (why each component needed what it did). Read the page for what you touch; this skill is the checklist and the traps. Do not write from memory: check a property against the widget's declaration (`docs/schema/tesserae-widget-schema.json`, or `docs/api/yaml.md`).

## Files and names

| File | Name is | Notes |
|---|---|---|
| `Counter_View.yaml` | `Counter` | a view; `name:` inside is its **bind key**, keep it equal to the file name |
| `Counter_ViewModel.py` | `Counter` | class `CounterViewModel`, `views = "Counter"` |
| `Brand_Theme.yaml` | `Brand` | `seed:`, `colors:`, `typography:`, `components:` |
| `Tasks_Stylesheet.yaml` | `Tasks` | a `styles:` list of rules; each names a `widget` |

CamelCase names. A view with `params:` is a component: another view calls it by name with the params as plain keys. A view with no `name:` has no ViewModel.

## A node

`widget:` (required), then the keys every node has: `name` (a handle, unique in the view), `if`/`for`/`key`, `slot`, `state`, `style`, `classes`, `handlers`, `a11y`, `interaction`, `visible`, `window_region`, `route`, `focus_group`, `children`. **Anything else is a property of the widget**, and an unknown one is an error with the nearest suggestion. State (`checked`, `selected`, `value`, `disabled`) is a property, never a style. Values and text may be `{{ expressions }}`: a safe Python subset, with a fixed list of functions and the lookup order loop variable, local state, params, ViewModel, app, built-ins.

Ids are assigned by the loader (`root.add`, `root.children[0]`, `[key]` under a `for:`); give a node a `name` when a ViewModel, a stylesheet rule, a test or hot reload has to find it.

## Validate without a window

Never trust a view you have not loaded. In order, fastest first:

1. **Render it**: `python3 tools/shot.py <folder> --view Main --out /tmp/shots/x.png` (see the `live-check` skill). A mistake is a `LoadError` that names the file, line and column and the nearest valid name, for example `Main_View.yaml:7:5: error: Rect: no property 'colour' (properties: disabled)`; the message is the last line of the traceback.
2. **`assert app.check() == []`** in a test: it compares every name, action and `expects:` entry of the open views with their ViewModels. This is the cheap guard that a view and its ViewModel stay in step.
3. **Schema**: `tesserae schema --project` writes a schema that includes your own views for the editor. After any change to a file format or the generated schemas, `tools/check_schema_in_language_server.py` runs them through the real YAML language server (needs node; not in CI; instructions in its docstring).
4. **Tests**: `tests/helpers.py` has `view_from(yaml_text)` to build a `View` from text; `tests/test_pixels.py` has `opened(tmp_path, yaml)` for a headless window.

## Stylesheet rules

A rule names a `widget` (or only `classes`, a `name` or a `style`), and may add `variant`, `size`, `shape`, `classes`, `name`, a `part` (a named node inside the widget's view) and a `state` (`hovered focused focus_visible pressed disabled selected checked expanded error read_only visited`). Specificity: a `name`, then the count of matched properties (all `classes` count as one), then a `state`, then the widget alone; a later rule wins a tie. A widget's shipped looks are the lowest layer, the app's stylesheet above them, and **a node's inline `style:` beats every rule for the fields it sets**.

## Traps

- **Old syntax.** `kind:`/`id:` instead of `widget:`/`name:`, `*_Component.yaml`, and the `Components/`, `Styles/` folders are the previous language: `app.load` still pairs such files by name (`docs/guide/naming-convention.md`, "Views in the older syntax"), but new work is written in the current one, and the current language refuses a `*_Style.yaml`. `tesserae migrate-yaml [PATH] [--write]` moves a project; it does not yet translate a call of a shipped fragment such as `ButtonFilled` (#290).
- **Known gaps** (open Backlog issues, so a silent no-op is not yet an error): a rule's `part:` that names no node of the widget raises no error (#288); `placement` or `offset` without `anchor` is accepted and does nothing (#289); `Link_Stylesheet.yaml` has no generated page and an unknown key in a stylesheet file is not refused (#291). Do not rely on these being accepted; do not document them as supported.
- **`foreground`** is a style extra of widgets that draw text or glyphs only; elsewhere it is an error that names who accepts it.
- A **spec-generated node key** (`spin`, `dial`, `graph`, `tooltip`) must be added in three places: `build._NODE_KEYS`, `view._props_equal`, and the exclusion set in `tools/generate_yaml_schema.py`.
- A docs example that uses `part:` names or expression lists is guarded by tests; keep the example true.

## After changing a view, a widget declaration, a component page entry or the expression language

Regenerate and commit the results, because tests compare them:

```bash
for g in generate_component_docs generate_yaml_docs generate_api_docs generate_yaml_schema generate_widget_schema; do .venv/bin/python tools/$g.py; done
python3 tools/docs_audit.py
```

`tools/component_docs.yaml` is the source of `docs/components/*.md`: edit it, never the pages. Then follow the `issue-workflow` skill (tests, full check, changelog, LOG).
