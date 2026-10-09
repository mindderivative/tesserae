# Request to tre: what a typing effect needs from the text input

*Drafted for Tesserae (a wish, not yet scheduled). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae wants (eventually)

Small, fun things when typing: a flash or a fade-in on the character just typed, and a caret that glides to the next character with a shader effect instead of jumping.

## What exists today (tre 0.5.4, probed on a `text_input`)

- It has `shader`, `blend_mode`, `opacity`, `fill`, `scale`, `translate_x` and `blur`, and `animate` works on `opacity`, `fill`, `scale`, `translate_x` and `blur`. So an effect on the **whole input** is possible now (a pulse or glow on each `input` event).
- It has `caret_color`, which cannot be animated. It has no caret width, shape, blink control or position (`caret_*` other than colour raise "unknown property"), and no selection or caret API.
- A shader on the node sees the node's pixels, not where the last character or the caret is.

## The ask

1. **Caret geometry.** Read the caret's rectangle (x, y, height) in the node's coordinates, and an event when it moves (or when text changes) carrying that rectangle and the index of the character just inserted. This is what lets Tesserae draw its own caret over the input, animate it to the next position, or place an effect at the new character.
2. **Caret styling.** `caret_width`, `caret_shape` (bar, block, underline), `caret_blink` (on/off or period) and an animatable `caret_color`; or `caret_visible=False` so a framework can draw its own.
3. **Glyph rectangles.** The rectangle of a character range (as `measure_text` gives sizes, but positions in the laid-out input), so a flash or fade-in can be drawn over the character just typed.
4. **Shader inputs for the above**, if the shader route is preferred: uniforms the framework can set per frame (the caret's rectangle, the time of the last edit) already work through `shader.set(uniforms=...)`, so (1) and (3) are enough to drive them.

## How Tesserae would use it

`TextInput` gains `typing_effect` and `caret_effect` (named effects, each a small shader or an animation on a node drawn over the input), driven by the caret rectangle events. Until tre has them, the only effect possible is on the whole input.

## Questions for tre

- Is the caret drawn by tre's text renderer in a way that could be hidden, so a framework's own caret does not double it?
- Would per-character shader inputs (a glyph index or an edit time attribute) be possible, so a fade-in could be done inside the text draw rather than over it?
