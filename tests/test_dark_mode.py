"""M38 Phase 3: light and dark.

`App(dark="system")` (the default, M38 Q2) follows the OS: the window's
`color_scheme` event re-themes every screen and the window. It starts
dark (Q3): 0.3.4 can't read the OS's appearance before its first event.
With `dark=True`/`False` the app keeps its choice, and puts the window's
own theme back when `tre` flips it on an OS switch. OS switches are
simulated with `window.simulate("color_scheme", dark=...)`.
"""

import importlib.util
import sys

import pytest

from tesserae import App, tokens

SEED = (0x67, 0x50, 0xA4, 0xFF)
LIGHT, DARK = tokens.color_scheme(SEED, False)["primary"], tokens.color_scheme(SEED, True)["primary"]
VIEW = ('id: root\nkind: Container\nchildren:\n'
        '  - {id: box, kind: Rect, style: {width: 10, height: 10, background: primary}}\n'
        '  - {id: label, kind: Text, text: {content: "", font_family: Roboto, font_size: 14}, style: {foreground: on_surface, width: 50, height: 20}, bindings: {text: "{{ title.get() }}"}}\n')


def _load(app, tmp_path, prefix="Home"):
    view = tmp_path / f"{prefix}_View.yaml"
    view.write_text(VIEW)
    vm = tmp_path / f"{prefix}_ViewModel.py"
    vm.write_text(f"from tesserae import Signal, ViewModel\n\n\nclass {prefix}ViewModel(ViewModel):\n"
                  f"    def __init__(self, view):\n        self.title = Signal('live')\n        super().__init__(view)\n")
    spec = importlib.util.spec_from_file_location(vm.stem, vm)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    view_obj, _ = app.load(view, getattr(module, f"{prefix}ViewModel"))
    return view_obj


def _screen(view):
    return view.node("box").get("fill")


def _window(app):
    return app.show(next(iter(app._registered))).theme.role("primary")


def _os(app, dark):
    app._window.simulate("color_scheme", dark=dark)


def test_the_default_follows_the_system_and_starts_dark(tmp_path):
    app = App(theme_seed=SEED)
    view = _load(app, tmp_path)
    assert app.dark_mode == "system" and app.dark is True
    assert _screen(view) == DARK and _window(app) == DARK


def test_following_the_os_re_themes_screens_and_the_window(tmp_path):
    app = App(theme_seed=SEED)
    home, settings = _load(app, tmp_path, "Home"), _load(app, tmp_path, "Settings")
    _os(app, False)
    assert app.dark is False and _screen(home) == _screen(settings) == LIGHT and _window(app) == LIGHT
    assert home.node("label").get("text") == "live"  # bound values stay
    _os(app, True)
    assert _screen(home) == DARK and _window(app) == DARK


@pytest.mark.parametrize("fixed", [True, False])
def test_a_fixed_choice_ignores_the_os_and_keeps_the_window_with_it(tmp_path, fixed):
    app = App(theme_seed=SEED, dark=fixed)
    view = _load(app, tmp_path)
    expected = DARK if fixed else LIGHT
    _os(app, not fixed)
    assert app.dark is fixed and _screen(view) == expected
    assert _window(app) == expected  # tre flipped the window's own theme; the app put it back


def test_set_dark_switches_in_place_and_system_resumes_following(tmp_path):
    app = App(theme_seed=SEED)
    view = _load(app, tmp_path)
    box = view.node("box")
    app.set_dark(False)
    assert app.dark_mode is False and _screen(view) == LIGHT and view.node("box") == box
    _os(app, True)
    assert _screen(view) == LIGHT  # fixed now
    app.set_dark("system")
    assert _screen(view) == LIGHT  # unchanged until the OS next switches
    _os(app, True)
    assert _screen(view) == DARK


def test_screens_loaded_later_use_the_current_appearance(tmp_path):
    app = App(theme_seed=SEED)
    _load(app, tmp_path, "Home")
    _os(app, False)
    later = _load(app, tmp_path, "Later")
    assert _screen(later) == LIGHT


def test_app_theme_reports_the_current_appearance(tmp_path):
    app = App(theme_seed=SEED)
    assert app.theme.dark is True and app.theme.role("primary") == DARK
    app.set_dark(False)
    assert app.theme.dark is False and app.theme.role("primary") == LIGHT


@pytest.mark.parametrize("bad", ["auto", None, "dark"])
def test_a_bad_dark_value_is_an_error(bad):
    with pytest.raises(ValueError, match='dark must be True, False or "system"'):
        App(dark=bad)
    with pytest.raises(ValueError, match='dark must be True, False or "system"'):
        App().set_dark(bad)
