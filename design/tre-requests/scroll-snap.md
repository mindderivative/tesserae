# Request to tre: horizontal scrolling and scroll snap points

*Sent as mindderivative/tre#166. From Tesserae 0.5.0 (#240). Re-checked on tre 0.5.6 (86f847b): nothing below exists yet.*

## What Tesserae needs

Carousels and scrolling tab strips: a row of items that scrolls sideways and comes to rest with an item aligned (snap), by wheel, drag or touch. Also a vertical list that snaps to its rows (a picker).

## What exists today (tre 0.5.4 and 0.5.6)

- **A `scroll_view` scrolls vertically only.** With a content box wider than the view (`flex_direction="horizontal"`, 500 wide in a 100 wide view), `scroll_offset=150` reads back as 0.0, and a wheel event with `delta_x=60` does nothing. There is one `scroll_offset`, no `scroll_offset_x`, no axis property. So a sideways carousel or tab strip cannot scroll at all, snap or not.
- No snap: `scroll_snap`, `snap_points`, `scroll_snap_type`, `snap_align` and `scroll_behavior` all raise "unknown node property", on a `scroll_view` and on a `virtual_list`.
- `animate("scroll_offset", ...)` works (an offset 50 ms into a 100 ms linear animation read 100 of 200), which is what a framework would use to settle on a snap point. A `virtual_list` has no `scroll_offset` property at all.

## The ask

1. Horizontal (and both-axis) scrolling on `scroll_view`: a `scroll_axis` (`vertical`, `horizontal`, `both`) and `scroll_offset_x` / `scroll_offset_y` (or `scroll_offset` as a pair), with wheel `delta_x`, shift-wheel, and touch/drag panning, and the `scroll` event carrying both offsets.
2. Snap points, as CSS has them: `scroll_snap` (`none`, `start`, `center`, `end`, optionally `proximity` or `mandatory`) on the scroll view, and `snap_align` on children; or a list of offsets. The view settles on the nearest point when the user lets go, animated.
3. The same on a `virtual_list`, and `scroll_offset` on it.

## How Tesserae uses it

`ScrollView` gains `axis` and `snap`; the Carousel and Tabs components use them. Until then they snap with an animated `scroll_offset`, which only works for vertical content; a sideways strip has to be moved by a transform on its content.

## Questions for tre

- Is horizontal scrolling planned? A `scroll_view` that reads back 0.0 for an offset it cannot take is quiet about it; a `ValueError` would help.
