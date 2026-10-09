# The Tesserae view language (0.5.0)

Phase 1 of [#209](https://github.com/mindderivative/tesserae/issues/209). This is the spec the later phases build and test against.
**Status: draft for the user's review.** Implemented so far: the expression language (phase 2), the node model (phase 3) and composition (phase 4), ViewModel binding with a renderer (phase 5), style rules (phase 6) and migration (phase 7).

Conventions: **Decided** marks what the user decided (2026-10-08); **Proposed** marks what this document adds and the user may change;
**Reserved** marks a place the language may grow without breaking what is written here. "Old" means 0.4.x.

## 0. Goals and non-goals

Goals: one way to say each thing; intuitive and consistent file shapes; widgets that are validated; state that is a property; a single
expression language for build time and run time; a ViewModel that serves several views at once; errors that say what to change.

Non-goals: a general-purpose programming language (that was YS, not adopted); changing the theme, token or stylesheet vocabularies
beyond what section 10 says; touching `tre`.

## 1. Files

**Decided: one suffix.** Every renderable file is `<Name>_View.yaml`, wherever it lives. A **view** is one node (section 2) plus optional
header keys. A view with `params:` is a **component** in the old sense; there is no other difference. Folders are for the author:
`Views/`, `Components/`, a feature folder; lookup (section 4) searches all of them by name.

Other files are unchanged: `<Name>_Theme.yaml` (a theme), `<Name>_Stylesheet.yaml` (style rules, section 10), `<Name>_ViewModel.py`.
Old `*_Component.yaml` and `*_Style.yaml` are accepted by the compatibility loader only (section 15).

A view file is valid YAML with exactly one top-level mapping, the root node. Header keys, valid only on the root, come first by convention:

```yaml
name: nav               # optional: the view's bind key and handle (section 5)
params: [items, selected]   # optional: the view's inputs (section 6)
expects: {...}          # optional: the contract (section 11)
widget: Navigation      # the root node
...
```

## 2. Nodes

A node is a mapping with a **`widget:`** key (**Decided**: the single node key). Every other key is one of:

| Key | Meaning | Valid on |
|---|---|---|
| `widget` | which widget (section 4) | every node |
| `name` | optional unique handle (section 5) | every node |
| `if`, `for`, `key` | directives (section 7) | every node |
| `slot` | which slot of the parent a child goes into (section 6) | a child |
| `state` | local state (section 9.2) | every node |
| `style` | universal layout and paint plus the widget's declared extras (section 10) | every node |
| `classes` | extra names for stylesheet rules (section 10) | every node |
| `handlers` | events to actions (**Decided**: stays as a mapping, section 9) | every node |
| `a11y` | accessibility overrides (section 12) | every node |
| `interaction` | the state layer and ripple: `true`, `false` or a colour role (as now) | every node |
| `window_region` | `drag` (as now) | every node |
| `route` | makes a view a screen of the app (as now; only on a node whose widget is a view, inside a Window) | a view call |
| `children` | child nodes | every node |
| *anything else* | a **property** of the widget (section 3) | per widget |

`params` and `expects` are header-only. `widget`, `name`, `params`, `slot`, `state`, `key` are **structural**: their values are never
`{{ }}` expressions. `if` and `for` take an expression as their whole value (section 7).

An unknown key is an error (section 14), with a suggestion.

## 3. Widgets and properties

A **widget** has a name, a set of **properties**, a set of **parts**, optionally a set of **style extras**, and an implementation. The
properties are everything an author may write on a node besides the universal keys in section 2. **Decided: state is properties** (`value`,
`selected`, `checked`, `disabled`, `open`, `collapsed`, `expanded`, `icon`, `label`, `badge`, ...), not style, not build-time parameters.

A property declaration:

| Field | Meaning |
|---|---|
| `type` | `str`, `int`, `float`, `bool`, `color` (a theme role, `#RRGGBB[AA]` or a CSS colour), `length` (a number, `auto` or `N%`), `icon` (a built-in icon name), `enum`, `list`, `dict`, `node` (one child node), `nodes` (a list of nodes), `handler`, `any` |
| `default` | the value when the property is not given |
| `choices` | for `enum`: the allowed values; an invalid one is an error listing them |
| `required` | `true` makes it an error to omit |
| `model` | `true` marks a property the user edits (`value` of a text field, `checked`, `selected` of a switch, `value` of a slider): **Proposed**, section 9.3 |
| `doc` | one line, shown by the editor and in the generated reference |

Any property may be given a literal or a `{{ expression }}` (section 8), whose value is coerced to `type` (a failed coercion is an error with
the offending value). `nodes` and `node` properties take node mappings, not expressions.

A widget is **built in** (Python, registered with its declarations) or a **view** (a file with `params:`). Both declare properties the same
way, so the schema generator, the editor and the validator treat them alike. Views declare theirs in the header:

```yaml
params:
  label: {type: str, required: true}
  variant: {type: enum, choices: [filled, tonal, elevated, outlined, text], default: filled}
  icon: {type: icon, default: null}
  selected: {type: bool, default: false, model: true}
  disabled: bool                 # a bare type: no default, not required (default false for bool, null otherwise)
```

and a short form where nothing needs declaring: `params: [label, icon]` (all `any`, all required unless written `{name: default}`).

**Widgets built in Python** declare the same in code:

```python
@widget("Slider")
class Slider(Widget):
    value = Property(float, default=0.0, model=True)
    min = Property(float, default=0.0)
    max = Property(float, default=1.0)
    step = Property(float, default=None)
    disabled = Property(bool, default=False)
    extras = ("track_height",)           # style extras this widget accepts (section 10)
    parts = ("track", "handle")          # parts a stylesheet can address
```

An **unknown property is an error**: `Slider: no property 'valu'. Did you mean 'value'? (properties: value, min, max, step, disabled)`.
The 0.4.x silent acceptance of `placeholder:` on a text field, `selected:` on a plain `Rect`, or `on_key_down:` in handlers is gone.

## 4. Which widget a name means

`widget: Name` resolves, in order: (1) a widget registered by the app (`app.register_widget`), (2) a built-in widget, (3) a view file
`Name_View.yaml` found in the project (`Views/`, `Components/`, then anywhere under the root with `recursive`, as `Project` does today),
(4) a view file shipped with Tesserae. The first match wins; a name found in two places in the same step is an error naming both files
(as `Project` does today). The author never says which kind it is.

**The 13 names that are both a kind and a fragment today** (`Checkbox`, `Slider`, ...) are one built-in widget with the fragment's
conveniences absorbed into its properties.

A view found by name is **instantiated** where it is written: its root node replaces the call, its `params:` are the call's properties, and
its `name:` and the call's `name:` combine (section 5).

## 5. Names, ids and handles

- `name:` is **optional** (**Decided**) and unique among siblings *and* within the view's naming scope (a name is a path segment, so a
  parent and a child may share one). A name is `[A-Za-z_][A-Za-z0-9_]*`.
- The **loader assigns every node a stable id**: the path from the view root, where each segment is the node's `name:` if it has one,
  else its position (`root.children[2]`), else, under a `for:`, its `key:` (`rows[item-7]`). Ids are never authored.
- **Parts**: the nodes a fragment's author names are its **parts**, the public interface a stylesheet and a ViewModel may address
  (`label`, `icon`, `pill`). Unnamed nodes are internal and not addressable.
- When a view is instantiated under a call named `nav`, its parts are `nav.label`, `nav.item[3].icon`, ... (the call's name is the
  prefix, as pyCopper and the current namespacing do).
- **Hot reload** reconciles by id, so a node that keeps its `name` or `key` keeps its state through edits and one that is only positional
  may be rebuilt when a sibling is inserted. Authors who want a node to survive reordering give it a `name` (or, in a loop, a `key`).
- **Handles**: a ViewModel reaches a node by name: `self.views["main"].node("save")` (section 11). Nodes without a `name` are not
  reachable from Python; that is deliberate.
- The old `id: root` at the top of every view is simply dropped by the migration tool.

## 6. Composition: params, children and slots

**Params.** A view's `params:` header (section 3) lists its properties. A call gives them as plain keys. A param may be a reactive
expression, which stays reactive inside the view: **an expression at a call site is evaluated in the caller's scope** (lexical scope), not
the callee's (pyCopper's reference lists the opposite as a trap; this removes it).

```yaml
widget: Button
label: "{{ 'Save changes' if dirty else 'Save' }}"      # evaluated where it is written; follows `dirty`
disabled: "{{ not form_valid }}"
```

**Children.** `children:` is valid on any node; for a view call they are the **slot content**. A view says where they go with `widget: Slot`:

```yaml
# Card_View.yaml
params: {variant: {type: enum, choices: [elevated, filled, outlined], default: elevated}}
widget: Container
variant: "{{ variant }}"
children:
  - widget: Slot                 # the default slot
  - widget: Slot
    name: actions                # a named slot
```
```yaml
widget: Card
variant: outlined
children:
  - widget: Text
    text: Title
  - slot: actions                # goes into the `actions` slot; without `slot:` a child goes into the default one
    widget: Button
    label: Share
```

A view with no `Slot` and a call with `children:` is an error ("`Card` takes no children"). Slot content is evaluated in the **caller's**
scope and keeps the caller's names; its ids are the caller's.

**Recursion.** A view may instantiate itself (a tree); the loader caps depth at 64 and reports the chain.

## 7. Directives: `for:` and `if:`

**`for:`** repeats the node (and its subtree) for each element:

```yaml
- for: item in items            # or:  for: i, item in enumerate(items)
  key: item.id                  # identity: required when `items` is reactive
  widget: ListItem
  headline: "{{ item.title }}"
  handlers: {on_click: "open(item.id)"}
```

The loop variable is in scope for the node and its subtree, **including its handlers** (so a per-item action is one line). `items` is any
expression yielding a list, tuple, dict (its keys), `range(...)` or a string. If the expression reads reactive names (a ViewModel Signal of
a list, say), the loop is **reactive**: when the list is replaced, nodes whose `key` persists are kept, new ones are built, removed ones
are destroyed, and order follows the list. If it reads only static values it is expanded once, at build time. Reactive without `key` is an
error. Nested `for:` is allowed. `for:` may not appear on a root node.

**`if:`** includes the node only when the expression is truthy:

```yaml
- if: unread > 0
  widget: Badge
  label: "{{ unread }}"
```

`if:` is reactive the same way; a node under a false `if:` is not built (and its handlers and bindings do not run). `if:` and `for:` may both
appear on one node (the `if:` is tested per element). There is no `else` in this release (**Reserved**: `elif:`, `else:` as adjacent siblings).

The whole value of `if:` and `for:` is an expression; they do not take `{{ }}`.

## 8. Expressions

**Decided: one language, a sandboxed subset of Python.** Used wherever `{{ ... }}` appears (properties, text, `if:`, `for:`, handlers).
Everything between `{{` and `}}` is one expression; a string with text around it (`"Hello {{ name }}!"`) is a template whose parts are
joined (a template is reactive if any part is). A property whose entire value is a single `{{ }}` keeps the value's type (a bool stays a
bool); a template always yields a string.

### 8.1 Grammar

Parsed with Python's `ast` (mode `eval`), then checked: only these node types are allowed; anything else is an error naming it.

| Allowed | Notes |
|---|---|
| `Constant` | numbers, strings, `True`, `False`, `None` |
| `Name` | resolved by 8.3 |
| `Attribute` | read-only; 8.4 |
| `Subscript`, `Slice` | `a[i]`, `a[1:3]`, `d['k']` |
| `UnaryOp` | `not`, `-`, `+` |
| `BinOp` | `+ - * / // % **` (limits in 8.6) |
| `BoolOp` | `and`, `or` |
| `Compare` | `== != < <= > >= in not in is is not` |
| `IfExp` | `a if c else b` (**the conditional expression**) |
| `JoinedStr`, `FormattedValue` | f-strings; the embedded expressions are checked by the same rules |
| `List`, `Tuple`, `Dict`, `Set` | displays |
| `ListComp`, `DictComp`, `SetComp`, `GeneratorExp`, `comprehension` | with `if`; the step budget applies |
| `Call` | only calls to whitelisted functions and methods (8.5) and, in handlers, ViewModel methods (section 9) |
| `Starred` | in calls and displays |

**Not allowed:** `Lambda`, `Await`, `Yield`, `NamedExpr` (`:=`), any statement in an expression, dunder attributes, `format` and
`format_map` (they reach attributes through the format mini-language), `getattr`, `eval`, `exec`, `open`, `type`, `globals`, `__import__`,
anything not in 8.5.

### 8.2 Static and reactive

The loader classifies every expression by the **free names** it reads (after scope resolution, 8.3):

- **Static**: only literals, params with static values, loop variables over static lists, and built-ins. Evaluated **once at build time** and
  the value substituted (this is the build-time arithmetic, variants by value and conditionals that 0.4.x could not do:
  `corner_radius: "{{ height / 2 }}"`).
- **Reactive**: reads a ViewModel Signal or Computed, local `state`, an interaction state, or `app` state. Compiled to a **binding**: it is
  re-evaluated when any of those it read changes (dependency tracking as `Effect` does today) and the node's property is set.
- A param whose call-site value is reactive makes every expression inside the view that reads that param reactive.

The author writes the same syntax either way; the loader tells them apart. A reactive expression in a place that cannot be reactive (a
structural key, `name`, `widget`, `params`) is an error: "`name` must be static".

### 8.3 Names and scope

A name resolves, innermost first:

1. **loop variables** (`item`, `i`) from enclosing `for:`
2. **local `state`** of the node and its ancestors (the nearest wins)
3. **interaction state** of the node's widget (`hovered`, `focused`, `pressed`; reserved names, 8.7)
4. **params** of the view the expression is written in (the *caller's* scope for a value written at a call site)
5. the **bound ViewModel** of the view (public attributes and methods; underscore names are invisible)
6. the **app state** (`App(state=...)`) and the reserved root `app` (`app.maximized`, `app.active`, `app.current_screen`, as now)
7. **built-ins** (8.5)

An unresolved name is a **load error** naming the file, line and column, with the nearest names (did-you-mean) once the ViewModel is
known. A view with no ViewModel resolves against 1, 2, 3, 4, 6 and 7 only and reports a name that needs one ("`count` is not defined: this
view has no ViewModel").

### 8.4 Signals as values and attribute access

**Decided: a Signal reads as its value.** `{{ count }}` is the value of the Signal `count`. When the name or attribute resolves to a
`Signal` or `Computed`, the evaluator **unwraps** it (and, in a reactive expression, subscribes). The one exception is a method call on it:
`count.get()` keeps working (a `Call` whose function is `Attribute(value=X, attr='get')` evaluates `X` without unwrapping). Writing is
only in handlers (section 9).

**Attribute access** on values is read-only and limited:
- on a mapping, `a.b` means `a['b']` when `'b'` is a key (so loop items from JSON-like data read naturally: `item.title`);
- on a ViewModel or `app`, public attributes and the properties listed in the object's `__expose__` (default: public non-callable
  attributes and `Signal`/`Computed`);
- on `str`, `list`, `dict`, `tuple`, `int`, `float`: only the whitelisted methods in 8.5;
- never on anything whose attribute name starts with `_`.

### 8.5 Built-in functions and methods

| Kind | Allowed |
|---|---|
| Functions | `len`, `min`, `max`, `abs`, `round`, `sum`, `str`, `int`, `float`, `bool`, `sorted`, `reversed`, `range`, `enumerate`, `zip`, `any`, `all`, `list`, `dict`, `tuple`, `set`; Tesserae's `format_number(x, digits)`, `pluralize(n, 'item', 'items')`, `clamp(x, lo, hi)` |
| `str` methods | `lower upper title capitalize strip lstrip rstrip split splitlines join startswith endswith replace find count zfill isdigit isalpha center ljust rjust removeprefix removesuffix` |
| `list`, `tuple` methods | `index count` |
| `dict` methods | `get keys values items` |

`format_number`, `pluralize` and `clamp` are the cases that made "formatting" a gap (#116, L5), without allowing `format`.

### 8.6 Limits (the sandbox)

Every evaluation has a **step budget** (default 200 000 visited AST nodes, counting comprehension iterations) and these caps, each a
named error: expression length 2 000 characters; AST depth 40; `range` length 100 000; a repeated sequence (`'a' * n`) at most 1 000 000
items; `**` with an exponent above 64 or a result beyond 2^1024; string results over 1 MB. There is no recursion (no definitions) and no I/O.
A function call that is not in 8.5 (and, in a handler, not a ViewModel method) is an error, not a `NameError`.

**Security test plan** (phase 2): a corpus of escapes that must all fail to load: `().__class__.__bases__`, `__import__('os')`,
`getattr`, `[].__class__.__mro__`, `"{0.__class__}".format(x)`, f-string attribute escapes, lambda tricks, generator frame access, name
shadowing of built-ins, unicode-identifier tricks, deep nesting, huge `range`, repeat and `**`; plus a fuzzer over the `ast` node set.
Every rule above has a test that fails if the rule is removed (mutation-checked).

### 8.7 Reserved names

`hovered`, `focused`, `pressed` (interaction state of the nearest widget with `interaction`), `event` (in handlers), `app`, `True`, `False`,
`None`, and the names in 8.5. A ViewModel attribute, param or loop variable with a reserved name is an error at the point it is defined.

## 9. Handlers and local state

### 9.1 Handlers (decided: `handlers:` stays)

```yaml
handlers:
  on_click: save                      # a ViewModel method (as now)
  on_hover_enter: "hint = 'Save'"     # a statement
  on_change: "query = event.value; page = 0"     # several, separated by ;
```

The event names are today's (`on_click`, `on_hover_enter`, `on_hover_exit`, `on_change`, `on_focus_enter`, `on_focus_exit`, `on_tap`,
`on_long_press`, `on_pan`, `on_pinch`, `on_touch_*`, `on_file_*`, `on_link`) **plus** `on_key` (**Proposed**: with `event.key` and
modifiers; the missing keyboard handler of #116, L11). An unknown event name is an error (it is silently ignored today).

A handler value is either a **dotted name** (`save`, `window.close`, `surface.dismiss`, `navigate.back`, `navigate.Settings`): the action
as now, or **statements** in this grammar:

```
statements := statement (";" statement)*
statement  := assignment | call
assignment := target ("=" | "+=" | "-=" | "*=" | "/=") expression
target     := Name                     # a local state variable, or a writable Signal of the ViewModel / app state
call       := Name "(" args ")"        # a ViewModel method, or a built-in action (window.minimize(), navigate.back())
```

Expressions on the right are section 8; `event` is in scope, with the event's documented attributes (`x`, `y`, `key`, `value`, `delta_x`, ...);
loop variables of enclosing `for:` are in scope. Assigning to a name that is not a local state variable or a writable Signal is a load error
("`items` is not writable"). **Nothing else**: no loops, no conditionals as statements (use the expression form: `x = a if c else b`), no
definitions, no attribute assignment, no calls to anything but ViewModel methods and the built-in actions.

**Reserved** (**Decided**: "if we need to add more then we will reserve the right to do what is needed"): `if` and `for` statements,
operations on collections (`append`, `del`), `return`, access to the event loop (`after(ms, ...)`), and writes through attributes. They are
errors today, with a message naming them as not yet available.

A handler runs **synchronously on the UI thread**; errors in it are logged with the file and line (as `simulate` shows today) and do not
stop the app.

### 9.2 Local state

```yaml
widget: Chip
variant: filter
label: Unread
state: {on: false}                  # declared here, readable by this node's subtree
selected: "{{ on }}"
handlers: {on_click: "on = not on"}
```

`state:` is a mapping of names to initial values (literals or static expressions). It lives **per node instance** (per row under `for:`,
per embedding of a view), starts at its initial value, and is reactive. It survives hot reload of the file when the node keeps its
`name` or `key`. It is not visible to the ViewModel unless the node is named and the ViewModel reads `self.views[...].state("on")`
(section 11). Local state is for presentation (open, on, hovered row); anything the application cares about belongs in the ViewModel.

### 9.3 Model properties (two-way) — Proposed

A property declared `model: true` (the text of a `TextField`, `checked`, `selected`, a slider's `value`) is **two-way** when it is given a
**bare writable reference** (`{{ name }}` where `name` is a Signal or local state), and **one-way** for any other expression (the user's
edit then has nowhere to go and the widget reverts to the expression's value). This replaces `two_way:` and `bindings:`.

```yaml
widget: Switch
selected: "{{ dark }}"              # two-way: toggling writes `dark`
```
```yaml
widget: Switch
selected: "{{ mode == 'dark' }}"    # one-way: shown, but the user's toggle does not write `mode`
handlers: {on_change: "mode = 'dark' if event.value else 'light'"}
```

## 10. Style

`style:` holds the **universal** set, valid on every widget, validated for type and range:

| Section | Fields |
|---|---|
| Size and spacing | `width height min_width max_width min_height max_height aspect_ratio padding margin` |
| Flex | `flex flex_direction flex_wrap gap` |
| Alignment | `align_content align_self spread align_wrapped` |
| Grid | `display grid_template_columns grid_template_rows grid_auto_columns grid_auto_rows grid_auto_flow grid_column grid_row row_gap column_gap align_tracks align_cells` |
| Position | `position x y z_index sticky` |
| Docking | `zone` (an error unless the parent is a `Dock`, as now) |
| Paint and effects | `background border_width border_color corner_radius opacity elevation clip_children blur backdrop_blur blend_mode filter cursor` |

**`foreground` is not universal**: it is an **extra** declared by the widgets that draw glyphs or text (`Text`, `Icon`, `Svg`, `Link`, and
any widget that says so). A widget's **extras** are listed in its declaration (section 3) and in its generated reference page; anything not
universal and not an extra is an error with a suggestion (`Container: style 'foreground' is not valid here; widgets that accept it: Text,
Icon, Svg, Link`). This replaces the unevenly checked flat 48.

**Named looks are properties**, not styles: `variant:`, `size:`, `shape:` where a widget defines them (a Button's `variant: tonal`). A
stylesheet maps them to style.

**Stylesheet rules** (`<Name>_Stylesheet.yaml`, `styles:`, **Proposed shape**; the cascade details are phase 6):

```yaml
styles:
  - widget: Button                 # a widget name
    variant: tonal                 # optional: variant, size, shape, classes, name
    part: label                    # optional: a part of the widget (default: the root)
    state: hovered                 # optional: hovered | focused | pressed | disabled | selected | checked | expanded
    style: {foreground: on_secondary_container}
```

Specificity, high to low: `name` (an id), then the number of matched properties (`variant`, `size`, `shape`, `classes`), then `state`, then
`widget` alone; later rules win ties. Inline `style:` on a node beats rules **only for the fields it sets** (fixing the 0.4.x trap where a
fragment's inline style beat class rules, #116 L4). **Interaction state selectors** (`hovered` ...) are what let stylesheets, not
per-component bindings, draw the hover and press looks.

**Reserved** here, specified in phase 6: `transition:` (`{property: {duration, easing}}`, #116 L8), role-with-alpha colours
(`primary@12%`), per-corner `corner_radius`, the `full` shape token.

## 11. ViewModels and views

**Decided:** ViewModels bind to **named** views; a view never names its ViewModel; **one ViewModel instance serves many views at once**; a
view without a `name:` is not bound and is for static visuals.

```python
class DataViewModel(ViewModel):
    views = ["data_pie", "data_list"]        # the names of the views it serves (a string means one)

    def __init__(self):
        super().__init__()
        self.rows = Signal([...])
```

- **The bind key** is the root `name:` of a view (`name: data_pie`). The ViewModel's `views` lists the keys it serves.
- **One instance.** `app.bind(DataViewModel)` creates it **once, lazily**, when the first view it serves is built; `app.bind(instance)`
  uses an instance you made. **Every view whose name is in `views` is bound to that one instance**, however many there are and wherever
  they are (both visible in one window, as in the pie chart and the list). A view instantiated twice is bound to the same instance twice. A
  change to `rows` updates all of them.
- **Per-instance ViewModels are opt-in**: `app.bind(factory=DataViewModel)` creates one per view instance. This is for the rare case a view
  needs its own mutable model; rows and repeated items use `for:` and `state:` instead.
- **Discovery.** `app.load("Data")` finds `Data_View.yaml` and, by project lookup, any `*_ViewModel.py` whose class declares a `views` that
  contains the view's name (the file name is a convenience for *finding*, not a binding rule). A ViewModel that serves a name no view has
  is a warning when `app.run()` starts.
- **Resolution** (8.3): a view bound to several names of one ViewModel resolves `{{ }}` and `handlers` against that one instance.
- **Handles.** `self.views` is a mapping from bind key to a **view handle** (`.node(name)`, `.state(name)`, `.show()`, `.hide()`). A
  ViewModel can show one of its views in place of another: `self.show("data_phone", "data_list")` (**Decided** by the user: the second argument is the view it replaces, a name or a list; **Reserved**: declared groups,
  `views = {"data": [...], "phone": [...]}`).
- **Lifetime.** A ViewModel is created before the first view it serves is attached and lives until the app ends (or `app.unbind(...)`).
  `ViewModel.on_attached(view_handle)` and `.on_detached(view_handle)` are called per view.
- **Old ViewModels** (`def __init__(self, view)` and `super().__init__(view)`) keep working in the compatibility release; the injected
  view is the first bound view and `self.view` stays.

**The contract.** A view may declare `expects:` in its header (**Proposed**; optional): the names its expressions read and the handlers it
names, as data: `expects: {count: int, rows: list, add: handler}`. It is never an import. It gives the editor and the schema something to
check against before a ViewModel exists, and lets a ViewModel be checked against a view's contract (`app.check()` and the tests) without the
window.

## 12. Accessibility

`a11y:` keeps its keys (`label`, `role`, `hidden`, `live`, `level`) and gains the states and relations that were missing (#116, L12):
`description`, `expanded`, `pressed`, `selected`, `checked`, `controls` (a part name), `current`, `value_text`. Each is a literal or an
expression (reactive). The built-in widgets set their own correct roles and states from their properties (a `Tab` is `role: tab` with
`selected`; a `Disclosure` has `expanded`), so authors rarely write `a11y:`. The roles are today's 23 plus `navigation`, `toolbar`,
`separator`, `option`, `listbox`, `combobox`, `search`, `status`, `banner`, `complementary`, `radiogroup`, `grid`, `gridcell`, `spinbutton`
(**Proposed**; each needs tre's AccessKit mapping checked in phase 5).

## 13. Overlays (phase 6)

Overlays are widgets with an `open` property, not actions (**Proposed**): `widget: Menu`, `anchor: save`, `open: "{{ menu_open }}"`, `modal`,
`placement`. Closing (outside press, Escape) writes `open` back when it is a bare writable reference (9.3). Reserved so the property names do
not collide: `open`, `anchor`, `placement`, `modal`, `dismissible`.

## 14. Errors

Every load error is one line plus context, in this shape:

```
Main_View.yaml:14:7: error: Slider: no property 'valu'. Did you mean 'value'? (properties: value, min, max, step, disabled)
    14 |   valu: "{{ volume }}"
       |   ^^^^
```

Categories: syntax (YAML), structure (unknown key, misplaced header key, missing `widget`), property (unknown, wrong type, value not in
`choices`, required missing), expression (syntax, disallowed construct, budget exceeded, unresolved name, not writable), composition (no such
view, no `Slot`, slot name unknown, depth), binding (unbound view needs a ViewModel, contract mismatch). The YAML position is kept by loading
with PyYAML's marks, so an error inside an expression reports the YAML line and the column inside the string. Every message names what is
wrong and what to write instead.

## 15. Compatibility and migration

For **one release (0.5.0)** the loader accepts the 0.4.x syntax, translates it, and **warns with the new form** (once per file). It is
removed in the release after, with clear messages, as the 0.4.5 and 0.4.6 pattern did.

| 0.4.x | 0.5.0 | Notes |
|---|---|---|
| `kind: X`, `component: X`, `view: X`, `include: X` | `widget: X` | `include:` (a YAML splice) becomes a view call; `view: File_View.yaml` becomes `widget: File` |
| `component_of: x` | dropped | stylesheet part addressing is by `name` and `part` |
| `id: x` | `name: x` | only where the id was addressed (a ViewModel, a stylesheet part, a test); the root's `id: root` is dropped |
| `with: {a: 1}` on a call | `a: 1` | properties are plain keys |
| `repeat: "{{ items }}"` | `for: item in items` | and `key:` |
| `when: "{{ x }}"`, `{if: ...}` | `if: x` | |
| `params: [a, b]` first, in `*_Component.yaml` | `params: [a, b]` in `*_View.yaml` | the file is renamed |
| `bindings: {text: "{{ x.get() }}"}` | `text: "{{ x }}"` | `.get()` still works |
| `two_way: text` | a bare reference on a `model` property (9.3) | |
| `text: {content, typography_role, wrap, overflow, text_align}` | `Text` properties `text`, `typography_role`, `wrap`, `overflow`, `text_align` | `text: "Hello"` for the content alone |
| `icon: {name: home}` | `icon: home` | |
| `selected`, `checked`, `disabled`, `value`, `min`, `max`, `step`, `hour`, `minute`, `label`, `x`, `y` (node keys) | properties of the widgets that declare them | |
| `image: ...`, `svg: ...`, `edges: ...` | properties of `Image`, `Svg`, `NodeGraph` | |
| `dock:`, `dock_panel:`, `split_handle:`, `embed:`, `window:` | internal; replaced by `Dock`, `DockPanel` properties and `Window` | the 0.4.4 expanders become widgets |
| `kind: Window` with `title_bar:` | `widget: Window` with `title_bar` as a `node` property | |
| `view: X_View.yaml` + `route: ""` | `widget: X` + `route: ""` | |
| `group: g` | `group: g` on `RadioButton` and `ButtonGroup` | now a property of the widgets that have it |
| `ViewModel(view)` | `ViewModel` with `views = [...]` | section 11 |
| `style: {foreground: ...}` on a container | error | `foreground` is an extra |

**Findings of phase 3** (translator over the 131 files in the repository; each is in the translator's notes):

- `{{ }}` spliced inside an expression (`'{{ screen }}'` in `{{ app.current_screen == '{{ screen }}' }}`) becomes the bare name.
- `navigate.{{ screen }}` (a screen named by a parameter) becomes `navigate_to(screen)`. **Proposed**: the built-in action that makes `navigate.<Screen>` dynamic; phase 5 implements it.
- A bound paint or size (`bindings: {background: ...}`) is a style value: `style: {background: "{{ ... }}"}`.
- `style:` may be the name of a style file (`style: row_Style.yaml`), as today.
- YAML 1.1 reads the key `on` as `true`; the loader keeps a boolean-looking key as written, so `state: {on: false}` works.
- **Not translatable, left for the component pass**: a widget name that is a parameter (`component: "{{ button }}"` in `ButtonGroup`; a `variant` property replaces it), and a call that binds a property its fragment does not declare (`ButtonText` has no `disabled`). The translator reports both and `tests/test_translate.py` names them.

**Findings of phase 4** (composition, tested headless; building real nodes is phase 5):

- **Ids.** An instance id is the parent's id, a dot, the node's `name` or place (`children[2]`), and `[key]` under a `for:`. A view call's id is the callee root's, so parts read `nav.label`. Slot content is the call's child: its segment is its `name`, else `content[i]` (`<slot>[i]` for a named slot), so it cannot collide with the callee's own `children[i]`; a real clash (a slot child named like a callee part) is an error naming the id.
- **Reactivity of names.** A name from a frame (state, loop variable, param) is reactive only when its value is a `Signal` or `Computed`; a ViewModel name is reactive; a built-in function is static. So `for: i in range(3)` expands once and `for: r in rows` needs a `key:`.
- **Read-only names.** Loop variables and params cannot be assigned in a handler (`'r' is not writable`); state and ViewModel Signals can.
- **State.** A node's `state:` is a `Signal` per name; a call's `state:` is visible to the call's arguments and its slot content (both written in the caller's scope). A recomposition (`Composer(previous=...)`) restores a value when the instance id and the name match; the key is `(id, name, call or node)`.
- **A call's own keys** (`style`, `classes`, `a11y`, `interaction`, `window_region`, `route`, `name`, `handlers`) lie over the callee's root; a handler written at the call runs in the caller's scope, the callee's own handlers in the callee's.
- **YAML trap**: `name: no` or `name: yes` reads as a boolean; the error says to quote it.
- A reactive `for:` over a list that is **replaced** is reconciled; a list changed **in place** is not seen (Signals notify on assignment). The ViewModel replaces lists, as `Signal.set` does everywhere.

**Findings of the foundations (level 0 of the build order)**:

- **#210, the accessibility states tre already has.** `a11y:` takes `expanded`, `selected`, `checked`, `value`, `value_min`, `value_max` and `value_step` beside the original five, fixed or bound (everything but `role` and `live` can follow an expression), and `null` clears one (tre holds them unset until a node says; `hidden` is always one or the other). A control kind sets its own `checked`, `selected` and `value`, so `a11y:` refuses them there. What tre lacks (`pressed`, `invalid`, `description`, `controls`, `current`, `value_text`, `busy`) is #232 and #237.

- **#211, text extras.** `max_lines`, `letter_spacing` and (for `Text`) `selectable` are properties; the old builder takes them in `text:` and the text's natural size measures with them. A Text with a fixed `width` and no `height` is now as tall as its lines wrap to (it was one line). MD3's per-role tracking is **not** applied by default (it would change every text's width); a role's `letter_spacing` stays a follow-up to the type scale.

- **#212, alpha on roles and the `full` shape.** A colour ends in `@N%` to scale its alpha (`tokens.resolve_color`, shared by the builder, bound colours and the loader's `color` properties); `corner_radius: full` is `tokens.FULL_RADIUS` (9999), which the engine rounds to half the shorter side. `SHAPES` itself is unchanged, so the recorded tre parity still holds. The reserved items of section 10 (`primary@12%`, `full`) are no longer reserved.

- **#213, focus.** `focus(name)` is a built-in action resolved by the renderer against the instance whose handler is running (`Scope.nearest_instance`, `Instance.view_root`): names are unique in a view and a view does not see into the ones it calls. `on_press` is the pointer-down event, which (unlike `on_click`) leaves the node out of the tab order and out of the button role, so a container can send the focus to its input. `focus_group` is a universal key: one tab stop (`tab_index`), arrow/Home/End movement and type-ahead among the focusable nodes under it, skipping disabled ones and groups nested inside. The text field's box uses it, so a click on its padding focuses the input. What is not here: roving among a grid's rows and columns (`both` moves along the document order), and `Tab`-order changes beyond one stop per group.

- **#214, `transition:` for what tre can animate.** A style field (so rules carry it): a mapping from style fields (or `all`) to a duration or `{duration, easing, bounce}`; `tesserae.spec.transition.plan` turns it into node properties and the builder's `patch` animates a change with `node.animate` (and sets at once when the app is to reduce motion, or the value did not change). The first build never eases. New style fields `scale`, `translate_x`, `translate_y`, `rotation_deg` use the optional-layout mechanism (set only when the style gives them, put back only if they were given before), which is what keeps a Python widget's own rotation from being undone by a re-theme. Layout properties wait for #233. A transition on a state-driven rule works because the composer re-lowers and `View.reconcile` patches; an interrupted change retargets from where it is.

**Findings of the component pass: TextField (#184)**, the first component, which also built what the others use:

- **Shipped views.** `src/tesserae/views/` holds `<Name>_View.yaml` and `<Name>_Stylesheet.yaml` (section 4, step 4). `ViewLibrary` finds a view in the project, then there; a project view of the same name replaces the shipped one **and its shipped rules** (`RuleSheet.without`). Shipped rules are the lowest layer, then the app's.
- **A primitive and a component.** The bare input is the widget `TextInput` (`text`, `placeholder`, `multiline`, `obscured`, `max_length`, `read_only`, `disabled`, type); `TextField` is the Material component built from it. The old builder's `kind: TextField` is the bare input, so the translator writes `widget: TextInput`. `max_length` and `read_only` are enforced by the renderer (the engine's input has neither): an edit that breaks either is put right before any listener that writes the text back hears of it.
- **Events.** `on_key` (a `key_down`) and `on_submit` (Enter, when the target is not a multiline input) are drawn by `ComposedView`; both are in the handler list.
- **Interaction states of a widget, not of a part.** A rule's `state: focused` on a part reads the state of the widget the rule names, so `part: label, state: focused` is the label while the *field* has the focus. Focus events bubble, so a widget is `focused` when anything inside it is; `focus_visible` is the keyboard-only form. `error` and `read_only` join the states that read the widget's own property.
- **Inline beats rules, so defaults live in rules.** The first draft of the field gave its line an inline `height: 1`, which kept the focused rule's `height: 2` from ever applying; a look a state changes belongs in the stylesheet, not inline.
- **Not done** (follow-ups): the label animates by jumping (needs `transition:`); filled's 4dp-top, 0dp-bottom corner (needs per-corner radius); `aria-invalid` and `aria-describedby` (the error is put in the input's name instead; needs the a11y vocabulary of section 12); clicking the padding around the input does not focus it; autocomplete, input masks, IME composition visuals.

**Findings of phase 7** (migration):

- **The old syntax keeps working** by being left alone: the 0.4.x loader, builder and `app.load` are untouched, so "the loader accepts the old syntax" costs nothing and a project moves one view at a time. A file in the old syntax says so once (a log warning) and names the command.
- **Not rewritten: Python.** The tool translates YAML and lists what each ViewModel needs (`views`, no `view` argument, `app.bind`, `app.open_view`). A view with a `<Name>_ViewModel.py` beside it is named after it; a fragment never is.
- **Round trip.** Primitive-only views from the examples (the counter, the four getting-started steps, the window-dock panels) migrate, compose and render the same laid-out and painted tree as the old builder gave. Getting there found that the builder reads a node's `handlers` to make it clickable (role, cursor, state layer), so `lower` carries a placeholder handler per event while the renderer wires the real ones.
- **Shipped fragments.** All 79 fragments and their stylesheets translate and load as views and rules, except `ButtonGroup` (a widget name from a parameter); that is the starting point of the component pass (#115, #118 to #208), which replaces them one by one with widgets that declare their properties, and the examples and tutorials that call them stay on the old path until then.
- **Not yet drawn by a composed view**: `Window`, `TitleBar`, `Dock` and `DockPanel` (the old expansion step gives them bindings and handlers that only a ViewModel-attached `View` wires), an Image `frame`, a ScrollView's `scroll_offset`, `on_key`. They belong to the windows-and-docks work (#114, #105, #106) and the component pass.

**Findings of phase 6** (style):

- **A new module, not a change to `cascade.py`.** The rule shape (`widget`, `variant`, `size`, `shape`, `classes`, `name`, `part`, `state`) is `spec/rules.py`; `cascade.py` keeps the 0.4.x shape (`kind`, `classes`, `id`) for the old builder and the themes. `is_rule_sheet` tells them apart by the keys; one app uses one shape for its stylesheet for now, and a rule-shaped stylesheet reaches composed views only.
- **Specificity** is the tuple (named, number of variant/size/shape/classes matched, has a state, has a widget), then the later rule. A class rule therefore beats a widget rule alone, and `variant` beats `state`.
- **Layers** run lowest first (a widget's shipped looks, then the app's); a later layer wins whatever the specificity. **Inline `style:` beats every rule, for the fields it sets and no others**, and a call-site `style:` lies over the callee's root. The 0.4.x trap (a component's look written *into* its inline style, so no class rule could beat it) is gone because a widget's shipped looks are rules in the lowest layer.
- **Naming a node.** An instance has identities: itself as its widget, the root of a view call as that view, and a named node inside a view as `part:` of it. Slot content belongs to the caller, not to the view it is passed to. The root of a view is the widget, not a part.
- **States.** `hovered`, `focused` and `pressed` are Signals made when a rule or an expression first asks (`focused` is true while the widget or anything inside it has the focus, and `focus_visible` while that focus came from the keyboard); the renderer wires pointer and focus events to the ones that exist. `disabled`, `selected`, `checked` and `expanded` read the widget's own property of that name. The three are readable names (`{{ 'hover' if hovered else 'rest' }}`, for the nearest widget with `interaction`) and read-only.
- **`foreground` is an extra** of `Text`, `Link`, `TextField`, `Icon` and `Svg` (`widgets.style_fields_of`); anywhere else it is an error naming who accepts it. The 131 repository files all still load.
- **Rule values** may be expressions, read in the widget's own names (a view's params, a built-in's properties), and follow them.
- **Deferred.** `transition:`, role-with-alpha colours, per-corner radius and the `full` shape token stay reserved. Section 13's overlays (`open`, `anchor`, `placement`, `modal`, `dismissible` on `Menu`, `Dialog` and the rest) need those widgets, so they are the component pass's; the property names stay reserved.

**Findings of phase 5** (binding and rendering):

- **Rendering reuses the builder.** `spec/lower.py` writes a composition as the 0.4.x node mappings at the values the instances hold now; `ComposedView` (a `View`) builds that, then an `Effect` lowers again whenever a value any property reads changes and `View.reconcile` patches the live nodes by id. Structure changes (`for:`, `if:`) re-run the effect so it follows the new instances. So the cascade, controls, interaction and themes are the tested code; only what feeds them is new.
- **`views` is two things.** On the class it lists the names a ViewModel serves; on an instance `self.views` is the mapping from name to `ViewHandle` (the base class replaces it when the first view opens). `declared_views(cls)` reads the class form.
- **`ViewModel(view=None)`**: the 0.4.x `ViewModel(view)` still attaches; with no argument the ViewModel is attached by `app.bind`. `on_attached(handle)` and `on_detached(handle)` are called per view.
- **Swapping** (**Decided**): `self.show(new, old)`. Both views are visible by default, so the second argument says what `new` replaces (a name or a list of names); the `show` docstring explains it. A handle has `.show()` and `.hide()`. Declared groups remain reserved.
- **Two-way.** A `model` property given a bare reference to a writable Signal or state writes the user's edit back. A model *param* given a bare Signal passes the Signal itself to the callee, so a view built around a `Checkbox` can be two-way with its caller's Signal. A loop variable or a computed expression is one-way.
- **Contract.** `check_view(doc, viewmodel)` reports, as `file:line:column`, every name a view reads and every action it names that the ViewModel lacks, and each `expects:` entry (`int float str bool list dict any handler`) that is missing or of another type. `App.check()` runs it for the opened views and warns about a ViewModel that serves a name no view has.
- **Not yet** (phase 7 or the component pass): discovering a `*_ViewModel.py` by its `views` in `app.load`, `app.unbind`, hot reload of a new-syntax file, `style:` as a file name in a composed view, `on_key` handlers, an Image `frame`, a ScrollView `scroll_offset`. A property the renderer cannot draw is an error naming it. The TextField declaration lost `placeholder`, `multiline` and `obscured`, which the builder never supported.

`tesserae migrate-yaml [path]` rewrites a project in place (a report of what it could not translate) and is tested against all 45 views, the
79 fragments, the examples and the tutorials in the repository.

## 16. The built-in widget list (provisional)

Outcome of the 91 component issues' consolidation proposals (#118 to #208, now 0.5.1). **Provisional**: each is settled in the component pass;
this list fixes only the names the language and the registry are designed around.

| Widget | Replaces | Key properties (beyond the universal keys) |
|---|---|---|
| `Container`, `Rect`, `ScrollView`, `Slot` | the same | layout in `style`; `Slot` placeholder |
| `Text`, `Link` | `Text`, `Link` | `text`, `typography_role`, `wrap`, `overflow`, `text_align`; `Link`: `href`, `visited` |
| `Icon`, `Svg`, `Image`, `Video` | the same | `icon` / `source` / `fit` / `label` |
| `Button` | the 5 buttons | `variant`, `size`, `shape`, `label`, `icon`, `trailing_icon`, `toggle`, `selected`, `disabled`, `loading` |
| `ButtonGroup` | `ButtonGroup`, segmented buttons | `selection` (`none`, `single`, `multiple`), `connected`, `orientation`, `selected` (model) |
| `SplitButton` | the 5 split buttons | `variant`, `label`, a `Menu` child, `open` |
| `IconButton` | the 4 icon buttons | `variant`, `size`, `shape`, `icon`, `selected_icon`, `toggle`, `selected`, `label` |
| `Fab` | 4 FABs and 4 extended FABs | `variant`, `size`, `icon`, `label`, `collapsed` |
| `Badge` | 2 badges | `label`, `max`, `anchor` |
| `Progress` | linear, circular, loading | `shape`, `value`, `indeterminate`, `wavy`, `size` |
| `Snackbar`, `Tooltip`, `Dialog`, `Menu`, `Sheet` | the overlays | `open`, `anchor`, `placement`, `modal`; `Sheet`: `side`, `detached`; `Tooltip`: `variant` |
| `Card` | 3 cards | `variant`, `selected`, `actionable` |
| `Divider` | `Divider` | `orientation`, `inset` |
| `List`, `ListItem` | `ListItem` and the menu, drawer, tree and accordion rows | `lines`, `leading`, `trailing`, `selected`, `expanded`, `depth` |
| `Disclosure` | `AccordionHeader` | `title`, `expanded`, `exclusive_group` |
| `Tree`, `TreeItem` | `TreeNodeBranch`, `TreeNodeLeaf` | data-driven; `expanded`, `selected` |
| `Navigation`, `NavigationItem` | rail, rail items, screens variants, drawer, drawer items | `mode`, `collapsed`, `selected` (model), `screen`, `badge`, `icon`, `label` |
| `AppBar` | `TopAppBar`, `TitleBar` | `size`, `window` (is the window's title bar), `leading`, `trailing` slots |
| `Tabs`, `Tab` | `Tabs`, `TabsItem` | `selected` (model), `scrollable`, `secondary` |
| `Search`, `Toolbar` | `SearchBar`, `SearchView`, 2 toolbars | `query` (model), `open`; `variant`, `vibrant`, `orientation` |
| `Toggle` | `Checkbox`, `RadioButton`, `Switch` | `type`, `checked` or `selected` (model), `indeterminate`, `label`, `group` |
| `Slider`, `NumberField`, `TextField` | the same and `SpinBox` | `value` (model), `min`, `max`, `step`, `range`, `ticks`; `variant`, `label`, `supporting`, `error`, `leading`, `trailing`, `multiline`, `obscured` |
| `Chip`, `ChipGroup` | the 5 chips | `variant`, `selected` (model), `icon`, `removable`, `elevated`; `selection` |
| `DatePicker`, `TimePicker`, `PeriodSelector` | day fragments, dial, AM/PM, time input | `value` (model), `mode`, `min`, `max`, `range` |
| `Carousel`, `Pagination`, `StatusBar`, `NodeGraph`, `Split` | the same and `Splitter` | as today, plus slots |
| `Window`, `Dock`, `DockPanel` | the 0.4.4 kinds | as today, as properties |

## 17. Implementation map and tests

| Phase | New or changed modules | Tests |
|---|---|---|
| 2 expression language | `src/tesserae/expr.py` (parse, check, evaluate, classify); `binding.py` is now a facade over it | the section 8 grammar table row by row; the sandbox corpus and fuzzer (8.6); every limit; static and reactive classification; Signals as values; error positions |
| 3 node model | `src/tesserae/spec/widgets.py` (registry, `Property`, `@widget`, `decl_from_params`, JSON schema), `spec/builtin_widgets.py` (the 25 built-in declarations), `spec/nodes.py` (`parse_view`: nodes, ids, positions, `LoadError`), `spec/translate.py` (old to new), `tools/generate_widget_schema.py` | one test per key in section 2; unknown-property errors with suggestions; the translator over every file in the repository (128 of 131 load, 3 known gaps) |
| 4 composition | `src/tesserae/spec/compose.py` (`Composer`, `Composition`, `Instance`, `Scope`: params, the caller's scope, `Slot`, `for`, `if`, `state`, ids, disposal) | scope rules; slot placement and errors; reactive `for:` reconciliation (add, remove, reorder, update in place, 10 000 rows); state per row and across a recomposition; the call's keys over the callee's root; every subscription released on dispose; mutation-checked |
| 5 binding | `src/tesserae/viewmodel.py` (`Bindings`, `ViewHandle`, `open_view`, `check_view`), `spec/lower.py` (instances to the builder's spec), `composed.py` (`ComposedView`, `open_composed`, built-in actions), `App.bind`/`open_view`/`check`, `ViewModel(view=None)` with `views`, `show`, `on_attached`, `on_detached` | the pie-and-list case (two views, one instance, one Signal) headless and on screen; the three ways to bind; unbound views; swap; the contract and `expects:`; lowering of every widget shape; handlers, two-way edits, `for:` and `if:` reaching real nodes; mutation-checked |
| 6 style | `src/tesserae/spec/rules.py` (`RuleSheet`, `Rule`, `Identity`, the specificity order, `is_rule_sheet`, `load_rule_sheet`), `widgets.style_fields_of` (per-widget extras), rule resolution and the `hovered`/`focused`/`pressed` Signals in `spec/compose.py`, state wiring in `composed.py`; `spec/cascade.py` stays for the 0.4.x shape | the shape and its errors; the specificity table; layers; inline over rules for the fields it sets; variant, part and state selectors; rule values that read params; hover and press on screen; mutation-checked |
| 7 migration | `src/tesserae/migrate.py` (`migrate_project`, `Report`), `tesserae migrate-yaml` in `cli.py`, `translate.translate_rules` (stylesheets), the once-per-file notice in `spec/load.py`, `docs/guide/view-language.md`, `docs/migration.md` | dry run, write, all-or-nothing and `--force`; renames, header comments, bind key from the ViewModel, stylesheets to rules; the shipped fragments and their sheets (155 files, one known gap); migrated primitive-only example views draw the same tree as the old ones; every YAML block in the guide loads; mutation-checked |

**Risks.** (1) A reactive `for:` over a list that is replaced often: reconciliation by `key` must be linear and tested at 10 000 rows against
`tre`'s `virtual_list`. (2) The step budget makes a slow binding fail rather than hang; the default needs measuring on the real built-in
widgets. (3) The migration of 79 fragments is large: the translator, with its round-trip test, is the safety net. (4) Names: `widget`,
`Slot`, `Disclosure`, `Toggle`, `Navigation`, `AppBar` are provisional.

## 18. Questions for the user

All **Proposed** above; each stands unless the user changes it.

1. **Dict attribute access** (`item.title` for `item['title']`, 8.4): yes, it reads naturally for JSON-like loop data.
2. **`route:` on a view call** (section 2) rather than a `Screen` widget: yes, unchanged from 0.4.4.
3. **Two-way by bare reference** (9.3) rather than an explicit marker: yes.
4. **`on_key`** added (9.1): yes.
5. **`classes:` kept** alongside `variant:` for stylesheet targeting (section 2): yes.
6. **The names** `Slot`, `Disclosure`, `Toggle`, `Navigation`, `AppBar`, `Split` (section 16): yours to change.
- **#215, `Canvas`.** A built-in widget whose `draw:` is a list of rect/circle/path command mappings (`tesserae.spec.canvas.plan` checks and resolves colours; `painter` makes tre's `draw` callback). It lowers to a `canvas` node key; the builder makes a tre `canvas` and, on a patch, sets the new `draw` callback and calls `redraw()` (setting `draw` alone does not repaint). `View._props_equal` compares `canvas`, or a changed drawing would be skipped. Errors name the widget and `draw[i]`. Gradients and hit-test shapes are not in the command set yet.
- **#216, icons.** `Icon` takes `icon:` or `path:` (+ optional `view_box:`), exactly one of name and path, checked by the builder. The icon set is `icons.ICONS`, the built-in names merged over `icon_data/material_symbols.json`, which `tools/import_material_symbols.py` writes from a folder of Google's SVGs (one `<path>`, view box `0 -960 960 960`). Fetching the Symbols is a download the project owner approves, so the data file is not in the repo yet; names beyond the 18 arrive when it is.
- **#217, timers.** `tesserae.timers.Timers(window)`: a timer is an animation of a private detached box (the trick `overlays._Timer` used), so it runs with the frame loop and `window.advance` drives it in tests; `every` re-arms before it calls `fn`, so `fn` can cancel it. In handlers `after`/`every`/`cancel` are built-in actions with scope (`ComposedView.timers`, `timer_action`, `timer_name`); the action argument is text compiled once per view, a literal one is also compiled at load (`expr.timer_handlers`). Names are keyed by the Scope that wrote them (a weak map to a number), not by the widget: a handler's scope is the view's or the `for:` iteration's, so that is what 'local' means for them. A widget that has gone (`Instance.disposed`) does not run its timer. Times are frame-quantized, and `every` drifts by up to a frame per round.
- **#218, scroll state.** `scroll_offset` lowers to the node key `scroll: {offset}` (only when the caller gave it, so an unbound ScrollView keeps the user's position through a re-sync) and the builder sets the tre scroll view's `scroll_offset`. `at_top`, `at_end`, `scroll_direction` are `model` outputs the renderer writes (`ComposedView._wire_scroll`), from tre's `scroll` event (`old_value`/`new_value`) and the layout of the scroll view and its content box. tre clamps an offset to 0 until the content has a size (and reading a layout property is what lays it out), and has no layout-changed event, so `_wire_scroll` applies the asked-for offset and first reports on a `Timers` tick one frame after each wiring, after reading the content's layout; `at_end` is false before there is a layout, and after a content change it is correct from the next scroll or re-sync. Vertical only. The direction is kept across re-wiring because every write to a Signal re-syncs the view.
- **#219, pointer capture and cursor in handlers.** `on_move`/`on_release` are tre's `pointer_move`/`pointer_up` (with `on_press`, `_KEY_EVENTS`). `capture()`, `release()` and `cursor(name)` are built-in actions that need to know which widget's handler is running, which the Scope does not (a handler's scope is the view's or the `for:` iteration's): `ComposedView` keeps a stack of firing instances (`_firing`, pushed around `inst.fire`) and `firing_node` reads the top, so a timer's action calling them is an error. `cursor` is tre's `cursor` node property (its names are tre's); the next patch that changes the node's style puts the style's cursor back. A handler's error is raised as an `ExprError` with the view position, and tre logs it rather than propagating it out of the event.
- **#220, per-corner `corner_radius`.** tre already took a 4-tuple; `build._corner_radius` resolves the style value (a list of four, or a mapping where edges set two corners first and named corners override, unnamed corners square) and collapses four equal radii to one float so the common case is unchanged. `interaction.py` already handled a tuple radius for the state layer and ring, and `node.animate` takes a tuple, so `transition:` eases between shapes. The `components:` theme entries are still a single radius.
- **#221, windows in composed views.** Two gaps, found by building a Window/TitleBar/Dock view with `open_view` (the handlers and the Dock already worked): the title bar's expanded `bindings` (`{{ app.maximized.get() ... }}`, in the 0.4.x grammar, over a ViewModel) were only wired when a ViewModel attached, which a composed view never has, so `View._wire_actions` now also wires those whose names are only `app` (against a stand-in with just `app`; others still wait for a ViewModel); and `open_view` did not adopt a `Window` root as the app's frame (title, borderless, minimum sizes, one window per app), so it now does. Routed screens (`route:`) in composed views are not part of this and still need `View._embedded`, which a composed view does not have.
- **#222, input masks.** `spec/mask.py` (`Mask.apply`): the text is read left to right, a slot takes the next character it accepts, a literal is typed-and-kept or inserted only when a later slot has input (so a trailing literal is never forced back by backspace, and `apply` is idempotent on its own output). `mask` is a new property type (checked at load) and a renderer-only property of `TextInput`; `ComposedView._enforce_input` listens to the engine's `change` after the max_length/read_only listener and sets the fitted text back before the model write-back reads it. A value a ViewModel sets is not masked, and tre has no caret control (#234), so where the caret lands after a rewrite is tre's (not checked with a person typing). The shipped TextField takes `mask`.
- **#223, clipboard.** `copy`/`paste` are built-in actions over tre's `write_clipboard`/`read_clipboard`. A handler's action call may be used as a value (`pasted = paste()`), which the evaluator already allowed in handler mode, so no language change was needed. `copy` takes text or a number and anything else is an error naming the call; `paste` turns `None` (no text, or no clipboard) into `''`.
- **#224, `open_url`.** `tesserae.urls.open_url(url)` over `webbrowser.open`, with `check_url` refusing anything but http(s) with a host, `mailto:` and `tel:`, and any link with whitespace or control characters. The allow-list is deliberate: view text and ViewModel values can come from users or the network, and an opener will happily run `file:` or an app's custom scheme. The action returns the opener's result as a bool.
- **#225, a request to tre (shape masks).** Not repo work; drafted as `design/tre-requests/shape-masks.md`. No tre node kind has `mask`/`clip_path`/`clip_shape`, but (read from `Window.snapshot` pixels, relative to the node's bounding box) an `image` clips to its own `corner_radius` (a 4-tuple, or a radius past the node's size for a circle) and a `clip_children` box clips children to its rounded shape, so round and rounded images need no mask; the request is only for non-rounded-rectangle shapes. A first draft of this note said the opposite, from a test that sampled pixels at the wrong place.
- **#152, Divider.** A shipped view that is just a `Container` with `a11y: {role: separator}` (hidden until tre 0.5.6 gave a `separator` role: the a11y gate, #232) and a stylesheet: the colour, and thickness and insets as rule expressions over the view's params (`orientation`, `thickness`), with `variant` selecting the inset rules. Two things learned: `margin` takes a mapping (`{left: 16}`), so an inset is an expression that builds one; and `align_self` is a nine-position alignment in this language, not flex's `stretch` (an unset cross axis already stretches). The 0.4.x `Divider` fragment stays until the fragments are retired, and the component page documents both forms.
- **#196, Image.** The widget existed; this adds `alt` (lowered to an `img` role and label, or `hidden` when there is none and no handlers; an explicit `a11y:` beats it) and `fit` as an enum. Found: `extract_images` strips `src` from the spec (the pixels travel as frames), so `View._props_equal` could not see a changed `src` and a Signal-driven picture never updated; `reconcile` now notes which ids got different frames (`_new_frames`) and patches those. Shape is `corner_radius` (see #225: the engine clips an image to it, per corner and as a circle). Not done from the issue's list: async/URL loading, blur-up, animated formats, lazy loading in lists, a `placeholder`; the first three wait on an async image source the engine does not have, and a missing file is a load error naming the widget and file.
- **#197, Svg.** The widget already drew files and inline documents and tinted them by `foreground`; added `alt` (as Image) and a `one_of` group on the widget declaration so `src`/`content` is checked at load with a position, not at build. Not done: an icon-set loader with the Material Symbols axes (weight, fill, grade, optical size) -- that is #216's data and needs the download decision -- and animated SVG, which the engine does not expose.
- **#216, MDI icons.** The user supplied the Iconify `mdi` collection (7447 icons, 24 x 24, one `<path>` each, Apache-2.0). `tools/import_mdi.py` writes a curated 147 (or `--names`, or `--all` at ~2 MB) to `icon_data/mdi.json` as snake_case; `icons.ICONS` is built-in over Symbols-importer over MDI, and `icons.icon_view_box(name)` says which box a name is drawn in (MDI's differs from Material Symbols', so paths are not rescaled). MDI is the Pictogrammers set, not Google's Material Symbols: the names differ (`arrow-left`, not `arrow_back`). `icon_data/NOTICE.md` carries the licence note.
- **#226, elevation that moves.** Needed no code: #214's `transition:` and #213's interaction states already compose, because tre eases a `shadows` list (even from none) and a retargeted animation continues from the current value. Written down and tested: hover, press, leave, release, interruption, token names, reduced motion, and a view-computed drag lift. The one trap: a node's inline `elevation` beats the state rules, so the base level has to be in a rule (documented).
- **#227, the Overlay widget.** A builder kind of two nodes like ScrollView: a 0 x 0 absolute placeholder where it is written and the layer box, which holds the children and is never attached to the tree (`_create` skips `add_child`); `ComposedView._wire_overlays` shows it with `window.show_layer(anchor, placement, modal, dismissible)` and hides it with `hide_layer` (tre returns focus). Modal: the layer is the full-window scrim, so tre's 'outside press' never fires for it and a `pointer_down` whose target is the layer dismisses instead; its size is set by the renderer on show, on resize and after every sync (a patch puts the layer's own size back). A user dismissal writes `open` false via the model reference, or, for an `open` that is not a Signal, is remembered until `open` goes false. An overlay that leaves the view (an `if:`) is hidden. Un-anchored non-modal layers sit at their own x/y. Lesson for mutation testing: an edit and its restore inside one second with the same file size leave a stale `.pyc`, so mutants must run with an isolated `PYTHONPYCACHEPREFIX`.
- **#228, VirtualList: windowing in the composer, not tre's `virtual_list`.** The issue says 'backed by tre's `virtual_list`'. tre's list asks for a node per index through a `materialize` callback and drops them itself, which cannot work with this design: the renderer lowers the whole instance tree and reconciles it, and every row is an `Instance` with expressions, handlers and rules. So the window is the composer's: a `VirtualList` lowers to a `ScrollView` whose content box is `count * item_height` tall, its one `for:` realizes only the items in `[first, last]` (`compose.Virtual`, `_For` in virtual mode; keys computed for the window only), and each row gets `position: absolute` at `index * item_height` (`Instance.virtual_index`, a Signal so a row that moves is re-placed). The renderer sets the window from the scroll event (`_wire_scroll`: offset and viewport height, with overscan), on the first frame, and on a change of data. A window change that arrives while the view is being patched (tre fires `scroll` when the content height changes) is deferred a frame, because it re-entered the reconcile. Equal fixed heights only (tre's `size_hint` is not used); a row's `state:` is not kept once it has left the window. 10 000 rows: opens in about 70 ms with 20 specs, about 4 ms per scroll step. Revisit tre's own list only if variable heights are needed and tre exposes a way to hand it nodes the framework already owns.
- **#230, window size classes.** `App.window_width/height` (Computed over one `(w, h)` Signal updated on the window's `resize`) and `width_class/height_class` using `tokens.width_class/height_class` (MD3's 600/840/1200/1600 and 480/900 breakpoints). Found: the reserved name `app` worked only where a ViewModel had been attached the 0.4.x way (`ViewModel.app` is found through `_view`), so no new-style view could read it, including the title-bar bindings; `Scope.lookup` now falls back to the window's app (`builtin_actions(..., window).app`) and `Scope.is_reactive('app')` is true, so `if: app.width_class == 'compact'` re-evaluates on resize. A ViewModel's own `app` still wins.
- **#231, screen transitions.** `screen_transition.play(window, outgoing, incoming, kind, forward, origin, reveal, hide_outgoing)` over `node.animate` on opacity, translate and scale (MD3 durations 90/210 ms and its emphasized curves). Both screens are laid `position: absolute` while it plays and restored (position, x, y, transforms) when it ends, so a screen comes back clean next time; the same code serves the app's own screens (add/remove the root) and a window view's routed screens (visible on/off), with `reveal`/`hide_outgoing` callbacks. `App._arrivals` remembers the transition and origin each history entry was reached with, so `back()` plays the reverse of how the screen it leaves arrived and `forward()` repeats it. `show()` is a jump and never animates. A new navigation finishes the one playing. Layout-property animation is not needed (everything is a transform), so this did not wait for #233.
- **#232 to #235, requests to tre.** Not repo work; each drafted in `design/tre-requests/` (`accessibility-states.md`, `layout-animation.md`, `text-input.md`, `timers.md`) from what a probe of tre 0.5.4 shows: no `pressed`/`invalid`/`description`/`describedby`/`controls`/`current`/`value_now`/`value_text`/`busy` node properties; `animate` refuses width, height, x, y, padding, margin, gap, flex and font_size; `text_input` has no `max_length`, `read_only`, `input_mode`, `mask`, `submit` or composition; no timer API. None is sent.
- **#195, Text.** Most of the issue's list was already done by #211 (`max_lines`, `letter_spacing`, `selectable`) and the expression language (formatting). Added: `heading` (lowered to `role: heading` + `level`, an explicit `a11y:` wins) and per-role `tracking` on `TypeStyle`, settable from a theme (`typography: {role: {tracking: n}}`, also in the schema). **MD3's tracking values are not the default**: switching them on changed 13 of the recorded tre parity trees (tre draws the roles with none), so they are `tokens.MD3_TRACKING` for a theme to opt into; making them the default would mean re-recording parity with a documented exception. Not done: variable fonts and text shadow (tre has neither), hyphenation.
- **#203, Splitter.** A built-in widget that lowers to a grid (`grid_template_columns: "0.5fr 16 0.5fr"`) of the first pane, the handle and the second pane, because the layout language has no flex ratios (`flex_grow` is refused; `flex: fill` shares equally) and `fr` tracks give exactly `position` of what the handle leaves. The handle is a lowered-only node (`{id}.handle`) with a placeholder click handler, which is what makes the builder give it a Tab stop, and `a11y: slider`; `ComposedView._wire_splitters` wires its pointer capture, drag (position from `window_x/y` against the first pane), keys, a11y actions and a time-based double click. A literal `position` is held in a Signal on the instance so the handle can move it; an expression is read-only; a bound Signal is written. Min sizes are the panes' `min_width`/`min_height` (grid tracks respect them) and the drag clamps to them. The dock's split handle is a second implementation of the same idea and was not unified here.
- **#236, Image masks.** Nothing new to build: #225's correction (tre clips an image to its `corner_radius`, per corner and past the node's size) means the rounded and circular masks were done by #196 and #220. Added tests for a pill on a non-square picture and a mask given by a rule, and a line in the images page. The non-rounded-rectangle masks still wait for tre (`design/tre-requests/shape-masks.md`).
- **#229, more than one window: answered by the spike, blocked on tre.** Run by the user on Linux/Wayland: `App.add_window` while the app runs raises `RuntimeError: Already borrowed` (from a key handler and from `call_soon`), no second window draws, and `Window.set` has no parent/owner/modal/position. Request drafted in `design/tre-requests/second-window.md`. No Tesserae API was built on a guess; an Overlay is the multi-surface answer meanwhile.
- **Typing effects (a wish, in the Backlog).** Flash or fade-in on typed text and an animated caret. Probe of tre 0.5.4: a `text_input` takes `shader`, `blend_mode` and animates `opacity`, `fill`, `scale`, `translate_x`, `blur`, so whole-input effects are possible now; the caret has only a non-animatable `caret_color`, and there is no caret or glyph geometry, so per-character and caret effects wait on tre. Draft request: `design/tre-requests/text-input-effects.md` (not sent).
- **#237, the full accessibility vocabulary (partly gated on tre#160).** The language and the Python `a11y` helpers accept, check and bind `pressed`, `invalid`, `description`, `current`, `value_now`, `value_text`, `busy` (`a11y.EXTRAS`) and the relations `describedby`/`controls` (`a11y.RELATIONS`: node names, lowered to ids, resolved to nodes by the view). tre 0.5.4 has none of those properties, so they never go in the builder's one `set` (which would raise for the whole node): `View._apply_a11y_extras` applies each separately through `a11y.apply_extras`, which skips a property tre says it does not know and warns once by name (any other error still raises), and clears one a node stops giving. Written against a recording node that takes them, since the real engine cannot yet; the first tre that has them should be checked for the value shapes (`pressed: 'mixed'`, relations as nodes) the request proposed. The shipped TextField sets `invalid` and `description` and keeps the error in the label until then. Relations need the view's root: a view that is open has no owner, so lowering climbs to the top of the tree.
- **#238, `tooltip:` on every node.** A universal key (`Node.tooltip`: `text`/`title`/`delay`, each possibly a template; a view call's goes to the callee's root). `ComposedView._wire_tooltips` listens on the node's outer box: `pointer_enter` starts a `Timers` delay, `pointer_leave`/`pointer_down`/`unfocus` hide, `focus` with `focus_visible` shows at once. The layer is a plain tre box shown with `show_layer(anchor, below, modal=False, dismissible=False)`: `dismissible=True` would make tre consume the next outside press, so a click on another control while a tooltip showed would be lost (tested), and Escape is a root `key_down` listener while it shows. `hit_testable=False`, so it never takes the pointer. Plain = inverse surface, 4 px; rich (a title) = surface container, 12 px, elevation 2. Not done: actions in a rich tooltip (needs the Button; #147), and the fade/scale in (the Tooltip component).
- **#239, `transition:` for layout, built without waiting for tre#161.** The issue is gated on tre, but the need (drawer and rail collapse, tab indicator, accordion) is real, so `spec/layout_steps.py` eases layout by hand and `patch` tries `node.animate` first, falling back only on tre's `isn't animatable` (any other error still raises): a tre that can animate layout is used with no change here. A step is a private detached box whose `stroke_width` animates 0 to 1 linearly (the engine's clock, so `window.advance` drives tests and reduced motion is respected at the planning stage) and a `Timers.every(1)` tick reads it, applies the curve (`curve`: CSS cubic bezier by bisection; a spring is the emphasized-decelerate curve) and sets the property. Numbers only: `auto`/percentages are set at once. A new change cancels the old step and starts from the current value. `padding` and `margin` are their four sides; `all` excludes layout. Cost: a layout pass per frame per animating property, no cheaper than tre would be but not worse. A dropped layout-field cannot be animated back to `auto`.
- **#240, a request to tre (horizontal scrolling and scroll snap).** Not repo work; drafted as `design/tre-requests/scroll-snap.md`. **CORRECTED:** the probe was wrong, because it never set `orientation`. A tre `scroll_view` with `orientation="horizontal"` scrolls sideways (offset, wheel `delta_x` and `animate('scroll_offset')` all work on 0.5.6), so the Carousel (#199) and a scrolling Tabs bar need Tesserae to expose it, not tre. Sent as mindderivative/tre#166; tre keeps the snap part (`scroll_snap`, `snap_align`, a `virtual_list` offset) for 0.5.6.
- **#141 and #142, Badge.** One shipped view for both fragments (`value` empty = the 6 px dot): the mark is a Container with a label Text; anchored, it is absolutely positioned at `x: 100%` with a `translate_x` (-4 for a dot, -12 for a pill, y -4 for a pill) over a wrapper whose only flow child is the host (a `Slot` in a Container, since a Slot takes no `if:`). Pill width is `8 + 6 * characters`, at least 16, because there is no fit-to-text width for a pill in this layout language. `max` is a reserved name (a built-in function), so the cap is `limit`. Hidden from a screen reader; the host's label should carry the count, which the component cannot do for it. Hosts (rail items, tabs, icon buttons) get `anchored` when those components are built.
- **#174, Link.** Added to the built-in widget: `href`, `visited` (model; the rules gain `state: visited`), `disabled`, `underline`, plus a shipped `Link_Stylesheet.yaml` (primary; `secondary` when visited, since MD3 has no visited colour and `tertiary` is not a role here; dimmed when disabled) and a `body_medium` default so a Link needs no font. `ComposedView._wire_links`: `click` calls `urls.open_url` (a refused link is logged, not raised, as an event handler's error would only be logged), and the underline is `spans` on the Link's text (tre has no underline property; a span is the only way), set from pointer-over and keyboard focus (`focus_visible` only, so a mouse click's focus does not underline) and re-applied after every sync because a patch rewrites `spans`. Span offsets are UTF-8 bytes. An external link does not yet say 'opens in a browser' to a screen reader (that needs `description`, #237, which tre must take first).
- **#143, #144, #145, Progress.** The controls already existed; what was missing in the language: **indeterminate was unreachable** (the builder turned a missing `value` into 0.0, so only Python could make a wait with no end). Lowering now says `value: None` when a progress widget is given none, and `_progress_value` reads presence, so the 0.4.x syntax (no `value` key) is still a bar at 0. Patching a progress control's value had never run (`control.disabled` does not exist on an indicator): fixed. Added `track` (a role), linear `buffer` (a second lighter bar, a Signal on the control) and `stop_indicator`, `label`, and `busy`/`value_text` through the tolerant a11y setter. They are opt-in because the recorded tre trees draw the old look (a `surface_container_highest` track, no stop dot). **Not built:** MD3 Expressive wavy shapes, the two-bar indeterminate sweep (one bar sweeps), the contained loading indicator, thicker sizes.
- **#175, #176, #177, Checkbox, RadioButton, Switch.** The controls existed. Added: Checkbox `checked: null` (tri-state: `Signal(None)`, a dash path, a click turns it on; tre takes `checked=None`), `error` on Checkbox and RadioButton (the `error` role for outline, fill and state layer), Switch `icons` (a check/cross `path` on the handle, off handle as large as on), and `label` on all three: lowered to a row `{id}.field` of the control (still `{id}`) and a Text `{id}.label`, with `ComposedView._wire_fields` forwarding a press on the row to the control (focus, then `_activate`; the control's own press is `handled`, so it never reaches the row). The control colour is `style.foreground` now (the 0.4.x fragments' `background` still works). **Latent bug fixed:** a patch reset a control's own a11y states (`checked`, `selected`, `value`...) to None through `_A11Y_RESET`, so any re-sync erased what a screen reader was told; a control now keeps its own. A chosen value for a radio group is `selected: size == 'm'` + `on_change: size = 'm'` rather than a new group widget. Not done: radio `radiogroup` role/label (tre has no such role), the handle's spring slide (MD3 Expressive), and `on_error` vs `on_primary` for the check are the same white in the baseline so the tests cannot tell them apart.
- **#178, Slider.** The control had min/max/step but the builder passed none of them (only `value`): now `min`, `max`, `step`, `ticks` (a mark per step, up to 100), `value_indicator` (a bubble drawn above the handle, shown while dragged or on keyboard focus: `focus_visible` only), `label`, and `foreground` for the colour. A new control signal `Slider.on_input` fires on every user change while a drag is going (`on_change` stays the end of a drag and each key); the language event is `on_input`, and a bound `value` is written on input as well as on change, so a volume follows the pointer. **Order fix:** `_wire_instances` now writes a bound model before running the node's handlers, so `on_input: "log = volume"` sees the new value (the other order made a handler lag one step). **Not built, filed in the Backlog:** the range (two handles) slider, vertical, inset icons, Expressive sizes.
- **#193, SegmentedButton.** Written entirely in the view language as a shipped view, with no renderer code: a `for:` over `options` (key `o['value']`), a `focus_group: horizontal` for the roving tab stop and arrows, handlers that assign the `selected` model param (single: `selected = o['value']`; multiple: toggle in a list comprehension), `on_focus_enter` choosing the focused segment so an arrow moves *and* chooses (single only), `interaction: true` for the state layer, icons (`check` replacing the segment's own when chosen), and the pill from `corner_radius: full` + `clip_children`. What it needed from the language: an `a11y: role` worked out from a param (radio versus checkbox by `multiple`). A role still cannot change while a view is open (an earlier decision, kept: `role` is not bindable), so the parser accepts an expression for it and composing refuses one that is reactive; and a roving group that starts on the item that is `checked`/`selected` (it started on the first). The segments' colours are in the view (inline) because a stylesheet state reads the *widget's* property, not the segment's; so restyling means replacing the view. Not built: vertical, overflow for many segments, a `radiogroup` role (tre has none; the root is `group`).
- **#166 #167, Tabs.** A second shipped view, with no renderer code: a `focus_group: horizontal` bar of `for:` tabs (`role: tab`, `a11y selected`, `on_focus_enter` choosing the focused tab), a `Badge` anchored on an icon, and the indicator as an absolutely placed node whose `x` and `width` are worked out from `selected` and eased by `transition` (the layout-transition fallback, #239). The panels are plain `if:` nodes on `selected`. Needed from the language: nothing new. Not built yet: a scrolling bar (tre 0.5.6 scrolls a `scroll_view` sideways with `orientation="horizontal"`; snap is tre#166), tab panels as a component (`tabpanel`/`controls` relation), vertical tabs.
- **ScrollView orientation.** `orientation: vertical|horizontal` on `ScrollView`, passed to tre's `scroll_view`; a horizontal content box fills the height and runs along x. The scroll outputs measure along the axis. Snap points wait on tre#166.
- **#118 to #122, Button.** One shipped view with a stylesheet of rules keyed by `variant`, `size`, `shape` and `state` (hovered, pressed, selected), replacing five fragments that could not branch on a name. What it needed from the language: `disabled` declared on `Container` and `Rect` (the View already held it for any node), and nothing else; the call site's `handlers:` run alongside the view's own root handler (the toggle flip). Rule expressions read size tables as dict literals. The shape swap on a toggle and the press morph are `state:` rules that change `corner_radius`, eased by `transition`. Not built: the 12% container of a disabled filled button, a ripple/state layer shader (step 48), split buttons.
- **#147, Tooltip.** The plain and rich tooltips already came with `tooltip:` (#238); this adds `placement`, up to two `actions` (each label and handler, run in the scope they were written in) and a rich tooltip the pointer can enter (a 150 ms grace after leaving the node, cancelled by arriving on the card), plus `long_press`. Not built: keyboard reach to the actions.
- **#151, Dialog.** A shipped view whose root is a modal `Overlay`: `open` and `result` are model params written from the action handlers (`result = a['value']; open = False`; names in expressions are Python's, so `False`), the content scrolls in a `ScrollView`, and `at_top` bound to a local `state:` name shows the divider once it has scrolled. What it needed from the language: a `ScrollView` with a `max_height` and no height is as long as its content up to that limit (tre gives a scroll view no size from what is in it; `ComposedView._fit_scroll` sets it after layout). Stacked actions are an estimate from the label lengths. Not built: the full-screen variant, an `alertdialog` role (tre has none), focus to a form's first field, a decision-result type beyond the action's value.
- **#123, ButtonGroup.** A shipped view of `Button`s. What it needed from the language: a model param nobody bound is a local Signal the view's handlers may write (before, `chosen = ...` raised 'not writable' whenever a caller left it out, so one handler could not serve three modes); an inline style that is `None` leaves the field to the rules (the connected corner radii apply only when `connected`); and the roving focus group also starts on a `pressed` item. Names are `chosen`, not `pressed`, which is reserved. `focus_group` cannot come from a param, so it is `both`. Not built: the pressed button widening with its neighbours giving way, an overflow button.
- **#129 to #132, IconButton.** A shipped view like Button, with the icon as the one child and the label as its a11y name and `tooltip:`. What it needed from the language: a call's handler for an event the called view's root also handles (`on_click`: the view flips a toggle, the caller saves) used to replace the view's own, so a toggle with a call-site handler never flipped; now the view's runs first and the caller's after, in the caller's scope (`Instance.chained`). A blank tooltip is not shown. Widths are an expression over a size-and-width table (`width` is a style field, so the param is `width_kind`). Not built: the 48 pixel touch target.
- **One-way model params.** A model param given an expression (not one bare Signal) is a local Signal the view may write, seeded from the expression and following it each time it changes (`ComposedView`/`Composer._local_copy`). Needed because a chained call-site handler runs the view's own `selected = ...` first, and that raised on a non-writable param. `Button.flip: false` is for a caller that decides the toggle itself (ButtonGroup).
- **#133 to #140, Fab.** One shipped view for the eight issues (four colours, plain and extended): a `label` makes it extended, `collapsed` drops the label and the width goes to the square, the stylesheet picks the shape from `label` and `collapsed`. Nothing new was needed from the language. Not built: the extend half of the collapse animates only when the engine can (a width back to `auto` is set at once), and the FAB menu.
- **#201, StatusBar.** A shipped view with a grid of three sections (`1fr auto 1fr`, so the centre is centred) made by one `for:` over `start`, `center`, `end`, each holding the items for its side (names in a view are unique, so three copies of a section were refused). `interaction:` takes a colour or a boolean and no expression, so the pressable items and the plain notes are two nodes, picked by filtering the list. A grid root takes `align_cells`, not `align_content`; a progress control takes no percentage width, so it sits in a wrapper that has one. Nothing needed from the language itself.
- **#153, ListItem.** A shipped view with named `leading` and `trailing` slots (an empty slot adds no node, so the gap between parts does not double), the height worked out from which lines the item has, and the root as the pressable row (the call's handlers and style lie over it). One row component for the later rows (MenuItem, NavigationDrawerItem, SearchView results). Nothing new was needed from the language. Not built: swipe actions, drag to reorder, sticky headers, the dragged state.
- **#159 to #162, NavigationRail.** Four shipped views, each built from the one before: `NavigationRailScreen` is a `NavigationRailItem` whose `selected` is `app.current_screen == screen` and whose press is `navigate_to(screen)` (a view whose root is another view, with only params). Empty slots leave no node, so `header` and `footer` are bare `Slot`s (a wrapper around each added a gap). The roving focus group also starts on an item that is `current`. Nothing else was needed from the language. Not built: the modal expanded rail, sections, the pill animation; tre has no `navigation` or `tab` pairing for a rail, so it is a labelled group of links.
- **#148 to #150, Card.** One shipped view. What it needed from the language: `interaction:` may be an expression over the view's params, evaluated once when composing and refused if it reads a Signal (like an `a11y` role), so a card is pressable only when `actionable`. A handler written in the view's root makes the node clickable whatever `interaction` says (the builder reads the handlers), so the card has no root handler of its own and the caller supplies `on_click` (and any selection toggle). Not built: dragging and swiping, the dragged state.
- **#205, Title bar.** The bar stays the expansion in `spec/title_bar.py` (drag region, inset, fade, hot reload and the tests that pin them are all there); this step added a `tooltip` to each window button's spec, which `ComposedView._wire_tooltips` now also reads from the built specs (a `_SpecTip` stands in for an instance), and tests that the shipped views (`Tabs`, `IconButton`) work in the bar's middle. The Window's root is a row unless the window says `flex_direction: vertical`, so a bar written beside a dock sat beside it: windows with a bar want the vertical direction. Not built: snap layouts (Windows 11, no tre support), the system menu, a different glyph set.
- **#200, Pagination.** A shipped view. The expression language has no local definitions, so the numbers are one `for:` over every page with a wrapper that is shown when that page is (the first, the last, its neighbours, or the one page between an edge and the neighbours) and a gap text inside it when the page before is hidden, rather than a list of entries with ellipses built by comprehension (that needs the visible-list expression four times over). `min`, `max` and `clamp` are the functions (there is no `limit`); a name that is not a function is found only when the expression runs, not when the view loads (filed as #251). Not built: items per page, a total, jump-to.
- **#179 to #183, Chip.** One `Chip` view for the five issues (the selected filter chip was a separate fragment only because structure could not follow a param) and a `ChipGroup`. What it needed from the language: **handler parameters** (`on_remove: {type: handler}`): the caller's action or statements, compiled where they are written, run in the caller's scope when the view calls the parameter as `on_remove()`; a parameter the caller leaves out is a no-op. The group needs this to remove a chip from its list when the chip's own close is pressed (the close is inside the chip; the group is the one that owns the list). The chips' `flip: false` keeps the group in charge of the choice, as with `Button`. Not built: dragging to reorder, a scrolling chip group.
- **#154 #155, SideSheet.** Three views: the panel (header, scrolling content, actions) is shared, and a view can forward its own slots into a called view's (`- widget: Slot` inside a call's children), so the sheets add only their surround. The standard sheet's width is `min(400, max(256, width)) if open else 0` with `transition: {width: 250}` (the engine eases layout now), so it pushes the content open and shut. The modal sheet is a modal `Overlay` whose `align_content` puts the panel on a side. A back button is the `on_back` handler parameter. Not built: the detached variant, the modal sheet sliding in (an overlay is where its style says when first drawn).
- **#146, Snackbar.** `Overlay` gains `timeout` and an `on_dismiss` event (the timer is the window's own `after`, named for the overlay, cancelled when it hides, and held off while the pointer is on the layer), because a view could not otherwise start something when `open` turned true. The snackbar is a non-modal, unanchored overlay at an `absolute` `x` and `y` worked out from `app.window_width` and `app.window_height`, so it follows the window. A message wraps only when its text has a width, so the view works one out from the bar's width and the buttons'. `SnackbarHost` keys a `for:` over `messages[:1]` so each message is a new instance with a new timer, and `on_close` takes the first off the list. Not built: swipe to dismiss, lifting above a FAB.
- **#185, SpinBox.** The control stays Python (three nodes: two buttons and a field) and gains the engine's `Window.after` and `every` for hold-to-repeat (a hold that has stepped suppresses the click that ends it: tre sends `pointer_up` then `click`), a `wrap` option, `decimals`/`prefix`/`suffix` formatting and Page keys. Home and End are not taken: they move the caret in the field. The new options reach the control as one `spin` key on the lowered node (a generated key, like a title bar's `tooltip`). `SpinBoxField` is a view around it with a visible label and help line; `min` and `max` are reserved names, so it calls them `least` and `most`.
