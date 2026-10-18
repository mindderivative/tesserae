# Component Views

A **component** is a view with `params:`. Another view calls it by name, gives it values as plain keys, and may hand it children. There
is no separate kind of file for it: a component is `<Name>_View.yaml`, like any view. A component has no ViewModel of its own and no
state of its own beyond what it declares: it is part of the view that calls it, built where it is written. This is a different thing
from opening a whole view against a ViewModel, which [Components & Embedding](components.md) covers.

Tesserae's own [Material 3 components](../components/index.md) (`Button`, `Card`, `Tabs`, `Dialog`, ...) are views of exactly this kind,
and you can write your own the same way. The whole language is in [The View Language](view-language.md); this page is about writing
and calling components.

## Using one

```yaml
name: actions
widget: Container
style: {flex_direction: horizontal, gap: 8, padding: 16, align_content: center}
children:
  - {widget: Button, name: save, label: Save, icon: check, handlers: {on_click: save}}
  - {widget: Button, name: cancel, label: Cancel, variant: outlined}
```

- `widget: Button` is the call. It finds `Button_View.yaml`, first in your project and then among the views Tesserae ships.
- `label`, `icon` and `variant` are the component's params, written as plain keys. A param you leave out takes its default; one the
  component marks `required` must be there; a key the component does not declare is an error that names it.
- `name:` is optional. It is how a ViewModel, a stylesheet rule or a test finds this call again.
- Each widget's page under [Components](../components/index.md) lists its params.

The values are checked when the view loads, against what the component declares, and the error names the file, line and column:

```
Main_View.yaml:5:5: error: Stat: 'label' is required
Main_View.yaml:5:40: error: Stat: no property 'colour' (properties: label, unit, size)
Main_View.yaml:5:46: error: Stat: 'size' is 'xl', which is not one of: s, m
Main_View.yaml:5:43: error: Stat: 'n' takes a number from 0 to 10, got 11
```

### Handlers, bindings and names on a call

A call takes the keys every node takes. They go on the component's root, over what the root has:

```yaml
- widget: Button
  name: save
  label: Save
  handlers: {on_click: save}
  a11y: {label: Save the note}
  classes: [primary_action]
  style: {width: 160}
```

- `handlers:` run in the caller's names: `on_click: save` is the caller's ViewModel method, and `on_click: "saved = True"` writes the
  caller's state. If the component's root has a handler for the same event, the component's runs first and the call's after it.
- `style:`, `classes:`, `a11y:`, `interaction:` and `tooltip:` lie over the root's own. `style:` wins for the fields it sets and no
  others. `visible: false` hides the whole component.
- A value written as an expression (`label: "{{ 'Save changes' if dirty else 'Save' }}"`) is read where it is written, in the caller's
  names, and stays reactive inside the component. That is all a "binding" is now: there is no `bindings:` key.
- The component cannot see the caller's names, only its params. To let it change something of the caller's, pass a model param or a
  handler param (see below).
- With `for:`, every item gets the call's keys.
- A clickable root is a button for the keyboard and assistive technology too, with the state layer and ripple
  (see [Interaction](interaction.md)).

The call's `name:` is the prefix of everything inside it. The component's nodes that have a name are its **parts**, and the call
`save` above has `save.label` and `save.icon`. A stylesheet rule reaches a part with `part:`, and a test with the full id
(`root.save.label`).

## Writing your own

Put a `<Name>_View.yaml` anywhere in the project (`Views/`, `Components/`, a feature folder: it is found by name) and call it as
`widget: Name`.

```yaml
# Stat_View.yaml
params:
  label: {type: str, required: true, doc: What the number is}
  value: {type: float, default: 0}
  unit: {type: str, default: ""}
  size: {type: enum, choices: [s, m], default: s}
widget: Container
style: {flex_direction: vertical, gap: 2}
children:
  - widget: Text
    name: value
    text: "{{ format_number(value) }}{{ unit }}"
    typography_role: "{{ 'title_large' if size == 'm' else 'title_medium' }}"
    style: {foreground: on_surface}
  - widget: Text
    name: label
    text: "{{ label }}"
    typography_role: label_medium
    style: {foreground: on_surface_variant}
```

```yaml
# anywhere else
- {widget: Stat, name: users, label: Active users, value: "{{ active }}", size: m}
```

`params:` is a list of names (`[title, icon]`: each is required unless written `{icon: null}`) or a mapping of names to a type or to
`{type, default, choices, required, model, doc, min, max}`:

| Key | Meaning |
| --- | --- |
| `type` | one of `str int float bool color length icon enum list dict node nodes handler any` |
| `default` | the value when the call leaves it out (a param with a default is optional) |
| `choices` | the values an `enum` allows |
| `required` | the call must give it |
| `model` | the component changes it (see below) |
| `doc` | one line, shown by the editor and in the schema |
| `min`, `max` | the range a number may take |

!!! warning "Don't name a param `on`, `off`, `yes` or `no`"
    YAML reads those bare words as booleans before Tesserae sees them, so the name is refused. Name a boolean param `selected` or
    `enabled`, or quote the name.

### Children and slots

A call's `children:` are the component's content. The component says where they go with `widget: Slot`:

```yaml
# Panel_View.yaml
params:
  title: {type: str, required: true}
widget: Container
style: {flex_direction: vertical, gap: 8, padding: 16}
children:
  - {widget: Text, name: heading, text: "{{ title }}", typography_role: title_medium, style: {foreground: on_surface}}
  - widget: Slot                      # the default slot
  - widget: Slot
    name: actions                     # a named slot
```

```yaml
- widget: Panel
  name: profile
  title: Profile
  children:
    - {widget: Text, name: bio, text: "{{ bio }}", typography_role: body_medium, style: {foreground: on_surface}}
    - slot: actions                   # goes into the `actions` slot
      widget: Button
      name: edit
      label: Edit
```

- A child without `slot:` goes into the default slot.
- Slot content is written in the caller's names and keeps them. Its ids are the caller's, under the call: `profile.bio`.
- A component with no `Slot` takes no children: giving it some is an error (`Plain takes no children (its view has no Slot)`).
- A `Card` has a default slot for its content and an `actions` slot for its buttons, a `Dialog` takes its content as children.

### Letting the component change something of the caller's

A param with `model: true` that is given **one bare reference** to a Signal or to local state passes the thing itself, so the component's own
control edits the caller's value. The `Switch` below writes `dark` in the caller:

```yaml
# Setting_View.yaml
params:
  label: {type: str, required: true}
  checked: {type: bool, model: true, default: false}
widget: Container
style: {flex_direction: horizontal, align_content: center, gap: 12}
children:
  - {widget: Text, name: label, text: "{{ label }}", typography_role: body_large, style: {foreground: on_surface}}
  - {widget: Switch, name: toggle, selected: "{{ checked }}"}
```

```yaml
- {widget: Setting, name: dark_mode, label: Dark mode, checked: "{{ dark }}"}
```

Given an expression (`checked: "{{ not light }}"`) the component gets a copy that follows it, and a write by the component stays in the copy until the
expression next changes; given a literal or nothing it keeps its own value. A param without `model: true` follows what it is given and cannot be written.
[Two-way properties](view-language.md#two-way-properties) has the table.

A param of type `handler` takes an action of the caller's, to run when something happens in the component. The component calls it
like an action, and a param the caller left out does nothing when called:

```yaml
# Removable_View.yaml
params:
  label: {type: str, required: true}
  on_remove: {type: handler}
widget: Container
style: {flex_direction: horizontal, align_content: center, gap: 8}
children:
  - {widget: Text, name: label, text: "{{ label }}", typography_role: body_large, style: {foreground: on_surface}}
  - {widget: IconButton, name: remove, icon: close, label: Remove, handlers: {on_click: on_remove}}
```

```yaml
- widget: Removable
  for: tag in tags
  key: tag
  name: tag
  label: "{{ tag }}"
  on_remove: "tags = [t for t in tags if t != tag]"     # read in the caller's names
```

## Where the look is

A component holds structure and behaviour. Its look is **rules** that name it: a stylesheet lists them, and the shipped components
come with theirs.

```yaml
styles:
  - widget: Stat
    style: {padding: 12, background: surface_container, corner_radius: 12}
  - widget: Stat
    size: m
    style: {padding: 20}
  - widget: Stat
    part: label
    style: {foreground: primary}
```

- A rule names a `widget` and may add the params `variant`, `size` and `shape` (when the component declares them), `classes`, `name`,
  a `part` (a named node inside the component) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). The most
  specific rule wins.
- A node's inline `style:` beats every rule, for the fields it sets. A shipped component leaves its looks to rules for that reason, and
  a call's `style:` always has the last word.
- Rule values may be expressions over the component's params (`corner_radius: "{{ 12 if size == 'm' else 8 }}"`).
- Rules go in the app's stylesheet: `App(stylesheet="App")` finds `Styles/App_Stylesheet.yaml`. Every shipped component's rules are the
  lowest layer under it, so yours override them, field by field.
- Every shipped [stylesheet](../stylesheets/index.md) has a page, and the [Style](view-language.md#style) section of the language page is
  the whole rule format.

### Replacing a shipped component

A `Button_View.yaml` in your project is used instead of the one Tesserae ships, for every `widget: Button` in the app, and **its shipped
rules go with it**: the replacement starts with no look until your own stylesheet gives it one. To change only how a shipped component
looks, leave the view alone and write rules.

## Repeating a view: `for:`

`for:` on a call builds it once for each element of a list. If the list can change while the app runs, the loop is reactive and needs a
`key:`: the identity of an element, so a node whose key stays is kept.

```yaml
- widget: Chip
  for: tag in tags
  key: tag
  name: tag
  label: "{{ tag }}"
  handlers: {on_click: "picked = tag"}
```

- The loop variable is in scope for the call's params, its handlers and the children written inside it.
- A list that is replaced updates the screen; one changed in place is not noticed. Write `tags = tags + ['new']`, not `tags.append(...)`.
- A component can take a whole list as one param (`items`, `tabs`) and repeat inside itself. That is how `Tabs`, `NavigationRail`,
  `Menu` and `ButtonGroup` take their items:

```yaml
- widget: Tabs
  name: tabs
  selected: "{{ section }}"
  tabs:
    - {value: inbox, label: Inbox}
    - {value: sent, label: Sent}
```

For rows that are thousands long use a `VirtualList` ([The View Language](view-language.md#long-lists)).

## Optional parts

`if:` on a node builds it only while its expression is true, and it can read the component's params. This is how a component has an
icon only when it was given one:

```yaml
params:
  label: {type: str, required: true}
  icon: {type: icon, default: ""}
widget: Container
style: {flex_direction: horizontal, align_content: center, gap: 8}
children:
  - {widget: Icon, name: icon, if: "icon != ''", icon: "{{ icon }}", style: {foreground: on_surface}}
  - {widget: Text, name: label, text: "{{ label }}", typography_role: label_large, style: {foreground: on_surface}}
```

For a value that changes with a param, write the expression: `padding: "{{ {'left': 16, 'right': 20} if icon != '' else 20 }}"`.
`visible:` keeps a node built and takes it out of the layout; `if:` does not build it at all
(see [The View Language](view-language.md#repeating-choosing-and-remembering)).

## Nesting

A component can call other components, and its parts are named under the outer call's name too (`save.label.text`). A component may
call itself, which is how a tree is written, to a depth of 64.

## Looking at the shipped ones

The views Tesserae ships are in the `tesserae/views` folder of the package: `Button_View.yaml` with `Button_Stylesheet.yaml` beside it.
They are written in exactly this language and are the best examples of it: `Card` (slots), `ButtonGroup` (a list param and a
`for:`), `Tabs` (a model param), `Dialog` (an `Overlay`).
