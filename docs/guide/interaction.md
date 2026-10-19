# Interaction & Accessibility

A YAML node with an `on_click` handler behaves like an MD3 button,
whether it's used with a mouse, a keyboard or a screen reader. Tesserae
draws the feedback itself.

```yaml
- widget: Rect
  name: save
  style: {width: 120, height: 40, background: secondary_container, corner_radius: 20}
  handlers: {on_click: save}
```

A `Button` works the same way: give its call the handler,
`widget: Button` with `handlers: {on_click: save}`
(see [Handlers, bindings and names on a call](component-fragments.md#handlers-bindings-and-names-on-a-call)).

## The keyboard and assistive technology

A clickable node is focusable. Tab reaches it, and Enter or Space clicks
it, calling the same ViewModel method a mouse click does. It has
`role="button"`, so assistive technology announces it as a button.
A `Link` keeps its own role. Give a button a label, so
it's announced by name (see [below](#labels-and-roles-a11y)). A `Text` or
`Icon` with an `on_click` is focusable and a button in the same way, but
has no state layer or ripple (see below).

On keyboard focus, a clickable node shows MD3's focus ring: 3 px in the
theme's `secondary`, 2 px outside the node, following its corners. Focus
from a click shows no ring.

A row of related controls (a toolbar, tabs, a menu, a radio set) is one tab stop when it has a `focus_group`: the arrow keys move
among its items, `Home` and `End` go to the first and last, and typing the start of an item's name jumps to it
(see [Focus](view-language.md#focus)). `focus('name')` in a handler moves the focus to a named node.

## The state layer and ripple

A clickable `Rect` or `Container` also gets MD3's state layer and ripple:

| State | What shows |
| --- | --- |
| Hovered | The node is tinted at 8%, even while the pointer is over one of its children. |
| Focused by keyboard | Tinted at 10%. Focus from a click shows nothing extra. |
| Pressed | A ripple spreads from the press point at 10% until it covers the node, and fades once the press ends. A quick tap still shows it for 225 ms. Enter or Space ripples from the centre. |

The tint is the theme's `on_surface` by default, and it follows theme
changes, including light and dark. The feedback paints over the node's
content, clipped to its rounded corners. The node itself isn't clipped,
so its children can still overflow it.

When clickable nodes are nested, only the innermost one responds. A
press ripples only that node, and its `on_click` handler is the only one
that runs, as MD3 expects: a button in a clickable card, or a checkbox
in a clickable list row, doesn't open the card or row as well. The
innermost handler stops the click from going further up the tree. This
applies to pointer, keyboard (Enter and Space) and simulated clicks.

A child with no handler, such as a label or an icon inside a clickable
card, doesn't stop the click, so it still reaches the card. A decorative
layer laid over a button with `pointer_events: none` doesn't either (see
[Effects](effects.md)). A disabled
control does stop the click: nothing fires, and the card doesn't open.

### Choosing the colour, or turning it off

```yaml
interaction: false                 # no state layer or ripple
interaction: on_primary            # a theme role
interaction: "#FFFFFF"             # or a colour
interaction: true                  # feedback without an on_click
```

On a filled background, give the content's colour, such as `on_primary`
on `primary`, as MD3 does. The value may be an expression, and `interaction:`
on a call goes to the root of the view called (a component that is a button
by default, such as `Card` with `actionable`, sets it from its params).
`interaction:` works on `Rect` and `Container` only. A `Text` or `Icon` can't
hold the layer: `interaction: true` on one is accepted and shows nothing,
so wrap it in a clickable `Container`.

`hovered`, `focused` and `pressed` are also names an expression can read, for
the nearest widget with `interaction`: `style: {background: "{{ 'primary' if
hovered else 'surface' }}"}`. A stylesheet rule reaches the same states with
`state: hovered`, `focus_visible` or `pressed` (see
[The View Language](view-language.md#style)).

How a ripple is drawn (a circle node for each press, or one shader) and
whether the focus ring turns are App options: see
[Window Options](window-options.md).

## From code

`view = app.open_view("Main")` returns the view, and
`view.interaction("root.save")` the node's `tesserae.interaction.Interaction`
(by the node's id, the path from the root), or `None` if it has none. Its `layer` is the state layer node,
`ripples` lists the live ripple nodes, and `ring` is the focus ring
(`ring_visible` says whether it's showing). `set_dragged(True)` shows
MD3's dragged state (16%), for widgets that drag.

The opacities are MD3's. The ripple's timing is Material Web's: it grows
over 450 ms with MD3's standard easing, fades in over 105 ms and fades out
over 375 ms.

## Disabled

A `Rect`, a `Container` or a widget that declares `disabled` is disabled with
that key, a plain `true` or an expression:

```yaml
name: toolbar
widget: Container
style: {flex_direction: horizontal, gap: 8}
children:
  - widget: Button
    name: back
    label: Back
    variant: tonal
    handlers: {on_click: go_back}
    disabled: "{{ not app.can_go_back }}"
  - widget: Rect
    name: save
    style: {width: 120, height: 40, background: primary, corner_radius: 20}
    handlers: {on_click: save}
    disabled: true
```

While it's disabled a node:

- is announced disabled, and isn't focusable (Tab skips it);
- shows no state layer, ripple or focus ring;
- runs none of its handlers. A click on it is still taken, as a disabled
  button swallows one, so a clickable card behind it doesn't get it;
- fades to 38% of its style's `opacity` (MD3's disabled content
  opacity), and returns to it when enabled.

Enabled again, it's focusable as before: a clickable node is a Tab stop,
a plain one isn't. The state holds through a re-theme, a stylesheet
change and a reload. A control (`Checkbox`, `Switch`, `SpinBox`, ...)
takes the same key for its own `disabled`, and draws its own disabled look.

## Labels and roles: `a11y:`

A node's `a11y:` field sets what assistive technology hears:

```yaml
- widget: Rect
  name: save
  style: {width: 120, height: 40, background: secondary_container, corner_radius: 20}
  handlers: {on_click: save}
  a11y: {label: Save}
- widget: Text
  name: title
  text: Settings
  typography_role: headline_small
  style: {foreground: on_surface}
  a11y: {role: heading, level: 1}
```

| Field | What it does |
| --- | --- |
| `label` | The name read out, for a node whose content doesn't say it (an icon button, say). |
| `role` | One of `tre`'s roles: `alert`, `button`, `checkbox`, `dialog`, `group`, `heading`, `img`, `link`, `list`, `listitem`, `menu`, `menuitem`, `none`, `progressbar`, `radio`, `separator`, `slider`, `switch`, `tab`, `tablist`, `tabpanel`, `textbox`, `tree` or `treeitem`. A clickable node is a `button` unless you give another role, and it stays focusable. A `Link` has its own role, so `role` is an error on it. |
| `hidden` | `true` hides a decorative node from assistive technology. |
| `live` | `off`, `polite` or `assertive`, so changes to the node's content are announced. |
| `level` | A heading's level, from 1. |
| `expanded` | `true` or `false` on something that opens and closes (a disclosure, a menu button); leave it out on what cannot. |
| `selected` | `true` or `false` on one of a set (a tab, a list row). |
| `checked` | `true` or `false` on something that is on or off; `null` is neither. |
| `value`, `value_min`, `value_max`, `value_step` | A number and its range, for something that has one (a progress bar, a custom slider). |
| `pressed`, `invalid`, `busy`, `description`, `current`, `value_now`, `value_text` | The rest of a widget's state: a toggle button's `pressed` (`true`, `false` or `mixed`), a field that failed validation, a loading widget, a longer description, the current page or step, and a number with its spoken form. See [Accessibility](view-language.md#accessibility). |
| `describedby`, `controls` | The `name:` of another node of the view (or a list of them) that describes this one, or that this one controls. |

On a TextField, the fields apply to its input; on a control (a
checkbox, a switch and so on), to the control, which sets its own
`checked`, `selected` and `value`, so those three are an error there.
Anything else that does not fit is an error that names the widget.

### Bound fields

Every field but `role`, `live`, `describedby` and `controls` can be an expression (a binding), and it is kept up to date as what it reads changes (a `label` must come out as text, so write `"{{ n }} unread"`, not `"{{ n }}"`):

```yaml
- widget: Text
  name: inbox_status
  text: Inbox
  typography_role: body_medium
  style: {foreground: on_surface}
  a11y: {label: "Inbox, {{ unread }} unread", live: polite}
- widget: Container
  name: details
  a11y: {hidden: "{{ collapsed }}"}
```

A label made of text and values is one expression, as for any text (`"Inbox, {{ unread }} unread"`). A label must come out a
string, `hidden`, `expanded`, `selected` and `checked` true or false, a `value` a number, and `level` a whole number from 1; `None` clears
a label, a level, a state or a number (not `hidden`). A wrong value is an error naming the widget and field. `live` is how a node's
changes are announced, so it is set once and is not an expression; a `role` may be worked out from a view's params, but is fixed while the
view is open, since it is what the node is. A bound label on a Link is its name, whatever its text says.

## For widgets: `tesserae.a11y`

Tesserae's widgets describe themselves with `tesserae.a11y`:

```python
from tesserae import a11y

a11y.describe(node, role="switch", label="Wi-Fi", checked=True)
undo = a11y.on_action(slider, {
    "increment": lambda event: step(+1),
    "set_value": lambda event: set_to(event.value),
})
```

`describe` checks every field before setting any of them. It takes the
YAML fields above plus `disabled`; `describedby` and `controls` name other
nodes of a view, so they are written in the view's `a11y:` and `describe`
refuses them. `on_action` routes the
requests a screen reader can make: `increment`, `decrement`, `expand`,
`collapse`, `scroll_into_view` and `set_value`. Activating (clicking)
isn't one of them: `tre` doesn't route it through `a11y_action`.
`ROLES`, `LIVE` and `ACTIONS` are `tre`'s lists.

`tre`'s `disabled` is announced only: a disabled node still takes focus
and clicks. Tesserae's [controls](controls.md) make it behave: a disabled control
can't be focused or used, and draws in MD3's disabled colours.

`bind` keeps a widget's `label`, `hidden`, `level`, `expanded`, `selected`, `checked`, `value` (with its range) or any of the other states
(`pressed`, `invalid`, `busy`, `description`, `current`, `value_now`, `value_text`) up to date, as a bound YAML field does. Each is a `Signal`, a `Computed`, a
function of no arguments or a plain value:

```python
from tesserae import Computed, a11y

stop = a11y.bind(inbox_button, label=Computed(lambda: f"{unread.get()} unread"),
                 hidden=collapsed)
```

It takes a node, or a widget or control (their `.node`), checks each
value as `describe` does, and returns the function that stops it. `role`
and `live` aren't bindable: set them once with `describe`.

## Not yet covered

- Among plain YAML nodes, only `Rect` and `Container` get the state
  layer, ripple and focus ring. The MD3 controls (checkbox, switch and
  so on) have their own ([Controls](controls.md)).
- The ring is placed when focus arrives. A node that resizes while it
  has focus keeps its old ring until focus moves.
