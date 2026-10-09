# Request to tre: clip any node to a shape (a mask)

*Drafted for Tesserae 0.5.0 (#225). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae needs

A way to clip a node, and everything in it, to a shape that is not a rounded rectangle: a path (a squircle, a cut corner, a blob). Round and rounded images already work; the use for a general mask is MD3's expressive shapes on media, a cropped video, a card's media area, a masked icon.

## What exists today (tre 0.5.4)

Checked with `Node.get` on a node of each kind: there is no `mask`, `clip_path` or `clip_shape` property. What does work, checked by reading pixels
from `Window.snapshot`:

- an `image` node clips its own pixels to its `corner_radius`, including a 4-tuple (a different radius on each corner) and a radius larger than the
  node (a pill, or a circle on a square image);
- a `box` with `clip_children` and a `corner_radius` clips its children to the rounded shape.

So circles and rounded rectangles are covered, and Tesserae's Image uses them (`style.corner_radius`). What is missing is any shape that is not a
rounded rectangle.

## The ask

One node property, `mask`, taking:

- `{"path": data, "view_box": (x, y, w, h)}`: any path, scaled to the node's box;
- optionally `"circle"` and `{"rounded": radius_or_4_tuple}` as shorthands, so a mask can differ from the node's own `corner_radius`.

Applied to the node and its subtree, antialiased at the edge, and following the node's transform. Hit testing should follow the mask (a press on the clipped-away corner reaches what is behind), or at least be able to (`hit_testable` is there already).

## How Tesserae uses it

`style: {mask: {path: ..., view_box: ...}}` as a style field, so a rule can give it and `transition:` can ease it where tre can animate it. Until tre has it, a rounded or circular shape is `corner_radius`.

## Questions for tre

- Is animating `mask` between two paths with the same structure within reach, as `corner_radius` is?
- Does a mask on a node with `backdrop_blur` clip the blurred backdrop too?
