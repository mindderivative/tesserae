# LOG — M17: Part 3, Phase 3 — Button Component Fragments (All 5 MD3 Variants)

- User-directed ordering complete: "Start 3, then move to 2 and then
  1" — items 3 and 2 both landed. This starts item 1: the remaining
  37 component fragments.

## What shipped

1. Real scoping question resolved via `AskUserQuestion` before writing
   anything: one fragment per real MD3 variant, not one fragment with
   an unbranchable `variant` param (`{{ }}` substitution has no
   conditional logic). User confirmed full fidelity for all widgets
   going forward.
2. Real, major blocking finding surfaced immediately after: `engine-
   spec` supports only 7 of `tre`'s real 21 primitive kinds
   declaratively — no `kind: Icon` at all, confirmed directly. Blocks
   ~2/3 of the remaining catalog. Resolved via a second
   `AskUserQuestion`: added declarative `kind: Icon` to `tre` itself
   first (its own new M74) rather than narrowing scope — see `tre`'s
   own `LOG.md` for that work.
3. `Button_Component.yaml` renamed to `ButtonFilled_Component.yaml` --
   the new convention: `<Widget><Variant>_Component.yaml`.
4. Real fix caught before it went unnoticed: every existing consumer
   of the old `component: Button` name (4 test files) updated to
   `component: ButtonFilled`, caught by re-running the full suite
   immediately after reinstalling the new `tre` build.
5. 4 new fragments (`ButtonElevated`/`ButtonFilledTonal`/
   `ButtonOutlined`/`ButtonText`), all faithful to `resolve_button_
   colors` exactly. `ButtonElevated` uses `elevation: level_1` -- MD3's
   real named token, confirmed equal to the identical `1.0`
   `add_button`'s own unthemed fallback uses.
6. All 5 variants cross-checked in one pass against `tesserae.widgets.
   button(...)`'s own real output -- all 5 MATCH exactly.
- Verification: `pytest tests/` 101 passed, 0 regressions.

## Status

**M17 is complete.** Committed locally (`1d91f1e`); push deferred
pending explicit user confirmation.

Next: `icon_button` (4 variants), now unblocked by `kind: Icon`.
