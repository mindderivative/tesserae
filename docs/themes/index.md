# Themes

A theme decides how an app looks as a whole: its colours, its type, and the shapes
and shadows of its components. A stylesheet holds the style rules you add. This page
says what a theme is made of, how Tesserae applies one with a stylesheet, how to change each
part, and ends with the complete API.

## What a theme is

| Thing | Scope | Lives in | Set with |
| --- | --- | --- | --- |
| **Theme** | the whole app | `*_Theme.yaml` | `App(custom_theme=)` |
| **Stylesheet** | every view of the app | `*_Stylesheet.yaml` | `App(stylesheet=)` |
| **Shipped rules** | one view Tesserae ships | `<Name>_Stylesheet.yaml` in the package | a rule of your own goes over them: [Component Stylesheets](../stylesheets/index.md) |
| **Style** | one node | `style:` | the node |

A theme file holds the palette, the type and the shapes. Every key is optional:

```yaml
# Brand_Theme.yaml
seed: "#0B6B58"              # the colour the whole palette is made from
dark: false                  # whether the theme is the dark scheme (the app decides: see below)
colors:                      # roles to replace, after the palette is made
  tertiary: "#C2410C"
typography:                  # changes to MD3's type styles
  body_large: {font_family: Inter, font_size: 17}
components:                  # the shape and elevation of widgets made in Python
  card.elevated: {corner_radius: 8, elevation: level_2}
```

A stylesheet has only `styles:`. The keys are listed in the [YAML reference](../api/yaml.md#theme-and-stylesheet).
Rules are written in a stylesheet, not a theme: a theme's own `styles:` list is read in the older rule shape (`kind`,
`classes`, `id`) and is not how a view in the current language is styled.

## How a node gets its style

A node's style is built from layers, lowest first. A later layer changes only the fields it mentions:

1. the **shipped rules** of the view or widget (Tesserae's own look for a `Button`, a `Card`, and so on);
2. the app's **stylesheet**;
3. the node's own **`style:`**.

A stylesheet is a list of rules. A rule names a `widget` (a built-in or a view, yours or Tesserae's) and may narrow it:

```yaml
# Notes_Stylesheet.yaml
styles:
  - widget: Container
    style: {padding: 12}                              # every Container
  - widget: Container
    classes: [panel]
    style: {background: surface_container_high}       # a Container with the class `panel`
  - widget: Text
    name: title
    style: {foreground: primary}                      # the node named `title`
  - widget: Button
    variant: filled
    style: {background: tertiary}                     # a property the widget declares
  - widget: Button
    variant: filled
    part: label
    style: {foreground: on_tertiary}                  # a named node inside the widget
  - widget: Button
    state: hovered
    style: {elevation: 2}                             # while the pointer is over it
```

A rule may narrow by `variant`, `size` and `shape` (properties the widget declares), `classes`, `name`, a `part` (a node of the
widget's own view, named in its stylesheet page) and a `state` (`hovered`, `focused`, `focus_visible`, `pressed`, `disabled`, `selected`, `checked`,
`expanded`, `error`, `read_only`, `visited`). The most specific rule wins: a `name`, then how many of `variant`, `size`, `shape` and
`classes` it names, then a `state`, then the widget alone; a later rule wins a tie. A node's own `style:` beats every rule, for the
fields it sets and no others, and a value in a rule may be an expression over the widget's properties (`"{{ height / 2 }}"`).

A built-in view's look is its shipped rules, so restyling a part everywhere is a rule of your own with the same `widget` and `part`
in the app's stylesheet. See [Component Stylesheets](../stylesheets/index.md) for each widget's parts, and
[The View Language](../guide/view-language.md#style) for the rest.

## Colour

### From a seed

A theme's colours are made from one colour, the **seed**, by Material Design
3's algorithm: it builds a tonal palette and picks 49 named **roles** from it
(`primary`, `on_primary`, `surface`, `surface_container_high`, ...), once for
light and once for dark. The seed is the first of these that is set:

1. `App(theme_seed=(r, g, b, a))`;
2. the custom theme's `seed:`;
3. the default theme's `seed:`.

Then `colors:` replaces roles: the default theme's, then the custom theme's.

```python
app = App(theme_seed=(0x0B, 0x6B, 0x58, 0xFF), custom_theme="themes/Brand_Theme.yaml")
```

Anywhere a view takes a colour, the role's name works: `background: surface`.

### With no theme

An app with no seed at all still resolves roles, from MD3's baseline palette
(the purple one). A `theme_seed=` is what makes the colours your own and lets
them follow the OS's light and dark. A role that doesn't exist, or is
misspelt, is an error that says so: `unknown color identifier -- did you mean
'surface'?`

### Colour values

Anywhere a view, stylesheet or theme takes a colour, it takes a string:

- hex: `#RGB`, `#RGBA`, `#RRGGBB` or `#RRGGBBAA`;
- a CSS colour name, or `transparent`;
- `rgb()`, `rgba()`, `hsl()` and `hsla()`, with commas or spaces and an optional alpha;
- CSS Color 4's `oklch()`, `oklab()`, `lch()`, `lab()`, `hwb()`, and `color()` in `srgb`,
  `srgb-linear`, `display-p3`, `a98-rgb`, `prophoto-rgb`, `rec2020`, `xyz`, `xyz-d50` or `xyz-d65`.

```yaml
style:
  background: "oklch(62.8% 0.2577 29.23)"   # sRGB red
  foreground: "color(display-p3 0.2 0.3 0.1)"
```

Any of these, and any theme role, may end in `@N%` to scale its alpha: `primary@12%` is the primary colour at 12% (a state layer's
tint), `on_surface@38%` is disabled content, `"#6750A4@50%"` half of a hex colour, and a colour that already has alpha keeps that fraction
of it. The percentage is 0 to 100.

```yaml
style:
  background: primary@12%
  border_color: on_surface@38%
```

Tesserae renders in sRGB, so a colour outside it is clipped channel by channel. A colour's own
alpha renders (`"#FFFFFF80"` is half-transparent white), and `opacity:` fades a node and everything
in it as one layer; to dim a background without dimming what sits on it, put the transparency in the
colour. The built-in `Dialog` and `SideSheetModal` scrims do this, so a theme's `colors: {scrim: ...}`
doesn't reach them.

## Light and dark

An `App` follows the OS by default (`dark="system"`): when the OS switches, every screen, widget,
control, overlay and the window's frame switch with it, in place. On Linux the starting appearance is known at
once, from the desktop's settings portal; on macOS and Windows it is known once the window opens, so
the app starts dark and switches on the first frame if the OS is light. Headless, it starts dark.

```python
app = App(theme_seed=(0x67, 0x50, 0xA4, 0xFF))   # follows the OS, from the start
app.set_dark(False)                               # light from now on
app.set_dark("system")                            # back to following the OS
```

Pass `dark=True` or `dark=False` to fix it. A widget made on the app's window with no `theme=` follows
the app; an explicit `theme=` pins it to that theme.

### Contrast and motion

The OS can also ask for more contrast and for less motion, and an app follows both by default.
`App(high_contrast="system")` takes MD3's highest-contrast colours when the OS asks for them, and
`App(reduced_motion="system")` makes animations take no time when it asks for that. Pass `True` or `False` to fix
either, or change them while the app runs:

```python
app = App(theme_seed=(0x67, 0x50, 0xA4, 0xFF), high_contrast=False, reduced_motion="system")
app.set_high_contrast(True)       # every screen re-themed in place
app.set_reduced_motion("system")  # back to following the OS
app.high_contrast, app.reduced_motion    # what is in force now
```

The look of a press and of keyboard focus is the app's too: `App(ripple="shader")` draws every ripple with one shader
instead of a circle node per press, and `App(focus_ring="gradient")` turns a gradient around the focus ring
instead of the solid one.

## Shape and elevation

A view's shape and elevation are style: `corner_radius` and `elevation` in a rule or a node's `style:`, a number or one of MD3's
tokens. To change a widget's everywhere, write a rule for it in the app's stylesheet:

```yaml
styles:
  - {widget: Card, variant: elevated, style: {corner_radius: 4, elevation: 5}}
  - {widget: Dialog, style: {corner_radius: small}}
  - {widget: Fab, variant: surface, style: {corner_radius: 8}}
```

Shapes are `none`, `extra_small`, `small`, `medium`, `large`, `extra_large` and `full` (a pill or a circle: half the node's
shorter side), or a number; an elevation is a level from 0 to 5.

A theme's `components:` sets the corner radius and elevation of a widget made in Python with `tesserae.widgets`,
by MD3 component and variant. It is not read by a view written in YAML, which takes its shape from its rules.

```yaml
components:
  card.elevated: {corner_radius: 4, elevation: level_5}
  dialog: {corner_radius: small}
  fab.small: {corner_radius: 8}
```

```python
from tesserae.widgets import card

card(app.window, 200, 120, variant="elevated")     # corner radius 4, from the theme
```

A widget's entry for its variant (`card.elevated`) is read, then its component's (`card`), over the widget's own values. A FAB's
variant is its size (`fab.small`, `fab.default`, `fab.large`). A custom theme's entry for a key replaces the default's.

## Type

A theme's `typography:` overrides fields of MD3's 15 type roles
(`display_large` to `label_small`):

```yaml
typography:
  body_large: {font_family: Inter, font_size: 17}
  title_medium: {font_weight: 600}
```

A `Text` or `Link` with `typography_role: body_large` takes the theme's `body_large`; fields the node
sets itself still win. A custom theme's entry for a role replaces the default's, rather than merging
with it. Widgets follow it too. Text inputs don't: a `TextInput` keeps its own font, so typed text isn't
restyled by the theme.

### Fonts

Three families are bundled and always available: **Roboto**, **Noto Sans Arabic** and **Hack Nerd Font
Mono**. Tesserae does not look at the system's fonts unless you ask (`App(system_fonts=True)` lets text fall back to
installed fonts for scripts the bundled ones lack, such as CJK and colour emoji), so by default text looks the same on every
machine. To use any other family, register its file first:

```python
import tesserae

tesserae.register_font("fonts/Inter-Regular.ttf")  # -> ["Inter"]
```

The return value is the family name to use as `font_family`. Naming a family that is neither bundled nor
registered draws a bundled face in its place, and Tesserae warns, naming the file and the family
(`tesserae.fonts.FontFallbackWarning`; turn it into an error with `warnings.filterwarnings("error", ...)`).

## Making a change

| To change... | Do this |
| --- | --- |
| the app's colours | `App(theme_seed=...)`, or `seed:` in a theme |
| one colour role | `colors:` in a theme |
| every view's look | `App(stylesheet=...)`: rules |
| one kind of widget, a variant of it, or a part of it | a rule for the `widget`, with `variant`, `part` or `state`, in the stylesheet |
| one view or a few nodes | `classes:` on the nodes and a rule for them; or a rule for the view's name |
| a widget's shape or shadow | `corner_radius` and `elevation` in a rule (`components:` in a theme is for widgets made in Python) |
| the type | `typography:` in a theme, and [fonts](#fonts) |
| one node | its `style:` |

An app has one stylesheet, and every view it opens uses it.

### While the app runs

`app.set_theme_specs(default, custom)` re-themes every view the app opened, and the window, in one
call. Both dicts are the complete new selection (`None` for none); the seed and the light or dark
appearance stay as they are. With `run(hot_reload=True)`, saving a theme file does this for you.
A stylesheet of rules is read when the app is made: change it and run the app again.

```python
from tesserae.spec import load_theme

app.set_theme_specs(None, load_theme("themes/Dark_Theme.yaml"))
```

### Reading the theme from code

```python
theme = app.theme                      # a tesserae.Theme
theme.role("primary")                  # (r, g, b, a)
theme.shape("card", "elevated")        # components: card.elevated, then card
theme.elevation("dialog")              # an MD3 elevation level, or None
theme.typography("body_large")         # the type role, with typography: overrides
theme.easing("emphasized_decelerate")  # (x1, y1, x2, y2), for node.animate(easing=...)
theme.duration("medium2")              # 300 (ms)
```

`shape` and `elevation` return `None` when the theme's `components:` doesn't mention the component, and
the widget uses its own MD3 default. MD3's easing and duration tokens are all there; `emphasized` is MD3's
single-curve form, `(0.2, 0, 0, 1)`.

### Style files

A `*_Style.yaml` file holds one node's `style:` (its fields under a `style:` key, and an optional `id:`), and a node of a view in
the older syntax can name it (`style: row_Style.yaml`) so several nodes share it. A view in the current language does not apply
one: write the fields in `style:`, or in a rule that several nodes match through a class or a widget name.

### Files and checking

`load_theme` and `load_stylesheet` read a file into the dict the app takes; `App(custom_theme=)` and `App(stylesheet=)` do it for you,
and each also has a `*_spec=` form that takes a dict directly (`custom_theme_spec={"colors": {"primary": "#00FF00"}}`). Give one
form or the other. A mistake in a theme or stylesheet names the file:
`ValueError: themes/Brand_Theme.yaml: custom_theme_spec=: unknown field 'colours'`.

## How it is implemented

- **Resolving.** `Theme.resolve(seed, dark, default_theme_spec, custom_theme_spec)` turns the four inputs
  into one `Theme`: the role table (`tokens.resolve_scheme`), the `components:` map, the type scale and the
  motion tokens. `app.theme` and `view.theme` return one.
- **Applying.** A view is built by Tesserae's own compiler: for each node it merges the layers
  (above), resolves colour roles against the scheme, and sets the result on the node. `view.set_theme`
  runs the same pass again over the nodes already built, in place, so a theme change never rebuilds a view.
- **Following.** `tesserae.follow` keeps the widgets, controls and overlays made on an app's window
  without a `theme=`. When the app's theme or appearance changes (including the OS switching) it re-themes
  them with the app's views.
- **Files.** Tesserae reads theme and stylesheet files itself and hands the engine only data, as for views
  and images. `*_Theme.yaml` and `*_Stylesheet.yaml` say what a file is, and a file named
  for one kind is refused by the loader of another.

## The complete API

<!-- api:begin (written by tools/generate_api_docs.py) -->

### On the app

- `App.theme` *(property)*: The app's resolved theme (`tesserae.Theme`): roles, component shape and elevation, typography, and motion tokens.
- `App.dark` *(property)*: Whether the app is showing its dark scheme right now.
- `App.dark_mode` *(property)*: `"system"` (following the OS), or the app's fixed `True`/`False`.
- `App.set_dark(dark: bool | str) -> None`: `True`/`False` fixes the app dark or light, re-theming every screen in place; `"system"` goes back to following the OS from its next switch.
- `App.set_theme_specs(default_theme_spec: Any, custom_theme_spec: Any) -> None`: Re-themes the running app in place: every view `build_view()`/`load()` made.
- `App.set_stylesheet_spec(stylesheet_spec: dict[str, Any] | None) -> None`: Replaces the app's default stylesheet in place: every view `build_view()`/`load()` made with the default -- not one given its own `stylesheet=` -- is re-styled, and views built later use it too.
- `App.build_view(view_path: str | Path, *, stylesheet: str | Path | None = None, stylesheet_spec: dict[str, Any] | None = None) -> Any`: Builds a view with this app's theme and stylesheet, without registering it -- for a screen given to `register()`, e.g. one whose `ViewModel` needs the `app` itself.

### On a view

- `View.theme` *(property)*: This view's resolved theme (`tesserae.Theme`).
- `View.set_theme(theme_seed: Optional[tuple[int, int, int, int]] = None, dark: bool = False, default_theme_spec: Optional[dict[str, Any]] = None, custom_theme_spec: Optional[dict[str, Any]] = None, contrast: float = 0.0) -> None`: Re-themes every node in place.
- `View.set_stylesheet(stylesheet_spec: Optional[dict[str, Any]] = None) -> None`: Replaces the stylesheet and re-styles every node in place; `None` clears it.

### `Theme`

```python
class Theme(
    seed: Optional[RGBA],
    dark: bool,
    roles: Optional[dict[str, RGBA]],
    components: dict[str, _Component] = <factory>,
    type_overrides: dict[str, dict[str, Any]] = <factory>,
    contrast: float = 0.0
) -> None
```

A resolved theme. Build one with `Theme.resolve(...)`.

- `duration(name: str) -> int`: An MD3 duration token, in milliseconds.
- `easing(name: str) -> Easing`: An MD3 easing token, as `animate(easing=...)` takes it.
- `elevation(component: str, variant: Optional[str] = None) -> Optional[float]`: A component's elevation level from `components:`, or `None`.
- `is_set` *(property)*: Whether there's a colour scheme (a seed was given somewhere).
- `resolve(theme_seed: Optional[RGBA] = None, dark: bool = False, default_theme_spec: Optional[dict[str, Any]] = None, custom_theme_spec: Optional[dict[str, Any]] = None, contrast: float = 0.0) -> 'Theme'`: Resolves a theme; raises `ValueError` for an unknown role, an unknown token in `components:` or an unknown `typography:` field.
- `role(name: str) -> Optional[RGBA]`: An MD3 colour role, or `None` without a scheme or for an unknown name.
- `shape(component: str, variant: Optional[str] = None) -> Optional[float]`: A component's corner radius from `components:`, or `None` when the theme doesn't say (the widget uses its own MD3 default).
- `spring(bounce: float = 0.0) -> Easing`: A spring easing: `bounce` from -1 to 1 (exclusive), 0 settling without overshoot, above 0 overshooting.
- `typography(role: str) -> Optional[tokens.TypeStyle]`: An MD3 type role with the theme's `typography:` overrides, or `None` for an unknown role.

### Loading files

- `load_theme(path: str | Path) -> dict[str, Any]`: Reads a theme YAML file into the dict `tre`'s `default_theme_spec=`/`custom_theme_spec=` take, for `load_view` or for switching themes later:
- `load_stylesheet(path: str | Path) -> dict[str, Any]`: Reads a stylesheet YAML file into the dict `tre`'s `stylesheet_spec=` takes.

### Tokens

`tesserae.tokens`: Material Design 3's tokens as Python values.

- `shape(name: str) -> Optional[float]`: The corner radius of the MD3 shape token `name` (`"small"`, `"medium"`, ...
- `elevation(name: str) -> Optional[float]`: The level (0 to 5) of the MD3 elevation token `name`, or `None` if it isn't one.
- `type_style(role: str) -> Optional[TypeStyle]`: The font size, weight, line height and tracking of the MD3 type role `role`, or `None` if it isn't one.
- `color_scheme(seed: RGBA, dark: bool = False, contrast: float = 0.0) -> dict[str, RGBA]`: Every MD3 role for `seed`, light or dark.
- `baseline_scheme() -> dict[str, RGBA]`: Every role, for widgets with no theme: the scheme MD3's baseline seed (#6750A4) generates, with MD3's published `BASELINE` values over it where they differ.
- `resolve_scheme(theme_seed: Optional[RGBA], dark: bool, default_theme: Optional[dict[str, Any]], custom_theme: Optional[dict[str, Any]], contrast: float = 0.0) -> Optional[dict[str, RGBA]]`: The scheme a view resolves roles against, by `tre`'s `View` rules: the seed is `theme_seed`, else the custom theme's `seed:`, else the default theme's; `colors:` overrides apply default theme first, then custom.
- `parse_color(raw: str) -> RGBA`: A colour string as `tre` parses it: hex (`#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`), a CSS colour name, `transparent`, or `rgb()`/`rgba()`/`hsl()`/`hsla()` in CSS Color 4's comma or space syntax with an optional alpha, and CSS's wide-gamut functions (`color()`, `lab()`, `lch()`, `oklab()`, `oklch()`, `hwb()`), clipped into sRGB.
- `elevation_shadows(level: float) -> list[Shadow]`: MD3 elevation `level` (0–5, fractional allowed) as a `shadows` list, `(color, offset_x, offset_y, blur, spread)`: `tre`'s key shadow (30% black) first, so it paints on top, then its ambient shadow (15%).

- `tokens.ROLES` = `tuple of 49`
- `tokens.SHAPES` = `dict of 6`
- `tokens.ELEVATION_LEVELS` = `dict of 6`
- `tokens.TYPE_SCALE` = `dict of 15`
- `tokens.BASELINE` = `dict of 24`
### Fonts

- `register_font(path: str | Path) -> list[str]`: Reads the font file at `path` and registers it with `tre`, process-wide.
- `available_families() -> frozenset[str]`: Every family `tre` can draw right now: its bundled ones plus any registered through `register_font`.
- `FontFallbackWarning`: A `font_family` names a family that isn't bundled with `tre` and hasn't been registered, so `tre` will draw a bundled face instead.
- `BUNDLED_FAMILIES` = `['Hack Nerd Font Mono', 'Noto Sans Arabic', 'Roboto']`

<!-- api:end -->
