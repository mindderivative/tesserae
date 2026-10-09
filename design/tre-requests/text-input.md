# Request to tre: more on the text input

*Drafted for Tesserae 0.5.0 (#234). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae needs

A text field that behaves the way Material 3 and the platforms expect: a limit on its length, a read-only mode, a mask, a mode that picks the keyboard on a touch device, Enter as its own event, and IME composition.

## What exists today (tre 0.5.4)

A `text_input` node has `placeholder`, `multiline` and `obscured`. It has no `max_length`, `read_only`, `input_mode`, `mask`, `submit` or composition property (each raises "unknown node property"). Tesserae works round three of them in the renderer: `max_length` and `read_only` by putting the text back on `change`, a `mask` by rewriting it (#222), `on_submit` by watching Enter on `key_down`. Those workarounds flicker for a frame on a real input, lose the caret position (setting `text` moves the caret to the end), and cannot reject an edit before it is drawn.

## The ask

- `max_length`, `read_only` (selectable and copyable, not editable), and `input_mode` (`text`, `numeric`, `decimal`, `email`, `phone`, `url`, `search`) on `text_input`.
- A `submit` event for Enter in a single-line input (not multiline).
- An edit filter, or a `before_change` event that can reject or rewrite the new text and say where the caret goes: that is what lets a mask keep the caret in place.
- IME composition: events for the composition (start, update with the preedit text and its cursor, commit, cancel) and the preedit drawn in the input, with the underline the platform uses. There is no workaround for this one, so it matters most for East Asian languages.
- A caret and selection API: `selection_start`, `selection_end` readable and settable.

## How Tesserae uses it

`TextInput` already declares `max_length`, `read_only` and `mask`; the renderer would pass them to the node and drop its workarounds. `selection_*` and the composition events would reach handlers as `on_compose`.

## Questions for tre

- Does `read_only` still allow focus and Tab, so a screen reader can read the field?
- Is the preedit drawn by tre or by the OS?
