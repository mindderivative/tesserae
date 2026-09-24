# PLAN — M17: Part 3, Phase 3 — Button Component Fragments (All 5 MD3 Variants)

*(Replaces the prior M16 plan in this file — M16 is complete, committed.
User-directed ordering complete: "Start 3, then move to 2 and then 1"
— items 3 and 2 both landed. This starts item 1.)*

## Goal

The other 37 component fragments, per the user's own confirmed design:
one fragment per real MD3 variant, full fidelity, not one fragment
with an unbranchable `variant` param.

## Real findings that reshaped this milestone

1. **Variant scope, confirmed via `AskUserQuestion`**: "one fragment
   per variant, all variants" — a widget like `button` (5 variants)
   needs 5 fragments (`ButtonElevated`/`ButtonFilled`/
   `ButtonFilledTonal`/`ButtonOutlined`/`ButtonText`), not one.
2. **Major blocking finding, surfaced immediately after**: `engine-
   spec`'s `NodeKindSpec` supports only 7 of `tre`'s real 21 primitive
   kinds (`Rect`/`Container`/`Text`/`Checkbox`/`Slider`/`TextField`/
   `Image`) — no `kind: Icon` at all, confirmed directly with a
   failing test (`unknown variant "Icon"`). This blocks roughly
   two-thirds of the remaining catalog (any composition with an icon
   glyph). Resolved via a second `AskUserQuestion`: added declarative
   `kind: Icon` to `tre` itself first (`tre`'s own new M74, on its
   `0.3.1` branch) rather than narrowing this milestone's scope.

## Status

**Complete.** `Button_Component.yaml` renamed to `ButtonFilled_
Component.yaml` — the new per-variant naming convention is
`<Widget><Variant>_Component.yaml` / `component: <Widget><Variant>`.
Real fix caught before it went unnoticed: every existing consumer of
the old `component: Button` name (`test_spec_expand.py`, `test_spec_
load.py`, `test_app.py`, `test_component.py`) updated to `component:
ButtonFilled` — caught by re-running the full suite immediately after
reinstalling the new `tre` build, not left stale.

4 new fragments shipped, all faithful to `resolve_button_colors`
(`window_factory.rs`) exactly: `ButtonElevated` (container=`surface_
container_low`, label=`primary`, `elevation: level_1` — MD3's real
named token, confirmed equal to `add_button`'s own unthemed `1.0`
fallback), `ButtonFilledTonal` (container=`secondary_container`,
label=`on_secondary_container`), `ButtonOutlined` (container=
`transparent`, label=`primary`, `border_color: outline`, `border_
width: 1.0`), `ButtonText` (container=`transparent`, label=`primary`).

All 5 variants cross-checked in one pass against `tesserae.widgets.
button(...)`'s own real output (`corner_radius`/`elevation`/`border_
width`) — all 5 MATCH exactly. Full suite: 101 passed, 0 regressions.
`BUILD_TRACKER.md` updated, tracker artifact regenerated (17
milestones/35 phases/84 items/7 known gaps/3 fixed gaps) and
republished. Committed locally (`1d91f1e`); push deferred pending
explicit user confirmation.

Next: `icon_button` (4 variants: filled/filled_tonal/outlined/standard,
reusing `resolve_button_colors` with `"standard"` mapped to `"text"`),
now unblocked by `kind: Icon`.
