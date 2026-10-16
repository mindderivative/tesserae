# Text fields

*Selection and input*

## In Material Design 3

A text field lets people enter and edit text. Material Design 3 has two kinds: a **filled** field, a tinted container with a line under
it, and an **outlined** one, a field with a border. The label is the field's name: it sits in the middle as a hint and moves up, smaller,
when the field has focus or text. Supporting text, a character counter, icons before and after, and an error state with its message
belong to the field.

## In Tesserae

`widget: TextField` is a view Tesserae ships (`TextField_View.yaml`) with its look as rules (`TextField_Stylesheet.yaml`). It is built from
the `TextInput` widget, the bare input, and the nodes around it, so every part has a name a stylesheet can address.

`text` is two-way: give it a bare reference and typing writes it. `placeholder` shows while the field is empty and has focus (or has no label). `supporting` is help under the
field, and `error` is a message that gives the field the error look and replaces the supporting text. `leading` and `trailing` are icons (an error replaces the trailing one),
`prefix` and `suffix` are text around the typing, such as `$` and `USD`, and `counter` shows how many characters are typed, of `max_length` when there is one (`0` is no limit).
`multiline` makes Enter start a new line; `obscured` makes a password (dots, with a button that shows the text); `read_only` lets the text be selected and copied but not
changed. `mask` fits what is typed to a pattern (`###-####`: `#` a digit, `A` a letter, `*` either, `\` a literal). `suggestions` is a list of texts: those that contain
what is typed show in a menu under the field (up to six), pressing one fills the field in, and Escape closes the menu.

Events: `on_key` for each key pressed in the field, `on_edit` after each edit (once `text` has been written), and `on_submit` for Enter in a field that is not
multiline.

**Typing effects.** `typing_effect: flash` tints the characters just typed with the primary colour and lets the tint fade (about a quarter of a second);
`fade_in` covers them in the background colour and lets that fade, so they seem to appear. Each is drawn exactly over what was inserted (a paste over
several lines gets a piece on each line), from the geometry the engine reports for the edit. The background `fade_in` uses is the first opaque fill going up from the
input, else the theme's `surface`. `caret_effect: glide` hides the engine's caret and draws one of Tesserae's own, which eases to each new place in about an eighth
of a second, stays solid while you type and blinks after a moment, and shows only while the field has the focus. When the app asks for reduced motion there is no
flash and no fade, and the caret jumps and does not blink. Neither takes the pointer or appears to a screen reader.

Five more properties tune them, each the field's own to set. `typing_duration` is how long a flash or a fade-in lasts, in milliseconds (260 for a flash and 180 for a fade-in
when left out; `0` leaves the effect out). `flash_color` is what a flash is tinted with: a theme role or a colour (`tertiary`, `#FF8800`, `primary@50%`), the primary colour
when left out. `flash_opacity` is how strong a flash starts, `0` to `1` (`0.24` when left out). `glide_duration` is how long the gliding caret takes to reach its new place
(`120` when left out; `0` makes it jump), and `caret_blink` is how long it is on, then off (`530` when left out; `0` keeps it solid). A number below `0`, or a strength outside
`0` to `1`, is an error that names the property and the line. The easing is not settable.

The parts a stylesheet can address are `box`, `label`, `input`, `prefix`, `suffix`, `leading_icon`, `trailing_icon`, `error_icon`,
`reveal_button`, `reveal_icon`, `indicator` (the line under a filled field), `supporting` and `counter`. The state of a rule is the state of
the whole field: `focused` is true while anything inside it has the focus, `hovered` while the pointer is over it, and `error` and
`disabled` read the field's own properties. The label glides between its two places (its position eases in 150 milliseconds; its size changes at once, as the
engine cannot ease a font size). A filled field has 4 pixel top corners and a square bottom, over its line. The input says it is described by the help line, so a
screen reader reads that too, and it is invalid while there is an error. Not built: moving into the suggestions with the arrow keys (press one with the pointer), the input method's
composition drawn by Tesserae (the engine draws the candidate window at the caret), and an exposed dropdown that is a select.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: TextField`. A file of the same name in your project replaces it.

### `TextField`

The Material 3 text field: a labelled box around a text input, with an optional leading icon, prefix, suffix, trailing icon, supporting text, character counter and an error state. `variant: filled | outlined`. What it looks like is in TextField_Stylesheet.yaml; this file is its structure. `text` is two-way: give it a bare reference (`text: "{{ query }}"`) and typing writes `query`. The label is raised (small, at the top) while the field has focus or text, and sits in the middle as a hint otherwise; it glides between the two (`transition:` on its position).

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `variant` | `filled` or `outlined` | `filled` | filled has a fill and a line under it; outlined has a border. |
| `label` | `str` |  | The field's name; it also names the field for a screen reader. |
| `text` | `str` |  | What the user has typed. Two-way: give it a bare reference and the view writes it back. |
| `placeholder` | `str` |  | Shown while the field is empty and focused (or has no label). |
| `supporting` | `str` |  | Help under the field. |
| `error` | `str` |  | An error message. When it is not empty the field shows the error look and the message replaces the supporting text. |
| `leading` | `str` |  | A built-in icon name shown before the text. |
| `trailing` | `str` |  | A built-in icon name shown after the text. |
| `prefix` | `str` |  | Text before the typing, such as a currency sign. |
| `suffix` | `str` |  | Text after the typing, such as a unit. |
| `max_length` | `int` | `0` | The most characters it takes; 0 is no limit. |
| `typing_effect` | `none` or `flash` or `fade_in` | `none` | What happens to the characters just typed: flash tints them for a moment; fade_in fades them in. Left out when the app asks for reduced motion. |
| `typing_duration` | `float`, 0 or more |  | How long a flash or a fade-in lasts, in milliseconds: 260 for a flash and 180 for a fade-in when left out; 0 leaves the effect out. |
| `flash_color` | `color` |  | What a flash is tinted with: a theme role or a colour; the primary colour when left out. |
| `flash_opacity` | `float`, 0 to 1 |  | How strong a flash starts, from 0 to 1: 0.24 when left out. |
| `glide_duration` | `float`, 0 or more |  | How long the gliding caret takes to reach its new place, in milliseconds: 120 when left out; 0 makes it jump. |
| `caret_blink` | `float`, 0 or more |  | The time the gliding caret is on and then off, in milliseconds: 530 when left out; 0 keeps it solid. |
| `caret_effect` | `none` or `glide` | `none` | glide draws the caret itself and eases it to each new place. It jumps, and does not blink, when the app asks for reduced motion. |
| `mask` | `mask` |  | A pattern the typing is put in: # a digit, A a letter, * either, \ a literal; other characters come by themselves, as in (###) ###-####. |
| `counter` | `bool` | `false` | Shows how many characters are typed (of max_length, when there is one). |
| `multiline` | `bool` | `false` | Several lines; Enter makes a new one, so on_submit does not fire. |
| `obscured` | `bool` | `false` | A password: dots instead of the text, with a button that shows it. |
| `disabled` | `bool` | `false` | Dimmed, and takes no typing. |
| `read_only` | `bool` | `false` | The text can be selected and copied but not changed. |
| `on_edit` | `handler` |  | Called after each edit the user makes, once `text` has been written. |
| `suggestions` | `list` | `[]` | Texts to offer while typing: those that contain what is typed show in a menu under the field, and pressing one fills it in. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `offers` (Menu), `box` (Container), `leading_icon` (Icon), `body` (Container), `prefix` (Text), `input` (TextInput), `suffix` (Text), `error_icon` (Icon), `trailing_icon` (Icon), `reveal_button` (Rect), `reveal_icon` (Icon), `label_box` (Container), `label` (Text), `indicator` (Rect), `footer` (Container), `supporting` (Text), `counter` (Text).

Its look is in [`TextField_Stylesheet.yaml`](../stylesheets/text-fields/text-field.md).

### `TextInput`

A bare text input (the part of a TextField that takes the typing).

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `text` | `str` |  | What the user has typed. Two-way. |
| `placeholder` | `str` |  | Shown, dimmed, while the field is empty. |
| `multiline` | `bool` |  | Several lines; Enter makes a new one. |
| `obscured` | `bool` |  | Shows dots instead of the text, and blocks copy and cut (a password). |
| `max_length` | `int` |  | The most characters it takes; 0 is no limit. |
| `read_only` | `bool` |  | The text can be selected and copied but not changed. |
| `mask` | `mask` |  | A pattern the typed text is put in: # a digit, A a letter, * either, \ a literal; other characters come by themselves. |
| `typing_effect` | `none` or `flash` or `fade_in` | `none` | What happens to the characters just typed: `flash` tints them with the primary colour for a moment; `fade_in` fades them in out of the background. |
| `typing_duration` | `float`, 0 or more |  | How long a flash or a fade-in lasts, in milliseconds: 260 for a flash and 180 for a fade-in when left out; 0 leaves the effect out. |
| `flash_color` | `color` |  | What a flash is tinted with: a theme role or a colour (`primary@50%` works); the primary colour when left out. |
| `flash_opacity` | `float`, 0 to 1 |  | How strong a flash starts, from 0 to 1: 0.24 when left out. |
| `caret_effect` | `none` or `glide` | `none` | `glide` draws the caret itself and eases it to each new place; it blinks, solid while typing. The engine's caret is hidden meanwhile. |
| `glide_duration` | `float`, 0 or more |  | How long the caret takes to reach its new place, in milliseconds: 120 when left out; 0 makes it jump. |
| `caret_blink` | `float`, 0 or more |  | The time the gliding caret is on and then off, in milliseconds: 530 when left out; 0 keeps it solid. |
| `typography_role` | `str` |  |  |
| `font_family` | `str` |  |  |
| `font_size` | `float` |  |  |
| `font_weight` | `any` |  |  |
| `disabled` | `bool` |  |  |

Its `style:` also takes `foreground`.

## Using it

```yaml
name: signup
widget: Container
style: {flex_direction: vertical, width: 360, height: 420, gap: 16, padding: 16}
children:
  - widget: TextField
    name: email
    label: Email
    leading: search
    text: "{{ email }}"
    error: "{{ email_error }}"
    supporting: We never share it
    handlers: {on_submit: sign_up}
  - widget: TextField
    name: password
    variant: outlined
    label: Password
    obscured: true
    text: "{{ password }}"
  - widget: TextField
    name: bio
    label: About you
    multiline: true
    max_length: 140
    counter: true
    text: "{{ bio }}"
```

`TextInput` is the bare input, for when the field around it is your own: `text`, `placeholder`, `multiline`, `obscured`, `max_length`,
`read_only`, `disabled`, `mask`, the typing and caret effects above (`typing_effect`, `caret_effect` and the five that tune them) and the font (`typography_role`,
`font_family`, `font_size`, `font_weight`); its colour is `style.foreground`.

## Changing its look

Write rules for `TextField` in your app's stylesheet; they sit above the shipped ones, and a `style:` on the node beats every rule for the
fields it sets.

```yaml
styles:
  - widget: TextField
    part: box
    variant: filled
    style: {background: surface_container_high, corner_radius: 12}
  - widget: TextField
    part: indicator
    state: focused
    style: {background: tertiary}
```

A view named `TextField_View.yaml` in your project replaces the shipped field, and its shipped look with it.

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# TextField_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: TextField
    part: box
    variant: filled
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [View Language](../guide/view-language.md)
- [Bindings](../guide/bindings.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
