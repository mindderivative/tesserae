# Interaction Feedback

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
Links and text fields keep their own roles.

## The state layer and ripple

A clickable `Rect` or `Container` also gets MD3's state layer and ripple:

| State | What shows |
| --- | --- |
| Hovered | The node is tinted at 8%, even while the pointer is over one of its children. |
| Focused by keyboard | Tinted at 10%. Focus from a click shows nothing extra. |
| Pressed | A ripple spreads from the press point at 10% until it covers the node, and fades once the press ends. A quick tap still shows it for 225 ms. Enter or Space ripples from the centre. |

The tint is the theme's `on_surface` by default, and it follows theme
changes, including light and dark. The feedback paints over the node's
content, clipped to its rounded corners. The node gets
`clip_children: true`, so children that overflow it are clipped too.

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
or `None` if it has none. Its `layer` is the state layer node, and
`ripples` lists the live ripple nodes. `set_dragged(True)` shows MD3's
dragged state (16%), for widgets that drag.

The opacities are MD3's. The ripple's timing is Material Web's: it grows
over 450 ms with MD3's standard easing, fades in over 105 ms and fades out
over 375 ms.

## Not yet covered

- A visible focus ring on keyboard focus comes in M39 Phase 3.
- Only `Rect` and `Container` get the state layer and ripple. The
  built-in MD3 controls (checkbox, switch and so on) are still `tre`'s
  until M40.
