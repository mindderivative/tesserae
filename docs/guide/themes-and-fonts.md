# Themes & Fonts

Give Tesserae file paths for themes, stylesheets and fonts. Tesserae
reads and parses them itself and hands `tre` only the data, the same as
it does for views and images.

## Themes and stylesheets for an app

Give the `App` one theme for every screen, plus a default stylesheet;
a screen can bring its own stylesheet instead:

```python
from tesserae import App

app = App(
    theme_seed=(0x67, 0x50, 0xA4, 0xFF),
    custom_theme="themes/Brand.yaml",   # one theme, every screen
    stylesheet="styles/Default.yaml",   # every screen's default
)
app.load("Home_View.yaml", HomeViewModel)
app.load("Settings_View.yaml", SettingsViewModel, stylesheet="styles/Settings.yaml")
```

The theme is app-wide because in `tre` a theme belongs to the window.
The window's theme is what widgets from `tesserae.widgets` (and `tre`'s
hover and press tints on them) use, and switching screens never changes
it. A YAML node's own state layer and ripple use the view's theme
([Interaction Feedback](interaction.md)).
`app.show()` gives the window the same theme as the screens: the same
seed (`theme_seed=` first, then the custom theme's `seed:`, then the
default theme's) and both themes' `colors:`. An app with no seed
anywhere leaves the window unthemed, as `tre` does. A stylesheet belongs
to a single view, so it can differ per screen. For a screen you pass to `App.register()`, build its view with
`app.build_view("Foo_View.yaml")` so it gets the same theme and
stylesheet.

The theme and default stylesheet files are read once, when the `App` is created, so a font warning appears once rather than once per screen. A screen's own stylesheet file is read when that screen loads.

## Themes and stylesheets on a single view

Outside an `App`, `load_view` takes the same arguments:

```python
from tesserae.spec import load_view

view = load_view(
    "Home_View.yaml",
    theme_seed=(0x67, 0x50, 0xA4, 0xFF),
    custom_theme="themes/Brand.yaml",
    stylesheet="styles/Home.yaml",
)
```

- `stylesheet=`, `default_theme=` and `custom_theme=` take file paths,
  relative to the current directory.
- Each also has a `*_spec=` form that takes a dict directly
  (`custom_theme_spec={"colors": {"primary": "#00FF00"}}`). Give one
  form or the other, not both.
- The files use `tre`'s own schemas unchanged: a theme has `seed`,
  `dark`, `colors`, `styles`, `components` and `typography`; a
  stylesheet has `styles`. See `tre`'s
  [theming guide](https://mindderivative.github.io/tre/guide/theming-and-accessibility/).
- If `tre` rejects a theme or stylesheet's contents, the error names
  that file:

  ```text
  ValueError: themes/Brand.yaml: custom_theme_spec=: unknown field `colours`, ...
  ```

## Layout rules in stylesheets and themes

A stylesheet's or theme's `styles:` rules can set layout as well as
paint -- `margin`, `flex_grow`, `flex_shrink`, `flex_basis`,
`align_items` and `justify_content` -- and since `tre` 0.3.3 those rules
take effect. Before 0.3.3 they were silently ignored, so if you're
upgrading, a screen whose stylesheet sets them may now lay out
differently. A widget's own inline `style:` always applied, and still
wins over any rule.

## Transparency: color alpha and `opacity`

Since `tre` 0.3.4, two things work the way they do in CSS:

- **A color's own alpha renders.** `"#FFFFFF80"` is half-transparent
  white, and `"#FFFFFF00"` is invisible. (Before 0.3.4 a color's alpha
  was ignored, so `"#FFFFFF00"` painted solid white.) Give text an opaque
  color.
- **`opacity` fades the node and everything inside it**, as one layer.
  To dim a background without dimming what sits on it, put the
  translucency in the background's color instead. The built-in `Dialog`
  and `SideSheetModal` fragments do this: their scrim is
  `background: "#00000052"` (black at 32%, as `tre`'s own dialogs use)
  with no `opacity`, so the panel stays fully opaque. A theme's
  `colors: {scrim: ...}` doesn't reach those two fragments, since a YAML
  color can't be "a theme role at 32%".

## Light and dark

An `App` follows the OS by default (`dark="system"`): when the OS
switches between light and dark, every screen and the window switch
with it, in place. It starts dark, since the OS's appearance can't be
read until it first switches. To fix the appearance instead, pass
`dark=True` or `dark=False`, or call `app.set_dark(...)` at any time;
`app.set_dark("system")` goes back to following the OS.

```python
app = App(theme_seed=(0x67, 0x50, 0xA4, 0xFF))   # follows the OS, starts dark
app.set_dark(False)                               # light from now on
```

## Typography in a theme

A theme's `typography:` overrides fields of MD3's type roles:

```yaml
typography:
  body_large: {font_family: Inter, font_size: 17}
  title_medium: {font_weight: 600}
```

Display text follows it: a `Text` or `Link` with `typography_role:
body_large` takes the theme's `body_large`. Fields the node sets itself
(`font_size:` and so on) still win. **Text inputs don't follow it:** a
text field keeps its own font even with a `typography_role`, so typed
text, and later multiline fields and the code editor, isn't restyled by
the theme. A custom theme's entry for a role replaces the default
theme's entry for that role, rather than merging with it. Re-theming,
including hot reload of a theme file, updates the text in place.

(`tre` applied a theme's `typography:` only to its imperative widgets,
never to a view; Tesserae applies it to both.)

## Reading the theme from code

`app.theme` (and `view.theme`) is the resolved theme, a `tesserae.Theme`:

```python
theme = app.theme
theme.role("primary")                 # (r, g, b, a), or None with no seed
theme.shape("card", "elevated")       # components: card.elevated, then card
theme.elevation("dialog")             # an MD3 elevation level, or None
theme.typography("body_large")        # the type role, with typography: overrides
theme.easing("emphasized_decelerate") # (x1, y1, x2, y2), for node.animate(easing=...)
theme.duration("medium2")             # 300 (ms)
```

`shape` and `elevation` return `None` when the theme's `components:`
doesn't mention the component, and the widget uses its own MD3 default.
A custom theme's `components:` entry, or `typography:` role, replaces
the default theme's entry for the same key. MD3's easing and duration
tokens are all there. `emphasized` is MD3's single-curve form
(0.2, 0, 0, 1), since one cubic bézier can't express the two-part curve
`tre` used.

## Switching themes later

In an `App`, `app.set_theme_specs(default_theme_spec, custom_theme_spec)`
re-themes every screen the app built, and the window, in one call. Both
dicts are the complete new selection (`None` for none), and the seed and
the light/dark appearance stay as they are. With `run(hot_reload=True)`, saving
a theme file does this for you ([Hot Reload](hot-reload.md#theme-and-stylesheet-files)).
`app.set_stylesheet_spec(stylesheet_spec)` does the same for the app's
default stylesheet, re-styling every screen that uses it.

For a single view or window, `load_theme` and `load_stylesheet` read a
file into the dict `tre` takes, for `View.set_theme` and
`Window.set_theme`:

```python
from tesserae.spec import load_theme

view.set_theme(theme_seed=seed, custom_theme_spec=load_theme("themes/Dark.yaml"))
window.set_theme(seed, custom_theme_spec=load_theme("themes/Dark.yaml"))
```

Use the `*_spec=` arguments with these, not `tre`'s path arguments, so
`tre` is never handed a file.

## Custom fonts

`tre` bundles three families -- **Roboto**, **Noto Sans Arabic** and
**Hack Nerd Font Mono** -- and never looks at fonts installed on the
system, so text looks the same on every machine. To use any other
family, register its font file first:

```python
import tesserae

tesserae.register_font("fonts/Inter-Regular.ttf")  # -> ["Inter"]
```

The return value is the family name(s) the file contains -- the exact
name to use as `font_family`, in a theme's `typography:` or a view's
`text:`. Registration is process-wide and a running window picks the
font up on its next frame. Registering the same file twice is harmless.
A file with no font faces in it raises `ValueError`.

### When a font isn't available

`tre` quietly draws a bundled face in place of any family it doesn't
have. Tesserae catches that instead: loading a theme or view that names
a family which is neither bundled nor registered issues a
`tesserae.fonts.FontFallbackWarning` naming the file and the family.

It's a warning rather than an error because registering a font after a
view exists is allowed. To make it an error:

```python
import warnings
from tesserae.fonts import FontFallbackWarning

warnings.filterwarnings("error", category=FontFallbackWarning)
```

## Not yet covered

- Nothing currently. A component added with
  [`tesserae.instantiate`](components.md) gets its host's theme and
  stylesheet, and follows them (M37).
