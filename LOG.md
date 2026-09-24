# LOG — M18: Part 3, Phase 4 — `icon_button`/`fab`/`extended_fab` Component Fragments

- Continues item 1, now unblocked by `tre`'s new declarative `kind:
  Icon` — the first 3 widget families that actually need an icon
  glyph.

## What shipped

1. `IconButtonFilled`/`IconButtonFilledTonal`/`IconButtonOutlined`/
   `IconButtonStandard` — reuses `resolve_button_colors` directly
   (confirmed: `"standard"` maps to `"text"`'s own colors, the same
   real translation the imperative factory itself performs).
2. `FabSurface`/`FabPrimary`/`FabSecondary`/`FabTertiary` — real,
   useful finding: `elevation: level_3` is a genuine fixed MD3 token
   here (confirmed `ELEVATION_LEVEL_3 == 3.0`, same across all 4
   colors) — no elevation param needed, unlike `corner_radius` (still
   required — FAB's 3 real sizes each pair a fixed container size with
   their own shape token).
3. `ExtendedFabSurface`/`ExtendedFabPrimary`/`ExtendedFabSecondary`/
   `ExtendedFabTertiary` — real, fixed `corner_radius: large` token too
   (confirmed `SHAPE_LARGE == 16.0 == EXTENDED_FAB_CORNER_RADIUS`
   exactly — Extended FAB has no size variants in real MD3 at all).
   Real, deliberate scope boundary: only the leading-icon shape
   shipped — `icon` is optional imperatively, changing both the
   leading padding and whether an `Icon` child exists at all, a
   genuine structural difference `{{ }}` can't conditionally express.
4. `tests/test_fragments_buttons.py` (new file) — 3 real pytest tests,
   each looping over its family's 4 variants, cross-checking against
   `tesserae.widgets`'s own imperative output (12 real variant checks)
   — all MATCH.
- Verification: `pytest tests/` 104 passed (101 prior + 3 new), 0
  regressions.

## Status

**M18 is complete.** 17 fragments total so far. Committed locally
(`8c6500e`); push deferred pending explicit user confirmation.

Next: `split_button` (a fixed 2-button+chevron shape, not a dynamic
list), then onward through the remaining categories.
