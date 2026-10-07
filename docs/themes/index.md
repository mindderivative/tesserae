# Themes

A theme decides how an app looks as a whole: its colours, the shapes and
shadows of its components, its type, and any style rules you add. This page
says what a theme is made of, how Tesserae applies one, how to change each
part, and ends with the complete API.

## What a theme is

| Thing | Scope | Lives in | Set with |
| --- | --- | --- | --- |
| **Theme** | the whole app | `*_Theme.yaml` | `App(custom_theme=)` |
| **Stylesheet** | one view, or every view by default | `*_Stylesheet.yaml` | `App(stylesheet=)`, `app.load(..., stylesheet=)` |
| **Component stylesheet** | one built-in component | `<Name>_Stylesheet.yaml` | next to your views: [Component Stylesheets](../stylesheets/index.md) |
| **Style** | one node | `style:` or `*_Style.yaml` | the node |

A theme file can hold everything:

```yaml
# Brand_Theme.yaml
seed: "#0B6B58"              # the colour the whole palette is made from
dark: false                  # whether the theme is the dark scheme (the app decides: see below)
colors:                      # roles to replace, after the palette is made
  tertiary: "#C2410C"
typography:                  # changes to MD3's type styles
  body_large: {font_family: Inter, font_size: 17}
components:                  # the shape and elevation of components
  card.elevated: {corner_radius: 8, elevation: level_2}
styles:                      # style rules, as in a stylesheet
  - {kind: Rect, classes: [panel], style: {background: surface_container_high}}
```

Every key is optional. A stylesheet has only `styles:`. The keys are listed in
the [YAML reference](../api/yaml.md#theme-and-stylesheet).

## How a node gets its style

A node's style is built from four layers, lowest first. A later layer
changes only the fields it mentions:

1. the **default theme's** `styles:` (Tesserae's own, which gives a few kinds their shape);
2. the **custom theme's** `styles:`;
3. the view's **stylesheet**;
4. the node's own **`style:`**.

Inside a layer, rules apply from the general to the specific: a rule with no
selector, then rules matching the node's `kind:`, then rules whose `classes:`
the node has all of (fewer classes first), then a rule matching its `id:`.
Rules of the same kind apply in the order written.

```yaml
# Notes_Stylesheet.yaml
styles:
  - style: {gap: 8}                                   # every node
  - {kind: Container, style: {padding: 12}}           # every Container
  - {classes: [panel], style: {background: surface_container_high}}
  - {id: title, style: {foreground: primary}}         # one node
```

A built-in component's own look is part of the node's `style:` (layer 4): its
[component stylesheet](../stylesheets/index.md) is merged under whatever the
fragment sets itself, which is why a view's stylesheet doesn't restyle a
component's parts. Give the component call a `classes:` and style that, or restyle
the component with a stylesheet of its own.

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

Tesserae renders in sRGB, so a colour outside it is clipped channel by channel. A colour's own
alpha renders (`"#FFFFFF80"` is half-transparent white), and `opacity:` fades a node and everything
in it as one layer; to dim a background without dimming what sits on it, put the transparency in the
colour. The built-in `Dialog` and `SideSheetModal` scrims do this, so a theme's `colors: {scrim: ...}`
doesn't reach them.

## Light and dark

An `App` follows the OS by default (`dark="system"`): when the OS switches, every screen, widget,
control, overlay and the shell switch with it, in place. On Linux the starting appearance is known at
once, from the desktop's settings portal; on macOS and Windows it is known once the window opens, so
the app starts dark and switches on the first frame if the OS is light. Headless, it starts dark.

```python
app = App(theme_seed=(0x67, 0x50, 0xA4, 0xFF))   # follows the OS, from the start
app.set_dark(False)                               # light from now on
app.set_dark("system")                            # back to following the OS
```

Pass `dark=True` or `dark=False` to fix it. A widget made on the app's window with no `theme=` follows
the app; an explicit `theme=` pins it to that theme.

## Shape and elevation

A theme's `components:` sets a component's corner radius and elevation, by MD3 component and variant:

```yaml
components:
  card.elevated: {corner_radius: 4, elevation: level_5}
  dialog: {corner_radius: small}
  fab.small: {corner_radius: 8}
```

It shapes widgets from `tesserae.widgets` and `component:` fragments in views alike. A fragment's root
reads the entry for its variant (`card.elevated`), then its component's (`card`), over its own values.
Fragment names map as `CardElevated` to `card.elevated`, `ButtonFilledTonal` to `button.filled_tonal`,
`SideSheetModal` to `side_sheet.modal` and `Dialog` to `dialog`. A FAB's variant is its size
(`fab.small`, `fab.default`, `fab.large`). Values are numbers or MD3's tokens: shapes `none`,
`extra_small`, `small`, `medium`, `large`, `extra_large`, and elevations `level_0` to `level_5`.

Tesserae's default theme has entries for MD3's own shapes. A custom theme's entry for a key replaces the
default's. Buttons, icon buttons and toolbars have no default entry: their corner radius is a formula of
their size, and a theme that names one overrides the formula.

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
with it. Widgets follow it too. Text inputs don't: a text field keeps its own font, so typed text isn't
restyled by the theme.

### Fonts

Three families are bundled and always available: **Roboto**, **Noto Sans Arabic** and **Hack Nerd Font
Mono**. Tesserae never looks at the system's fonts, so text looks the same on every machine. To use any
other family, register its file first:

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
| one screen's look | a stylesheet for that screen: `app.load(..., stylesheet=...)` |
| every screen's default look | `App(stylesheet=...)` |
| a component's shape or shadow | `components:` in a theme |
| a built-in component's parts, everywhere | [its stylesheet](../stylesheets/index.md), next to your views |
| the type | `typography:` in a theme, and [fonts](#fonts) |
| one node | its `style:` |

### While the app runs

`app.set_theme_specs(default, custom)` re-themes every screen the app built, and the window, in one
call. Both dicts are the complete new selection (`None` for none); the seed and the light or dark
appearance stay as they are. `app.set_stylesheet_spec(spec)` does the same for the default stylesheet.
With `run(hot_reload=True)`, saving a theme or stylesheet file does this for you.

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

A node's `style:` can name a `*_Style.yaml` file instead of a mapping, so several views can share one:

```yaml
# Counter_View.yaml
id: root
kind: Container
style: counter_Style.yaml   # or {flex_direction: vertical, width: 240, gap: 12}
```

```yaml
# counter_Style.yaml: one node's style
id: counter_style      # a name for the style, for the reader (optional)
style:
  flex_direction: vertical
  width: 240
  gap: 12
```

The fields go under `style:`, as they do in a view, and `id:` is a name for the style that Tesserae doesn't use. A
file that is only the fields, with no `style:` above them, is read as well. An editor with the
[style schema](../guide/editor-support.md) checks the file and says what each field is.

The file is found next to the file that names it, and can't be outside that folder (the same rules as
`include:`). Hot reload watches it. It is the whole style: a node's `style:` is a file or a mapping, not
both. To vary one node, give it a class and a stylesheet rule. A stylesheet's or theme's rule can name
one too (`- {kind: Rect, classes: [card], style: card_Style.yaml}`). A component fragment can't name one:
its look comes from its parameters and its [stylesheet](../stylesheets/index.md).

### On a single view

Outside an `App`, `load_view` takes the same arguments:

```python
from tesserae.spec import load_view

view = load_view(
    "Home_View.yaml",
    theme_seed=(0x67, 0x50, 0xA4, 0xFF),
    custom_theme="themes/Brand_Theme.yaml",
    stylesheet="styles/Home_Stylesheet.yaml",
)
```

`stylesheet=`, `default_theme=` and `custom_theme=` take file paths; each also has a `*_spec=` form that
takes a dict directly (`custom_theme_spec={"colors": {"primary": "#00FF00"}}`). Give one form or the other.
A mistake in a theme or stylesheet names the file:
`ValueError: themes/Brand_Theme.yaml: custom_theme_spec=: unknown field 'colours'`.

## How it is implemented

- **Resolving.** `Theme.resolve(seed, dark, default_theme_spec, custom_theme_spec)` turns the four inputs
  into one `Theme`: the role table (`tokens.resolve_scheme`), the `components:` map, the type scale and the
  motion tokens. `app.theme` and `view.theme` return one.
- **Applying.** A view is built by Tesserae's own compiler: for each node it merges the four layers
  (above), resolves colour roles against the scheme, and sets the result on the node. `view.set_theme`
  runs the same pass again over the nodes already built, in place, so a theme change never rebuilds a view.
- **Following.** `tesserae.follow` keeps the widgets, controls and overlays made on an app's window
  without a `theme=`. When the app's theme or appearance changes (including the OS switching) it re-themes
  them with the app's views.
- **Files.** Tesserae reads theme and stylesheet files itself and hands the engine only data, as for views
  and images. `*_Theme.yaml`, `*_Stylesheet.yaml` and `*_Style.yaml` say what a file is, and a file named
  for one kind is refused by the loader of another. A rule's `style:` may name a `*_Style.yaml` file.

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

- `shape(name: str) -> Optional[float]`: The corner radius of the MD3 shape token `name` (`"small"`, `"medium"`, ...), or `None` if it isn't one.
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
