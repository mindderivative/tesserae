# Request to tre: insets on an absolute node (or mixed-unit sizes)

*Drafted for Tesserae 0.5.0.8 (#261, part of #257). Sent 2026-10-11 as mindderivative/tre#178. Probed on tre 0.5.6.*

## What Tesserae needs

An absolutely positioned node that is stretched between two edges of its parent: "8 pixels from the left and 8 from the right", or "the whole width except a 16 pixel strip". Today a view cannot say it. The YAML user's wish (#116, L10) was spelled `width: calc(100% - 16)`.

## What exists today (tre 0.5.6)

- A size (`width`, `height`) is a number, `"auto"` or a percentage like `"50%"`. `"calc(100% - 16)"`, `"100% - 16"`, `"40px"`, `"10vw"`, `"fit-content"` and `"stretch"` are each rejected with *node property `width` must be a number, "auto", or a percentage*.
- An absolute node is placed by `x` and `y` only. `right`, `bottom`, `inset`, `inset_right` and `x2` are each rejected as unknown node properties.
- A margin does not shrink an absolute node: `position="absolute", x=8, width="100%", margin_right=16` in a 300 pixel parent is 300 wide at x=8 (it runs 8 pixels past the parent). `width="auto"` with `x=8` and `margin_right=8` is 0 wide.
- There is no node-level event for a size change (`resize`, `layout`, `size_changed` and `layout_changed` are each rejected; the window has `resize` only), so Tesserae cannot learn that a parent changed size unless the window did.

## What a node in the flow can already do

In the flow the same sizes are exact without calc: `flex: fill` with margins on both sides is `100% - margins` across the parent's axis (a 300 pixel column, margins 8: 284 wide), and two `flex: fill` children with a `gap` of 16 are `50% - 8` each (142 and 142). Tesserae documents these. They need the node to be in the flow, which an overlay-like absolute node is not.

## The ask

In order of how little it asks of tre, and how well it fits:

1. **Insets on an absolute node:** `right` and `bottom` (and perhaps `left`/`top` as aliases of `x`/`y`), with the usual meaning when both edges are given and the size is `auto`: the node is stretched between them. The layout engine already has the idea of an inset for an absolute child; it asks only to be exposed.
2. **Mixed-unit sizes:** a size that is a percentage plus pixels (`calc`-like), for the cases insets do not cover (`calc(33% + 10)`). The base of the percentage would be the parent's content box, as `"50%"` is now.

Either would let Tesserae write `x: 8, right: 8` or `width: calc(100% - 16)` in a view without any layout pass of its own.

## What the workaround costs

A Tesserae-side `calc` would have to set a number on the node whenever its parent's laid-out size changes. With no size-change event it can only re-run on window resizes and after Tesserae's own changes, or on every frame (`window.on("frame")` is accepted). The frame version follows any cause but trails the parent by one frame, and it can fall into a loop when the parent is `auto` and sized by the child (`child = parent - 16`, `parent = child`: the child shrinks 16 pixels each frame). Tesserae does not build it for that reason.

## Questions for tre

- Does tre's layout engine expose insets (`left`, `right`, `top`, `bottom`) for absolute children, as CSS does?
- Is a node-level layout-changed event feasible (the measured sizes `measured_width` and `measured_height` would be exact with it)?
