# Interaction & Accessibility

A YAML node with an `on_click` handler behaves like an MD3 button,
whether it's used with a mouse, a keyboard or a screen reader. Tesserae
draws the feedback itself, since `tre` 0.3.5 doesn't.

```yaml
- id: save
  kind: Rect
  style: {width: 120, height: 40, background: secondary_container, corner_radius: 20}
  handlers: {on_click: "save"}
```

## The keyboard and assistive technology

A clickable node is focusable. Tab reaches it, and Enter or Space clicks
it, calling the same ViewModel method a mouse click does. It has
`role="button"`, so assistive technology announces it as a button.
Links and text fields keep their own roles. Give a button a label, so
it's announced by name (see [below](#labels-and-roles-a11y)).

On keyboard focus, a clickable node shows MD3's focus ring: 3 px in the
theme's `secondary`, 2 px outside the node, following its corners. Focus
from a click shows no ring.

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

When clickable nodes are nested, a press ripples only the innermost
one. The click itself still bubbles to every `on_click` handler, as
before.

### Choosing the colour, or turning it off

```yaml
interaction: false                 # no state layer or ripple
interaction: {color: on_primary}   # a theme role or a hex colour
interaction: true                  # feedback without an on_click
```

On a filled background, give the content's colour, such as `on_primary`
on `primary`, as MD3 does. `interaction:` works on `Rect` and
`Container` only. A `Text` or `Icon` can't hold the layer, so wrap it in
a clickable `Container`.

## From code

`view.interaction("save")` returns the node's `tesserae.interaction.Interaction`,
or `None` if it has none. Its `layer` is the state layer node,
`ripples` lists the live ripple nodes, and `ring` is the focus ring
(`ring_visible` says whether it's showing). `set_dragged(True)` shows
MD3's dragged state (16%), for widgets that drag.

The opacities are MD3's. The ripple's timing is Material Web's: it grows
over 450 ms with MD3's standard easing, fades in over 105 ms and fades out
over 375 ms.

## Labels and roles: `a11y:`

A node's `a11y:` field sets what assistive technology hears:

```yaml
- id: save
  kind: Rect
  style: {width: 120, height: 40, background: secondary_container, corner_radius: 20}
  handlers: {on_click: "save"}
  a11y: {label: "Save"}
- id: title
  kind: Text
  text: {content: "Settings", font_family: Roboto, font_size: 22}
  style: {foreground: on_surface}
  a11y: {role: heading, level: 1}
```

| Field | What it does |
| --- | --- |
| `label` | The name read out, for a node whose content doesn't say it (an icon button, say). |
| `role` | One of `tre`'s roles: `button`, `tab`, `heading`, `listitem`, `img`, `group`, `none` and so on. A clickable node is a `button` unless you give another role, and it stays focusable. Links and text fields have their own roles, so `role` isn't allowed on them. |
| `hidden` | `true` hides a decorative node from assistive technology. |
| `live` | `polite` or `assertive`, so changes to the node's content are announced. |
| `level` | A heading's level, from 1. |

On a TextField, the fields apply to its input. A field you remove is
reset when the view reloads. Anything else is an error that names the
widget. Widget states such as `checked` belong to Tesserae's own
controls (M40).

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
YAML fields above plus `checked`, `selected`, `expanded`, `disabled` and
`value`/`value_min`/`value_max`/`value_step`. `on_action` routes the
requests a screen reader can make: `increment`, `decrement`, `expand`,
`collapse`, `scroll_into_view` and `set_value`. Activating (clicking)
isn't one of them: `tre` 0.3.4 doesn't route it through `a11y_action`.
`ROLES`, `LIVE` and `ACTIONS` are `tre`'s lists.

`tre`'s `disabled` is announced only: a disabled node still takes focus
and clicks. Tesserae's controls make disabled behave, from M40.

## Not yet covered

- Only `Rect` and `Container` get the state layer, ripple and focus
  ring. The built-in MD3 controls (checkbox, switch and so on) are still
  `tre`'s until M40.
- `a11y:` values are fixed in the YAML; binding a label to a `Signal`
  isn't supported yet.
- The ring is placed when focus arrives. A node that resizes while it
  has focus keeps its old ring until focus moves.
