# Request to tre: animatable layout properties, and an animation-finished event

*Drafted for Tesserae 0.5.0 (#233). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae needs

A collapse or expand that eases: an accordion opening, a navigation rail growing from icons to icons and labels, a drawer sliding, a chip shrinking, a list item changing height, a FAB extending. Today Tesserae can ease what tre animates (`opacity`, `fill`, `stroke_*`, `corner_radius`, `shadows`, `scale`, `translate_*`, `rotation_deg`, a scroll view's `scroll_offset`, a path's `data` and trim) and nothing that changes the layout.

## What exists today (tre 0.5.4)

`Node.animate` on `width`, `height`, `x`, `y`, `padding_left`, `gap`, `font_size`, `flex_grow` and `margin_top` each raises "node property ... isn't animatable". `animate(..., on_complete=fn)` takes a callback, but there is no node event for an animation finishing, which a listener could use.

## The ask

1. Make the layout properties animatable: `width`, `height`, `min_*`, `max_*`, `x`, `y`, `padding_*`, `margin_*`, `gap`, `flex_basis` (and `font_size`, if text can relayout per frame), with the same easings. Layout is recomputed each frame of the animation; the damage tracking already has to cope with a moving node.
2. An `animation_end` event on the node (property name and whether it ran to the end or was cancelled), so a framework can chain steps without a callback per call.

## How Tesserae uses it

`style.transition` already names the properties that ease (#214); the layout ones (`width`, `height`, `padding`, `gap`, `margin`, `x`, `y`) would be accepted (#239) and eased by the same code. Until then a collapse is a transform or frame by frame, and `transition:` rejects those names with a message saying so.

## Questions for tre

- Is animating `auto` to a number supported (a collapsing height starting from its content's height)? Components need it; a framework can measure first if not.
- What does an interrupted layout animation do: retarget from the current value, as the others do?
