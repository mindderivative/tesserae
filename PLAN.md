# PLAN — M11: Widget Catalog, Part 2d — Navigation & Shell Composition

*(Replaces the prior M10 plan in this file — M10 is complete, committed.)*

## Goal

Continue the widget catalog: `tabs`/`navigation_rail`/
`navigation_drawer`/`toolbar`/`top_app_bar`/`status_bar` — the 6 real
factories in `tre`'s own "Navigation & Shell Composition" category —
same thin-delegate pattern M8-M10 established.

## Status

**Complete.** `src/tesserae/widgets/navigation.py` — all 6, verified
directly against `window_factory.rs`.

Real, concrete first application of M8's naming-translation decision:
`add_toolbar`'s own `color=` param isn't an RGBA color — it's a named
container-tone selector (`"standard"`/`"vibrant"`), confirmed directly
in the Rust source. Tesserae's own `toolbar(tone=...)` translates to
it internally, since calling a two-value named selector `color` is its
own kind of confusing given every other `color`/`background` kwarg in
the catalog takes an RGBA tuple.

7 new pytest tests (`test_widgets_navigation.py`): parity on
`corner_radius`, a dedicated check proving the `tone=`→`color=`
translation reaches the identical underlying resolution as the native
call, and a real kwarg-forwarding check (`variant="docked"` vs.
`"floating"` resolves to different corner radius *and* elevation).
Full suite: 56 passed (49 prior + 7 new), 0 regressions.
`BUILD_TRACKER.md` updated, tracker artifact regenerated (11
milestones/21 phases/44 items/4 known gaps/1 fixed gap) and
republished. Committed locally (`66d2137`); push deferred pending
explicit user confirmation.

Next: the remaining 2 widget categories in the original Part 2 scope
(Overlays, Search) plus Date & Time and Media & Graphics. Then Part 3
(YAML component macro-expansion).
