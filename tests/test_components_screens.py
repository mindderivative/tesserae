"""M37 Phase 5: components and screens on Tesserae's builder.

A component (`tesserae.instantiate`, `View.instantiate`) is built in its
host's window with the host's theme and stylesheet, and follows them when
they change -- which closes M31's gap, where an embedded component built
by `tre` got neither. `App` builds screens in its own window and switches
them by attaching and detaching their roots.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
import tre

import tesserae
from tesserae import App, instantiate, tokens
from tesserae.view import View

SEED = (0x67, 0x50, 0xA4, 0xFF)
HOST = 'id: root\nkind: Container\nchildren:\n  - {id: host, kind: Container}\n  - {id: own, kind: Rect, style: {width: 10, height: 10, background: primary}}\n'
CARD = 'id: card\nkind: Rect\nstyle: {width: 10, height: 10, background: primary}\nbindings: {width: "{{ size.get() }}"}\n'


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _vm_module(path: Path, class_name: str, body: str = "    pass\n"):
    _write(path, f"from tesserae import Signal, ViewModel\n\n\nclass {class_name}(ViewModel):\n{body}")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


@pytest.fixture
def card(tmp_path):
    view = _write(tmp_path / "Card_View.yaml", CARD)
    vm = _vm_module(tmp_path / "Card_ViewModel.py", "CardViewModel",
                    "    def __init__(self, component, size=20):\n        self.size = Signal(size)\n        super().__init__(component)\n")
    return view, vm


def _host(tmp_path, **theme):
    return View(_write(tmp_path / "Host_View.yaml", HOST), theme_seed=SEED, **theme)


def test_a_component_gets_its_hosts_theme_and_stylesheet(tmp_path, card):
    """M31's gap: a component built by `tre` got neither."""
    sheet = {"styles": [{"kind": "Rect", "style": {"corner_radius": 6}}]}
    host = _host(tmp_path, stylesheet_spec=sheet, custom_theme_spec={"styles": [{"kind": "Rect", "style": {"elevation": 2}}]})
    component, vm = instantiate(host, card[0], card[1], host.node("host"))
    node = component.node("card")
    assert node.get("fill") == tokens.color_scheme(SEED)["primary"]
    assert node.get("corner_radius") == 6.0 and node.get("shadows") == tokens.elevation_shadows(2)
    assert node.get("width") == 20.0  # its own ViewModel's binding


def test_a_component_follows_its_host_when_re_themed_or_re_styled(tmp_path, card):
    host = _host(tmp_path)
    component, vm = instantiate(host, card[0], card[1], host.node("host"), size=33)
    red = (0xB3, 0x26, 0x1E, 0xFF)
    node = component.node("card")
    host.set_theme(theme_seed=red)
    assert node.get("fill") == tokens.color_scheme(red)["primary"]  # checked before the next change
    host.set_stylesheet({"styles": [{"kind": "Rect", "style": {"corner_radius": 9}}]})
    assert node.get("corner_radius") == 9.0
    assert node.get("width") == 33.0  # still bound, not the placeholder


def test_remove_unwires_and_frees_a_component(tmp_path, card):
    host = _host(tmp_path)
    component, vm = instantiate(host, card[0], card[1], host.node("host"))
    root = component.root
    assert root.parent() == host.node("host")
    component.remove()
    assert vm.size._subscribers == []
    vm.size.set(99)  # nothing listens any more
    with pytest.raises(ValueError):
        root.get("width")  # destroyed


def test_components_nest(tmp_path, card):
    outer_view = _write(tmp_path / "Outer_View.yaml", "id: shell\nkind: Container\nchildren:\n  - {id: slot, kind: Container}\n")
    outer_vm = _vm_module(tmp_path / "Outer_ViewModel.py", "OuterViewModel")
    host = _host(tmp_path)
    outer, _ = instantiate(host, outer_view, outer_vm, host.node("host"))
    inner, inner_vm = instantiate(outer, card[0], card[1], outer.node("slot"))
    host.set_stylesheet({"styles": [{"kind": "Rect", "style": {"corner_radius": 4}}]})
    assert inner.node("card").get("corner_radius") == 4.0
    outer.remove()
    assert inner_vm.size._subscribers == []


def test_host_reconcile_keeps_its_components(tmp_path, card):
    host = _host(tmp_path)
    component, _ = instantiate(host, card[0], card[1], host.node("host"))
    host.reconcile(host.spec)
    assert component.root.parent() == host.node("host")


# -- screens ---------------------------------------------------------------------------

SCREEN = 'id: root\nkind: Container\nchildren:\n  - {id: label, kind: Text, text: {content: "", font_family: Roboto, font_size: 14}, style: {foreground: "#000000", width: 80, height: 20}, bindings: {text: "{{ title.get() }}"}}\n'


def _pair(tmp_path, prefix):
    view = _write(tmp_path / f"{prefix}_View.yaml", SCREEN)
    vm = _vm_module(tmp_path / f"{prefix}_ViewModel.py", f"{prefix}ViewModel",
                    f"    def __init__(self, view):\n        self.title = Signal('{prefix}')\n        super().__init__(view)\n")
    return view, vm


def test_show_attaches_one_screen_at_a_time_and_keeps_the_others_alive(tmp_path):
    app = App(theme_seed=SEED)
    home, home_vm = app.load(*_pair(tmp_path, "Home"))
    settings, settings_vm = app.load(*_pair(tmp_path, "Settings"))
    window = app.show("Home")
    assert home.root.parent() == window.root and settings.root.parent() is None
    assert app.show("Settings") is window
    assert settings.root.parent() == window.root and home.root.parent() is None
    home_vm.title.set("changed while hidden")
    app.show("Home")
    assert home.node("label").get("text") == "changed while hidden"


def test_a_view_built_on_its_own_is_moved_into_the_apps_window(tmp_path):
    view_path, vm_cls = _pair(tmp_path, "Solo")
    view = View(view_path, theme_seed=SEED)
    vm = vm_cls(view)
    app = App(theme_seed=SEED)
    app.register("solo", view, vm)
    window = app.show("solo")
    assert view.window is window and view.root.parent() == window.root
    vm.title.set("still wired")
    assert view.node("label").get("text") == "still wired"


def test_register_rejects_a_tre_view(tmp_path):
    app = App()
    tre_view = tre.View(spec={"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000"}})
    with pytest.raises(TypeError, match="must be a tesserae View"):
        app.register("x", tre_view, None)
