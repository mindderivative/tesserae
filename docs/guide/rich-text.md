# Rich Text & Links

A `Text` is one style by default. Give it `runs` instead of `content` and it is one text in several: bold, coloured,
struck through, a different size, or a link.

```yaml
id: root
kind: Container
style: {flex_direction: vertical, gap: 12, padding: 16, width: 360, background: surface}
children:
  - id: price
    kind: Text
    text:
      typography_role: body_large
      runs:
        - "Sale: "
        - {text: "$12", strikethrough: true, color: on_surface_variant}
        - " "
        - {text: "$9", weight: 500, color: error}
        - ", ends Friday. "
        - {text: "Read the terms", link: terms}
    style: {foreground: on_surface}
    handlers: {on_link: open_terms}
```

A run is a string, or a mapping with its `text` and any of:

| Key | What it does |
| --- | --- |
| `color` | A theme role or a CSS colour. |
| `weight` | The font weight. |
| `italic`, `underline`, `strikethrough` | `true` or `false`. |
| `font_size`, `font_family` | A different size or face for the run. |
| `link` | Makes the run a link: a click on it calls `on_link` with `event.href`. |

What a run leaves out stays the `Text`'s own. The text is the runs joined, so give `runs` *or* `content`, not both;
and only a `Text` has runs (a `Link` is one piece, a `TextField` one style).

## Links

A run with a `link` is the theme's `primary` and underlined, unless it says its own `color` or `underline`. The
engine opens nothing: what `href` means is the app's. The handler decides:

```python
class MainViewModel(ViewModel):
    def open_terms(self, event):
        if event.href == "terms":
            self.app.navigate("Terms")
```

The pointer is a hand over a link. For a whole line that is one link, use the `Link` kind.

## Sizing

A `Text` with no `width` is measured to fit its runs on one line, each in its own size and weight. Rich text that
wraps wants a `width`; a bigger `font_size` in a run makes its line taller.

## Selectable text

`selectable: true` in `text:` lets the user select a `Text` with the pointer, and copy it with Ctrl+C. Double-click
selects a word, triple-click a line, and a drag from one selectable text into another selects across them. Only a
`Text` can be selectable.

```yaml
- id: help
  kind: Text
  text: {content: "Press and drag to select this.", typography_role: body_medium, selectable: true}
  style: {foreground: on_surface, width: 240}
```
