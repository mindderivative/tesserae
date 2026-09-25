# PLAN — M33: Migrate to `tre` 0.3.4

*(Replaces the M31 plan in this file — M31 is complete, committed and pushed.)*

## Goal

User-directed: "scope the tre 0.3.4 migration". Move Tesserae from `tre` v0.3.3 to the released v0.3.4 (tag on `29800f3`). 0.3.4 adds `tre`'s building-block API (M93–M96) and keeps the old API. This milestone is only the move; adopting the building blocks is the separate program `tre`'s M97 gate waits on.

## Sizing (a real 0.3.4 build, Tesserae unmodified)

- **1 of 255 tests fails**, no warnings, all 3 examples run clean.
- **Breaks, both predicted by the known gaps:**
  1. A color's alpha now renders: six Text glyphs colored `"#FFFFFF00"` (4 example views, 2 docs snippets) go from white to invisible. It's visual, so no test catches it.
  2. `opacity` is group opacity: `Dialog`/`SideSheetModal` fragments put `opacity: 0.32` on a scrim that contains the panel, so the panel fades to 32% too. This is the one failing test, because `tre`'s own scrims moved the 32% into the color's alpha.
- **Fixes that land:** `tre` issue #10 (background-thread GC panic); the M32 repro is clean on 0.3.4.
- **Checked and unaffected:** `Node.remove()` detach semantics (Tesserae only calls `Component.remove()`, which still frees), `animate()` argument order, `blur` → `unfocus`, the wheel sign fix.

## Decisions (Phase 1) — recommendations

1. **Scrim:** `background: "#00000052"` and no `opacity`. It matches `tre`'s own scrim, since MD3's scrim role is always black. The cost: a custom theme's `scrim` override won't reach these two fragments. Alternatives: make the scrim a sibling of the panel, or ask `tre` for a role-with-alpha color syntax.
2. **Labels:** `"#FFFFFF"`, which keeps today's look.
3. **`.venv`:** pin to the v0.3.4 release wheel (already built from the tag).

## Phases

1. **Decisions** — the three above.
2. **Migrate** — pin `.venv`; fix the two fragments and six labels; tests that fail on the old YAML (no translucent glyph colors; overlay scrim and panel opacity 1.0).
3. **Verify, docs, tracker** — suite and examples on 0.3.4; a tre#10 regression test; CI pinned to `v0.3.4`; `installation.md`; gaps moved to fixed.

## Status

**In progress — Phase 2 of 3 done (2026-09-25).** Decisions: the user took all three recommendations. Phase 2: `.venv` on 0.3.4; scrims `"#00000052"` (reads back `(0, 0, 0, 82)`, the same as `tre`'s); labels `"#FFFFFF"`; `tests/test_paint_0_3_4.py` scans every view, fragment and docs snippet (fails 8 times on the old files). 418 passed.

**Up next:** Phase 3, waiting on the user's go-ahead.
