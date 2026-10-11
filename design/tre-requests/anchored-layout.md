# Request to tre: place a node against another node, in the tree (and at its corners)

*Drafted for Tesserae 0.5.0.8 (#262, part of #257). Sent 2026-10-11 as mindderivative/tre#179. Probed on tre 0.5.6.*

## What Tesserae needs

A node placed against a named node that is not its parent, and following it: a badge on the corner of a distant button, a label beside a field, a marker on a chart point. #116 (L10) listed it as `style: {anchor: b}`.

## What exists today (tre 0.5.6)

`window.show_layer(node, anchor=other, placement=...)` does this for a **layer**: tre places the layer against the anchor at every layout, so it follows the anchor with no lag (probed: an anchor moved from x=100 to x=200 in one `advance`, and the layer was at x=200). Tesserae's `Overlay` widget (`widget: Overlay`, `anchor:`, `placement:`) is this, so a floating thing beside a distant node can be written in a view today. It is not enough for a badge or a marker, because a layer is:

- **drawn above the whole window**, not in its place in the tree: it escapes an ancestor's `clip_children` (probed: an anchor at the right edge of a clipped box, placement `end`, put the layer past the box's edge, drawn in full) and its `z_index` among siblings does not apply;
- **its own Tab scope**, and events inside it stop at it;
- **placed on four sides only**: `below`, `above`, `start`, `end`. `top_end`, `above_end`, `bottom_start`, `center` and `over` are each rejected. Each side is aligned with the anchor's start edge (below or above: the same x as the anchor; start or end: the same y), so "on the corner" and "centred on it" cannot be said (a transform on the node is the only way to nudge it);
- **flipped or shifted to fit** (probed: `above` an anchor 4 pixels from the top edge lands below it), which suits a menu and not a marker that must stay on the corner.

An ordinary node cannot do it: an absolute node is placed by `x` and `y` in its parent (there is no `right` or `bottom` either; see `absolute-insets.md`), and there is no node-level event for a change of layout (`resize`, `layout` and `layout_changed` are each rejected), so Tesserae cannot follow an anchor from outside.

## The ask

Either of these (the first is smaller):

1. **Corner and centre placements, and an offset, for layers:** `placement` taking `top_start`, `top_end`, `bottom_start`, `bottom_end` and `center`, plus `offset=(dx, dy)`, and a way to say "do not flip". That makes `Overlay` enough for a corner badge, at the price that it is still a layer.
2. **A node that stays in the tree and is placed against another node:** an `anchor` and `placement` on an ordinary node (with the same corners and offset), laid out after the anchor, clipped and ordered as a child of its parent is. Layout would resolve it, so there is no lag and no cycle (an absolute node does not change its anchor's layout).

## What the workaround costs

A Tesserae-side `anchor:` style would re-place the node each frame against the anchor's laid-out box (`window.on("frame")` is accepted). It trails the anchor by a frame, and a scrolling or transformed ancestor makes the arithmetic wrong. Tesserae does not build it for that reason.

## Questions for tre

- Is an in-tree anchored node compatible with how tre orders layout (the anchor must be laid out first)?
- Would corners on layers be a small change, if the in-tree version is not?
