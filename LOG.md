# LOG — M26: Detailed Scoping: `tre`-Side Primitive Additions & Macro-Layer Loop Construct

- User asked to scope both of M25's remaining fronts as separate
  milestones. No code changed — pure investigation and design.

## What shipped

1. Front A (tentatively M27) fully sized: all 7 primitives'
   (`RadioButton`/`Switch`/`Link`/`CircularProgress`/`LinearProgress`/
   `LoadingIndicator`/`TimePickerDial`) real constructors checked
   against `WidgetSpec`'s existing fields. Real correction to M25's
   own summary: 5 of 7 hardcode `PaintProperties.background` to
   `TRANSPARENT` and carry their real visual entirely in internal
   per-kind tint fields `Checkbox`/`Slider` never needed to
   theme-resolve — without closing this, declarative versions would
   render flat black regardless of theme, a real functional defect.
   Scoped a small reusable helper to fix it, not a new subsystem.
   Found `loading_indicator`'s real required `paint.shape`-seeding
   step (avoids a confirmed first-tick flash bug) and corrected
   `time_picker_dial`'s real new fields (`hour: u8`/`minute: u8`, not
   the `mode` field M25 guessed).
2. Front B (tentatively M28) fully sized: checked `pyCopper` directly
   for a repeat/loop precedent — found none. Found the 6 dynamic-list
   widgets aren't uniform: `add_list` takes pre-built `Node`s (pure
   composition — the loop construct's cleanest target, repeating the
   already-shipped `ListItem` fragment); the other 5 take raw
   `Vec<String>` and construct real state-dependent coloring
   internally in Rust, which a static template can't branch on. Full
   fidelity for `list_`; only a static snapshot for the other 5
   without a second, separate new capability.
- No new fragments, no new tests this milestone — pure scoping.

## Status

**M26 is complete. 60 fragments total, unchanged.** Committed locally
(`80deaa2`); push deferred pending explicit user confirmation.

Both fronts (M27, M28) are now scoped in enough detail to start
implementation. Next step is the user's: pick one, both, or continue
scoping something else.
