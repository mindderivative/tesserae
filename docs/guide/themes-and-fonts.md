# Themes & Fonts

Give Tesserae file paths for themes, stylesheets and fonts. Tesserae
reads and parses them itself and hands `tre` only the data, the same as
it does for views and images.

## Themes and stylesheets on a view

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

## Switching themes later

`load_theme` and `load_stylesheet` read a file into the dict `tre`
takes, for `View.set_theme` and `Window.set_theme`:

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

- **`App.load()` doesn't take theme or stylesheet arguments yet.** Use
  `load_view(...)` plus `App.register(...)` for a themed screen.
- **Hot reload doesn't watch theme or stylesheet files.**
  [`ViewWatcher`](hot-reload.md) watches the view, its includes,
  fragments and images; to pick up a theme edit, call `set_theme` again
  with a freshly loaded theme.
