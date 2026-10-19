# Rich Text & Links

A `Text` is text in one style: one `typography_role`, one `foreground`, one weight. For text that is partly bold, struck through, coloured
or a link, give it `runs`: the pieces of one text, each with its own style. A whole line that opens a page is a [`Link`](#links).

```yaml
widget: Text
name: offer
typography_role: body_large
style: {foreground: on_surface, width: 360}
runs:
  - "Sale: "
  - {text: "{{ was }}", strikethrough: true, color: on_surface_variant}
  - {text: " $9", weight: 700, color: error}
  - " ends Friday. "
  - {text: "Read the terms", link: terms}
handlers: {on_link: "open_terms(event.href)"}
```

A run is a string, or a mapping with its `text` and any of:

| Key | What it does |
| --- | --- |
| `color` | A theme role or a CSS colour. |
| `weight` | A font weight, 1 to 1000 (`700` is bold). |
| `italic`, `underline`, `strikethrough` | `true` for the style. |
| `font_size`, `font_family` | A size in pixels, a family. |
| `link` | A name for the link; the run is the theme's `primary` and underlined unless it says otherwise. |

`runs` is the text, so a `Text` has `runs` or `text`, not both. The pieces are joined into one text that wraps as one (give it a `width`),
and a string in a run may be an expression (`"{{ was }}"`), so the pieces follow your data. A mistake is refused with the node named: an empty
list, a run with no `text`, an unknown key, a `weight` that is not a number. Only a `Text` has `runs` (a `Link` is one piece, and what is typed in
a `TextInput` is one style).

## Pieces that need their own layout

When the pieces must be separate nodes (each with its own `handlers`, padding or alignment), lay `Text` and `Link` nodes out in a row:

```yaml
widget: Container
style: {flex_direction: horizontal, align_content: left, width: 360, padding: 16, background: surface}
children:
  - widget: Text
    name: was
    text: "$12"
    typography_role: body_large
    style: {foreground: on_surface_variant}
  - widget: Text
    name: now
    text: " $9"
    typography_role: body_large
    font_weight: 700
    style: {foreground: error}
  - widget: Link
    name: terms
    text: Read the terms
    handlers: {on_click: open_terms}
```

Each piece takes its own `typography_role`, `font_size`, `font_family` and `font_weight`, and its own `foreground`. The row keeps
its pieces on one line; for a paragraph that wraps, use one `Text` with `runs` and a `width`.

## Links

`widget: Link` is text that takes focus and that a click or Enter activates. It is the theme's `primary`, underlined
while the pointer is over it or it has the keyboard focus.

| Property | What it does |
| --- | --- |
| `text` | What it says; it also names the link for a screen reader. |
| `href` | A link the OS opens in the browser or mail program when it is activated: `http`, `https`, `mailto` and `tel` only. Anything else is not opened: activating it logs a warning. |
| `visited` | Whether it has been followed. Opening its `href` sets a bound one, and a stylesheet rule with `state: visited` can colour it. |
| `underline` | `hover` (the default), `always` or `never`. |
| `disabled` | Dimmed, out of the Tab order, and does nothing. |

`handlers: {on_click: ...}` runs as well as the `href` opens. A link that goes somewhere inside the app has no `href`, only a
handler; the handler decides what it means:

```yaml
widget: Link
text: Settings
handlers: {on_click: open_settings}
```

To open an address from any other node, a handler calls `open_url('https://example.com')`
([Opening a link](view-language.md#opening-a-link)). The pointer is a hand over a link.

`on_link` is the event of a link run inside one `Text`, with the run's `link` in `event.href`: `handlers: {on_link: "open_terms(event.href)"}`. A handler named
without brackets is called with no event, so write the call to get `event.href`.

## Sizing

A `Text` with no `width` is measured to fit its text on one line. Give it a `width` and it wraps, and is as tall as
its lines. `max_lines` and `overflow: ellipsis` end a long text with an ellipsis; see
[Text in a box](layout.md#text-in-a-box).

## Selectable text

`selectable: true` on a `Text` lets the user select it with the pointer, and copy it with Ctrl+C. Double-click
selects a word, triple-click a line, and a drag from one selectable text into another selects across them. Only a
`Text` can be selectable.

```yaml
widget: Text
name: help
text: Press and drag to select this.
typography_role: body_medium
selectable: true
style: {foreground: on_surface, width: 240}
```

To copy from a handler instead, `copy(text)` puts text on the clipboard ([The clipboard](view-language.md#the-clipboard)).
