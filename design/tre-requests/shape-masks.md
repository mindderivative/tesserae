# Request to tre: clip any node to a shape (a mask)

*Drafted for Tesserae 0.5.0 (#225). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae needs

A way to clip a node, and everything in it, to a shape other than its own rectangle with rounded corners: a circle, a rounded rectangle with per-corner radii, or a path. The first use is a round avatar or a rounded thumbnail made from an `image` node (Tesserae #236), but it is wanted wherever content has to take a shape: a cropped video, a card's media area, a masked icon.

## What exists today (tre 0.5.4)

Checked with `Node.get` on a node of each kind: there is no `mask`, `clip_path` or `clip_shape` property. `corner_radius` (a number, or a 4-tuple) shapes a box's own fill, stroke and shadow, and `clip_children` clips to the node's rectangle. Whether an `image` node's pixels follow its own `corner_radius`, or a `clip_children` box with a radius clips its children to the rounded shape, could not be checked here (`Window.snapshot` returned a blank frame in this environment), so Tesserae cannot yet say what it can rely on.

## The ask

One node property, `mask`, taking:

- `"circle"`: the largest circle in the node's box (an ellipse if it is not square);
- `{"rounded": radius_or_4_tuple}`: a rounded rectangle, so a mask can differ from the node's own `corner_radius`;
- `{"path": data, "view_box": (x, y, w, h)}`: any path, scaled to the node's box.

Applied to the node and its subtree, antialiased at the edge, and following the node's transform. Hit testing should follow the mask (a press on the clipped-away corner reaches what is behind), or at least be able to (`hit_testable` is there already).

## How Tesserae uses it

`style: {mask: circle}` (or `mask: {rounded: 12}`) as a style field, so a rule can give it and `transition:` can ease it where tre can animate it. Until tre has it, Tesserae gives an image the container's `corner_radius`, as the issue says.

## Questions for tre

- Is animating `mask` (rounded to circle) within reach, as `corner_radius` is?
- Does a mask on a node with `backdrop_blur` clip the blurred backdrop too?
