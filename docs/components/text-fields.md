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

| Property | Type | Meaning |
| --- | --- | --- |
| `variant` | `filled` or `outlined` | the look; `filled` by default |
| `label` | text | the field's name; it also names the input for a screen reader |
| `text` | text, two-way | what is typed: give it a bare reference and typing writes it |
| `placeholder` | text | shown while the field is empty and has focus (or has no label) |
| `supporting` | text | help under the field |
| `error` | text | an error message: the field takes the error look and the message replaces the supporting text |
| `leading`, `trailing` | icon name | an icon before and after the text; an error replaces the trailing icon |
| `prefix`, `suffix` | text | text around the typing, such as `$` and `USD` |
| `max_length` | whole number | the most characters it takes; `0` is no limit |
| `counter` | true or false | shows how many characters are typed, of `max_length` when there is one |
| `multiline` | true or false | several lines; Enter makes a new one |
| `obscured` | true or false | a password: dots, with a button that shows the text |
| `disabled`, `read_only` | true or false | dimmed and takes no typing; the text can be selected and copied but not changed |
| `suggestions` | a list of texts | those that contain what is typed show in a menu under the field (up to six); pressing one fills the field in; Escape closes the menu |
| `mask` | a pattern | what is typed is fitted to it (`###-####`) |
| `typing_effect` | `none`, `flash` or `fade_in` | what happens to the characters just typed (below); `none` by default |
| `typing_duration` | milliseconds | how long a flash or a fade-in lasts: 260 for a flash and 180 for a fade-in when left out; `0` leaves the effect out |
| `flash_color` | a theme role or colour | what a flash is tinted with (`tertiary`, `#FF8800`, `primary@50%`); the primary colour when left out |
| `flash_opacity` | 0 to 1 | how strong a flash starts: `0.24` when left out |
| `caret_effect` | `none` or `glide` | `glide` draws the caret itself and eases it to each new place (below); `none` by default |
| `glide_duration` | milliseconds | how long the gliding caret takes to reach its new place: `120` when left out; `0` makes it jump |
| `caret_blink` | milliseconds | how long the gliding caret is on, then off: `530` when left out; `0` keeps it solid |
| `on_edit` | a handler | called after each edit, once `text` has been written |

Events: `on_key` for each key pressed in the field, `on_edit` after each edit, and `on_submit` for Enter in a field that is not
multiline. A handler written on the field is called as the user types.

**Typing effects.** `typing_effect: flash` tints the characters just typed with the primary colour and lets the tint fade (about a quarter of a second);
`fade_in` covers them in the background colour and lets that fade, so they seem to appear. Each is drawn exactly over what was inserted (a paste over
several lines gets a piece on each line), from the geometry the engine reports for the edit. The background `fade_in` uses is the first opaque fill going up from the
input, else the theme's `surface`. `caret_effect: glide` hides the engine's caret and draws one of Tesserae's own, which eases to each new place in about an eighth
of a second, stays solid while you type and blinks after a moment, and shows only while the field has the focus. When the app asks for reduced motion there is no
flash and no fade, and the caret jumps and does not blink. Neither takes the pointer or appears to a screen reader. The looks above are each the field's own to set (a number below `0`, or a strength outside `0` to `1`, is an
error that names the property and the line); the easing is not settable.

The parts a stylesheet can address are `box`, `label`, `input`, `prefix`, `suffix`, `leading_icon`, `trailing_icon`, `error_icon`,
`reveal_button`, `reveal_icon`, `indicator` (the line under a filled field), `supporting` and `counter`. The state of a rule is the state of
the whole field: `focused` is true while anything inside it has the focus, `hovered` while the pointer is over it, and `error` and
`disabled` read the field's own properties. The label glides between its two places (its position eases in 150 milliseconds; its size changes at once, as the
engine cannot ease a font size). A filled field has 4 pixel top corners and a square bottom, over its line. The input says it is described by the help line, so a
screen reader reads that too, and it is invalid while there is an error. Not built: moving into the suggestions with the arrow keys (press one with the pointer), the input method's
composition drawn by Tesserae (the engine draws the candidate window at the caret), and an exposed dropdown that is a select.

This component is a view Tesserae ships: use `widget: TextField` in a view (see [The View Language](../guide/view-language.md)).

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
`read_only`, `disabled`, `mask`, `typing_effect` and `caret_effect`, drawn as one line that scrolls.

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

A view named `TextField_View.yaml` in your project replaces the shipped field, and its shipped look with it. In a view written with `kind:`,
`kind: TextField` is the bare input (the `TextInput` widget), with `text: {placeholder, multiline, obscured}` for those three;
`tesserae migrate-yaml` turns it into `widget: TextInput`.

## See also

- [View Language](../guide/view-language.md)
- [Bindings](../guide/bindings.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
