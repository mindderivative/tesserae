"""M31 Phase 2: stylesheet files are hot-reloaded.

The app's default stylesheet (`App(stylesheet=)`) re-styles every screen
that uses it; a screen's own `load(stylesheet=)` file re-styles only the
screens built with it. Watcher tests use a `FakeHandle`, as in
`test_theme_reload.py`: the test runs each queued reload itself.
"""

import importlib.util
import queue
import re
import sys
from pathlib import Path

import pytest

import tesserae.fonts as fonts
from tesserae import App

SEED = (0x67, 0x50, 0xA4, 0xFF)
RECT = 'id: box\nkind: Rect\nstyle: {width: 10, height: 10, background: "#112233"}\n'


@pytest.fixture(autouse=True)
def _fresh_font_registry(monkeypatch):
    monkeypatch.setattr(fonts, "_registered", set())


class FakeHandle:
    def __init__(self):
        self.queued: "queue.Queue" = queue.Queue()

    def call_soon(self, fn):
        self.queued.put(fn)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _module(path: Path, source: str):
    _write(path, source)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pair(tmp_path: Path, prefix: str, view_text: str = RECT):
    view = _write(tmp_path / f"{prefix}_View.yaml", view_text)
    module = _module(
        tmp_path / f"{prefix}_ViewModel.py",
        f"from tesserae import ViewModel\n\n\nclass {prefix}ViewModel(ViewModel):\n    pass\n",
    )
    return view, getattr(module, f"{prefix}ViewModel")


def _sheet(radius: int) -> str:
    return f"styles:\n  - kind: Rect\n    style: {{corner_radius: {radius}}}\n"


def _spec(radius: int) -> dict:
    return {"styles": [{"kind": "Rect", "style": {"corner_radius": radius}}]}


def _radius(view) -> float:
    return view.node("box").get("corner_radius")


def _edit_until_queued(handle: FakeHandle, path: Path, text: str, attempts: int = 40):
    for _ in range(attempts):
        path.write_text(text)
        try:
            return handle.queued.get(timeout=0.25)
        except queue.Empty:
            continue
    raise AssertionError(f"the watcher never queued a reload for {path}")


@pytest.fixture
def watching():
    started = []

    def start(app: App):
        handle = FakeHandle()
        started.extend(app._start_watchers(handle))
        return handle

    yield start
    for watcher in started:
        watcher.stop()


# -- set_stylesheet_spec ----------------------------------------------


def test_set_stylesheet_spec_restyles_the_screens_using_the_default(tmp_path: Path):
    app = App(theme_seed=SEED, stylesheet_spec=_spec(2))
    home, _ = app.load(*_pair(tmp_path, "Home"))
    own, _ = app.load(*_pair(tmp_path, "Own"), stylesheet_spec=_spec(20))

    app.set_stylesheet_spec(_spec(5))

    assert _radius(home) == 5.0
    assert _radius(own) == 20.0  # a screen's own stylesheet isn't the default
    later, _ = app.load(*_pair(tmp_path, "Later"))
    assert _radius(later) == 5.0


def test_a_rejected_stylesheet_leaves_every_screen_as_it_was(tmp_path: Path):
    app = App(theme_seed=SEED, stylesheet_spec=_spec(2))
    home, _ = app.load(*_pair(tmp_path, "Home"))
    other, _ = app.load(*_pair(tmp_path, "Other"))
    with pytest.raises(ValueError):
        app.set_stylesheet_spec({"styles": "not a list"})
    assert _radius(home) == _radius(other) == 2.0
    later, _ = app.load(*_pair(tmp_path, "Later"))
    assert _radius(later) == 2.0


def test_a_failure_part_way_undoes_the_screens_already_restyled(tmp_path: Path):
    app = App(theme_seed=SEED, stylesheet_spec=_spec(2))
    first, _ = app.load(*_pair(tmp_path, "First"))
    second, _ = app.load(*_pair(tmp_path, "Second"))

    class Refuses:
        """Stands in for a view `tre` refuses the new stylesheet on."""

        def __init__(self, view):
            self.view = view

        def set_stylesheet(self, stylesheet_spec=None):
            if stylesheet_spec == _spec(9):
                raise ValueError("refused")
            self.view.set_stylesheet(stylesheet_spec=stylesheet_spec)

    app._built[1].view = Refuses(second)
    with pytest.raises(ValueError, match="refused"):
        app.set_stylesheet_spec(_spec(9))
    assert _radius(first) == _radius(second) == 2.0


# -- hot reload of stylesheet files ------------------------------------


def test_editing_the_default_stylesheet_file_restyles_its_screens(tmp_path: Path, watching):
    default = _write(tmp_path / "default.yaml", _sheet(2))
    own = _write(tmp_path / "own.yaml", _sheet(20))
    app = App(theme_seed=SEED, stylesheet=default)
    home, _ = app.load(*_pair(tmp_path, "Home"))
    settings, _ = app.load(*_pair(tmp_path, "Settings"))
    other, _ = app.load(*_pair(tmp_path, "Other"), stylesheet=own)
    handle = watching(app)

    reload = _edit_until_queued(handle, default, _sheet(7))
    assert _radius(home) == 2.0  # nothing applied until the loop runs it
    reload()

    assert _radius(home) == _radius(settings) == 7.0
    assert _radius(other) == 20.0


def test_editing_a_screens_own_stylesheet_file_restyles_only_the_screens_using_it(tmp_path: Path, watching):
    shared = _write(tmp_path / "cards.yaml", _sheet(4))
    app = App(theme_seed=SEED, stylesheet_spec=_spec(1))
    a, _ = app.load(*_pair(tmp_path, "A"), stylesheet=shared)
    b, _ = app.load(*_pair(tmp_path, "B"), stylesheet=shared)
    plain, _ = app.load(*_pair(tmp_path, "Plain"))
    handle = watching(app)

    _edit_until_queued(handle, shared, _sheet(11))()

    assert _radius(a) == _radius(b) == 11.0
    assert _radius(plain) == 1.0


def test_a_broken_stylesheet_edit_raises_on_the_loop_and_the_watcher_carries_on(tmp_path: Path, watching):
    default = _write(tmp_path / "default.yaml", _sheet(2))
    app = App(theme_seed=SEED, stylesheet=default)
    home, _ = app.load(*_pair(tmp_path, "Home"))
    handle = watching(app)

    with pytest.raises(ValueError, match="invalid YAML"):
        _edit_until_queued(handle, default, "styles: [unclosed\n")()
    assert _radius(home) == 2.0

    _edit_until_queued(handle, default, _sheet(6))()
    assert _radius(home) == 6.0


def test_a_stylesheet_tre_rejects_is_reported_naming_the_file(tmp_path: Path, watching):
    own = _write(tmp_path / "own.yaml", _sheet(3))
    app = App(theme_seed=SEED)
    home, _ = app.load(*_pair(tmp_path, "Home"), stylesheet=own)
    handle = watching(app)

    rejected = _edit_until_queued(handle, own, "styles: not a list\n")
    with pytest.raises(ValueError, match=rf"^{re.escape(str(own.resolve()))}: "):
        rejected()
    assert _radius(home) == 3.0


def test_stylesheet_specs_are_not_watched(tmp_path: Path):
    app = App(theme_seed=SEED, stylesheet_spec=_spec(1))
    app.load(*_pair(tmp_path, "Home"), stylesheet_spec=_spec(2))
    watchers = app._start_watchers(FakeHandle())
    try:
        assert [type(w).__name__ for w in watchers] == ["ViewWatcher"]
    finally:
        for w in watchers:
            w.stop()


# -- bindings through a re-style (tre M91) -------------------------------

BOUND = (
    "id: root\nkind: Container\nchildren:\n"
    '  - {id: box, kind: Rect, style: {width: 10, height: 10, background: "#112233"}}\n'
    "  - id: agree\n    kind: Checkbox\n    checked: false\n"
    '    style: {width: 18, height: 18, background: "#6750A4"}\n'
    '    bindings: {checked: "{{ agreed.get() }}"}\n    handlers: {on_change: "changed"}\n'
)


def test_a_restyle_keeps_bound_values_and_fires_on_change_once(tmp_path: Path):
    """Pins `tre` 0.3.3's behaviour, documented in the hot-reload guide:
    re-applying bindings after a re-style sets each bound value again,
    so a declared `on_change` fires once -- as it does when the view is
    first attached. If `tre` stops doing that, this test says so."""
    view_path = _write(tmp_path / "Form_View.yaml", BOUND)
    module = _module(
        tmp_path / "Form_ViewModel.py",
        "from tesserae import Signal, ViewModel\n\n\nclass FormViewModel(ViewModel):\n"
        "    def __init__(self, view):\n        self.agreed = Signal(True)\n        self.calls = 0\n"
        "        super().__init__(view)\n\n    def changed(self):\n        self.calls += 1\n",
    )
    app = App(theme_seed=SEED, stylesheet_spec=_spec(2))
    view, vm = app.load(view_path, module.FormViewModel)
    vm.calls = 0

    app.set_stylesheet_spec(_spec(8))

    assert view.node("agree").get_checked() is True  # not the YAML's `false`
    assert vm.calls == 1
