"""M30: `App`'s app-wide theme and per-screen stylesheets.

The theme is set once on `App(...)` and applies to every screen `load()`
builds (a theme is window-level in `tre`); `stylesheet=` on `App(...)`
is every screen's default, and `load(stylesheet=...)` replaces it for
one screen. Files are read once, by Tesserae; `tre` gets dicts.

Effects are observed through `elevation`/`corner_radius`, which a
theme's or stylesheet's `styles:` can set and `Node.get` reads back.
"""

import importlib.util
import sys
import warnings
from pathlib import Path

import pytest

from helpers import elevation

import tesserae.app as app_module
import tesserae.fonts as fonts
from tesserae import App
from tesserae.fonts import FontFallbackWarning
from tesserae.spec import load_view

SEED = (0x67, 0x50, 0xA4, 0xFF)
RECT = 'id: box\nkind: Rect\nstyle: {width: 10, height: 10, background: "#112233"}\n'


@pytest.fixture(autouse=True)
def _fresh_font_registry(monkeypatch):
    monkeypatch.setattr(fonts, "_registered", set())


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _rule(**style) -> str:
    body = ", ".join(f"{k}: {v}" for k, v in style.items())
    return f"styles:\n  - kind: Rect\n    style: {{{body}}}\n"


def _pair(tmp_path: Path, prefix: str):
    """A real `<prefix>_View.yaml` + `<prefix>_ViewModel.py` pair (`load()`
    checks the ViewModel's defining file)."""
    view = _write(tmp_path / f"{prefix}_View.yaml", RECT)
    vm_path = _write(
        tmp_path / f"{prefix}_ViewModel.py",
        f"from tesserae import ViewModel\n\n\nclass {prefix}ViewModel(ViewModel):\n    pass\n",
    )
    spec = importlib.util.spec_from_file_location(vm_path.stem, vm_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return view, getattr(module, f"{prefix}ViewModel")


def _look(view):
    node = view.node("box")
    return elevation(node), node.get("corner_radius")


def test_an_app_wide_theme_reaches_every_loaded_screen(tmp_path: Path):
    theme = _write(tmp_path / "brand.yaml", _rule(elevation=3))
    app = App(theme_seed=SEED, custom_theme=theme)
    a, _ = app.load(*_pair(tmp_path, "Home"))
    b, _ = app.load(*_pair(tmp_path, "Settings"))
    assert _look(a)[0] == _look(b)[0] == 3.0


def test_a_default_theme_file_applies_too(tmp_path: Path):
    base = _write(tmp_path / "base.yaml", _rule(corner_radius=6))
    app = App(theme_seed=SEED, default_theme=base)
    view, _ = app.load(*_pair(tmp_path, "Home"))
    assert _look(view)[1] == 6.0


def test_the_default_stylesheet_applies_and_a_screen_can_replace_it(tmp_path: Path):
    default = _write(tmp_path / "default.yaml", _rule(corner_radius=8))
    own = _write(tmp_path / "settings.yaml", _rule(corner_radius=20))
    app = App(theme_seed=SEED, stylesheet=default)
    home, _ = app.load(*_pair(tmp_path, "Home"))
    settings, _ = app.load(*_pair(tmp_path, "Settings"), stylesheet=own)
    assert _look(home)[1] == 8.0
    assert _look(settings)[1] == 20.0


def test_spec_forms_work_the_same_as_files(tmp_path: Path):
    app = App(
        theme_seed=SEED,
        custom_theme_spec={"styles": [{"kind": "Rect", "style": {"elevation": 2}}]},
        stylesheet_spec={"styles": [{"kind": "Rect", "style": {"corner_radius": 4}}]},
    )
    home, _ = app.load(*_pair(tmp_path, "Home"))
    other, _ = app.load(
        *_pair(tmp_path, "Other"),
        stylesheet_spec={"styles": [{"kind": "Rect", "style": {"corner_radius": 12}}]},
    )
    assert _look(home) == (2.0, 4.0)
    assert _look(other) == (2.0, 12.0)


@pytest.mark.parametrize("arg", ["default_theme", "custom_theme", "stylesheet"])
def test_a_file_and_its_spec_together_is_an_error(tmp_path: Path, arg):
    file = _write(tmp_path / "x.yaml", "{}\n")
    with pytest.raises(ValueError, match=rf"App: pass {arg}= or {arg}_spec=, not both"):
        App(**{arg: file, f"{arg}_spec": {}})


def test_load_rejects_both_stylesheet_forms(tmp_path: Path):
    sheet = _write(tmp_path / "s.yaml", _rule(corner_radius=1))
    app = App()
    with pytest.raises(ValueError, match="stylesheet= or stylesheet_spec=, not both"):
        app.load(*_pair(tmp_path, "Home"), stylesheet=sheet, stylesheet_spec={})


def test_screens_are_tesserae_views_built_in_the_apps_window(tmp_path: Path):
    """M37: `App` builds its screens itself, with Tesserae's `View`, in its
    own window, from the theme and stylesheet it read; `tre` gets nodes,
    never files or dicts."""
    from tesserae.view import View as TesseraeView

    theme = _write(tmp_path / "brand.yaml", _rule(elevation=3))
    sheet = _write(tmp_path / "default.yaml", _rule(corner_radius=8))
    app = App(theme_seed=SEED, dark=True, custom_theme=theme, stylesheet=sheet)
    view, _ = app.load(*_pair(tmp_path, "Home"))
    assert isinstance(view, TesseraeView) and view.window is app.show("Home")
    assert _look(view) == (3.0, 8.0)


def test_theme_files_are_read_once_so_a_font_warning_fires_once(tmp_path: Path):
    theme = _write(tmp_path / "inter.yaml", "typography: {body_large: {font_family: Inter}}\n")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app = App(theme_seed=SEED, custom_theme=theme)
        for name in ("Home", "Settings", "About"):
            app.load(*_pair(tmp_path, name))
    assert sum(issubclass(w.category, FontFallbackWarning) for w in caught) == 1


def test_build_view_gives_a_registered_screen_the_app_theme(tmp_path: Path):
    theme = _write(tmp_path / "brand.yaml", _rule(elevation=3))
    sheet = _write(tmp_path / "default.yaml", _rule(corner_radius=8))
    app = App(theme_seed=SEED, custom_theme=theme, stylesheet=sheet)
    view_path, vm_cls = _pair(tmp_path, "Home")

    themed = app.build_view(view_path)
    app.register("Home", themed, vm_cls(themed))
    plain = load_view(view_path, theme_seed=SEED)  # built another way: keeps its own theme

    assert _look(themed) == (3.0, 8.0)
    assert _look(plain) != (3.0, 8.0)


def test_an_app_with_no_theme_arguments_behaves_as_before(tmp_path: Path):
    app = App()
    view, _ = app.load(*_pair(tmp_path, "Home"))
    assert _look(view) == _look(load_view(tmp_path / "Home_View.yaml"))
