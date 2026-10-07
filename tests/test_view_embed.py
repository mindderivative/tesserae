"""0.4.4 (#96): `view:` shows another `*_View.yaml` inside a view, with its ViewModel if it has one and without if not."""

import sys

import pytest
import yaml

from tesserae import App, View
from tesserae.spec.embed import EmbedError, embeds_of, expand_embeds

SEED = (0x67, 0x50, 0xA4, 0xFF)
LEFT = """
id: root
kind: Container
style: {flex_direction: vertical, width: 120, background: surface_container}
children:
  - {id: title, kind: Text, text: {content: "Left", typography_role: body_large}, style: {foreground: on_surface}}
"""
COUNTER = """
id: root
kind: Container
style: {width: 120, background: surface_container_high}
children:
  - {id: label, kind: Text, text: {content: "", typography_role: body_large}, style: {foreground: on_surface}, bindings: {text: "{{ label.get() }}"}}
  - {id: bump, kind: Rect, style: {width: 20, height: 20, background: primary}, handlers: {on_click: bump}}
"""
COUNTER_VM = """
from tesserae import Signal, ViewModel


class {name}ViewModel(ViewModel):
    def __init__(self, view, start=0):
        self.n = Signal(start)
        self.label = Signal(f"count {{start}}")
        super().__init__(view)

    def bump(self):
        self.n.update(lambda n: n + 1)
        self.label.set(f"count {{self.n.get()}}")
"""
HOST = """
id: root
kind: Container
style: {width: 300, height: 100, background: surface}
children:
  - {id: left, view: Left_View.yaml}
  - {id: counter, view: Counter_View.yaml, with: {start: 5}, style: {width: 140}}
"""


def _write(folder, name, text):
    (folder / name).write_text(text, encoding="utf-8")


def _vm_name(tmp_path, name):
    """A ViewModel module named for this test, so one test's class never answers for another's."""
    return f"{name}{abs(hash(str(tmp_path))) % 10**8}"


@pytest.fixture
def folder(tmp_path):
    name = _vm_name(tmp_path, "Counter")
    _write(tmp_path, "Left_View.yaml", LEFT)
    _write(tmp_path, f"{name}_View.yaml", COUNTER)
    _write(tmp_path, f"{name}_ViewModel.py", COUNTER_VM.format(name=name))
    _write(tmp_path, "Host_View.yaml", HOST.replace("Counter_View.yaml", f"{name}_View.yaml"))
    sys.path.insert(0, str(tmp_path))
    yield tmp_path, name
    sys.path.remove(str(tmp_path))
    sys.modules.pop(f"{name}_ViewModel", None)


def _host(folder, dark=True):
    app = App(width=300, height=100, theme_seed=SEED, dark=dark)
    view = View(folder / "Host_View.yaml", window=app.window)
    app.window.root.add_child(view.root)
    app.window.advance(32)
    return app, view


# -- the node ----------------------------------------------------------------------------------

def test_a_view_node_becomes_a_container_that_asks_for_the_view():
    spec = expand_embeds(yaml.safe_load(HOST))
    left = spec["children"][0]
    assert left == {"id": "left", "kind": "Container", "embed": {"view": "Left_View.yaml", "with": {}}}
    assert embeds_of(spec)["counter"] == {"view": "Counter_View.yaml", "with": {"start": 5}}
    assert "view" not in spec["children"][1] and spec["children"][1]["style"] == {"width": 140}


@pytest.mark.parametrize("node, message", [
    ({"view": "A_View.yaml"}, "needs an `id:`"),
    ({"id": "a", "view": 3}, "is a view's name or file"),
    ({"id": "a", "view": ""}, "is a view's name or file"),
    ({"id": "a", "view": "A_View.yaml", "kind": "Rect"}, "has kind"),
    ({"id": "a", "view": "A_View.yaml", "children": []}, "has children"),
    ({"id": "a", "view": "A_View.yaml", "text": {}}, "has text"),
    ({"id": "a", "view": "A_View.yaml", "with": [1]}, "`with:` is a mapping"),
])
def test_a_badly_written_view_node_is_refused(node, message):
    with pytest.raises(EmbedError, match=message):
        expand_embeds({"id": "root", "kind": "Container", "children": [node]})


# -- building ---------------------------------------------------------------------------------

def test_the_views_are_built_with_ids_of_their_own(folder):
    _, view = _host(folder[0])
    assert view.node("left").get("kind") == "box"
    assert view.embedded("left").node("title").get("text") == "Left"
    # both embedded views have an `id: root`, and so does the host: no clash
    assert view.embedded("left").node("root") is not None and view.node("root") is not None
    assert view.embedded("left").root.parent() == view.node("left")


def test_a_view_with_no_viewmodel_is_static(folder):
    _, view = _host(folder[0])
    assert view.embedded("left").viewmodel is None


def test_a_view_with_a_viewmodel_gets_it_and_its_with(folder):
    _, view = _host(folder[0])
    counter = view.embedded("counter")
    assert type(counter.viewmodel).__name__ == f"{folder[1]}ViewModel"
    assert counter.node("label").get("text") == "count 5"
    view.window.simulate("click", counter.node("bump"))
    view.window.advance(16)
    assert counter.node("label").get("text") == "count 6"
    assert view.embedded("counter").viewmodel is counter.viewmodel


def test_the_style_on_the_node_places_the_embedded_view(folder):
    _, view = _host(folder[0])
    assert view.node("counter").get("layout_width") == 140.0


def test_the_embedded_view_follows_the_hosts_theme(folder):
    app, view = _host(folder[0], dark=True)
    inner = view.embedded("left")
    dark_fill = inner.node("root").get("fill")
    app.set_dark(False)
    app.window.advance(16)
    assert inner.node("root").get("fill") != dark_fill
    assert inner.node("root").get("fill") == app.theme.role("surface_container")


def test_a_view_is_found_by_name_in_the_project(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "ViewModels").mkdir()
    name = _vm_name(tmp_path, "Named")
    _write(tmp_path / "Views", f"{name}_View.yaml", COUNTER)
    _write(tmp_path / "ViewModels", f"{name}_ViewModel.py", COUNTER_VM.format(name=name))
    _write(tmp_path / "Views", "Host_View.yaml", f"id: root\nkind: Container\nstyle: {{width: 200, height: 60}}\nchildren:\n  - {{id: it, view: {name}}}\n")
    app = App(width=300, height=100, theme_seed=SEED, root=tmp_path)
    view = View(tmp_path / "Views" / "Host_View.yaml", window=app.window)
    assert view.embedded("it").node("label").get("text") == "count 0"
    sys.modules.pop(f"{name}_ViewModel", None)


def test_a_name_with_no_project_says_so(tmp_path):
    _write(tmp_path, "Host_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: it, view: Left}\n")
    with pytest.raises(ValueError, match=r'widget "it".*no project to look in'):
        View(tmp_path / "Host_View.yaml")


def test_a_view_can_embed_a_view(tmp_path):
    _write(tmp_path, "Inner_View.yaml", LEFT)
    _write(tmp_path, "Middle_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: inner, view: Inner_View.yaml}\n")
    _write(tmp_path, "Outer_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: middle, view: Middle_View.yaml}\n")
    view = View(tmp_path / "Outer_View.yaml")
    assert view.embedded("middle").embedded("inner").node("title").get("text") == "Left"


# -- errors -----------------------------------------------------------------------------------

def test_a_missing_file_names_the_node_and_the_file(tmp_path):
    _write(tmp_path, "Host_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: gone, view: Gone_View.yaml}\n")
    with pytest.raises(FileNotFoundError, match="Gone_View.yaml"):
        View(tmp_path / "Host_View.yaml")


def test_a_static_view_with_bindings_or_handlers_is_an_error(tmp_path):
    _write(tmp_path, "Wired_View.yaml", COUNTER)  # bindings and handlers, and no Wired_ViewModel.py
    _write(tmp_path, "Host_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: w, view: Wired_View.yaml}\n")
    with pytest.raises(ValueError, match=r'widget "w".*label, bump.*no Wired_ViewModel.py'):
        View(tmp_path / "Host_View.yaml")


def test_with_for_a_view_with_no_viewmodel_is_an_error(tmp_path):
    _write(tmp_path, "Left_View.yaml", LEFT)
    _write(tmp_path, "Host_View.yaml", "id: root\nkind: Container\nchildren:\n  - {id: l, view: Left_View.yaml, with: {a: 1}}\n")
    with pytest.raises(ValueError, match="`with:` \\['a'\\] is for a ViewModel"):
        View(tmp_path / "Host_View.yaml")


def test_a_with_the_viewmodel_does_not_take_is_an_error(folder):
    path, name = folder
    _write(path, "Host_View.yaml", f"id: root\nkind: Container\nchildren:\n  - {{id: c, view: {name}_View.yaml, with: {{nope: 1}}}}\n")
    with pytest.raises(ValueError, match="nope"):
        View(path / "Host_View.yaml")


# -- changes ----------------------------------------------------------------------------------

def test_a_host_reload_keeps_an_embedded_view_whose_request_did_not_change(folder):
    _, view = _host(folder[0])
    before = view.embedded("counter")
    spec = yaml.safe_load((folder[0] / "Host_View.yaml").read_text())
    spec["style"]["height"] = 120  # something else changed
    view.reconcile(spec)
    assert view.embedded("counter") is before


def test_a_changed_request_builds_a_new_one_and_a_removed_node_takes_it_away(folder):
    path, name = folder
    _, view = _host(path)
    old = view.embedded("counter")
    spec = yaml.safe_load((path / "Host_View.yaml").read_text())
    spec["children"][1]["with"] = {"start": 9}
    view.reconcile(spec)
    new = view.embedded("counter")
    assert new is not old and new.node("label").get("text") == "count 9"
    assert old not in view._components and new in view._components
    spec["children"].pop(0)  # `left` gone
    view.reconcile(spec)
    with pytest.raises(ValueError, match="no view: node"):
        view.embedded("left")


def test_a_new_view_node_is_built_while_running(folder):
    path, _ = folder
    _, view = _host(path)
    spec = yaml.safe_load((path / "Host_View.yaml").read_text())
    spec["children"].append({"id": "again", "view": "Left_View.yaml"})
    view.reconcile(spec)
    assert view.embedded("again").node("title").get("text") == "Left"


def test_a_failed_reload_leaves_the_embedded_views_alone(folder):
    path, _ = folder
    _, view = _host(path)
    keep = view.embedded("left")
    spec = yaml.safe_load((path / "Host_View.yaml").read_text())
    spec["children"].append({"id": "bad", "view": "Missing_View.yaml"})
    with pytest.raises(Exception):
        view.reconcile(spec)
    assert view.embedded("left") is keep


def test_the_embedded_files_are_watched_for_hot_reload(folder):
    path, _ = folder
    app, view = _host(path)
    assert view.embedded("left") in app._instances


def test_removing_the_host_component_takes_its_embedded_views_with_it(folder):
    path, _ = folder
    app = App(width=300, height=100, theme_seed=SEED)
    outer = View({"id": "root", "kind": "Container", "children": [{"id": "slot", "kind": "Container"}]}, window=app.window)
    app.window.root.add_child(outer.root)
    from tesserae.component import embed

    component, _vm = embed(outer, path / "Host_View.yaml", outer.node("slot"))
    inner = component.embedded("left")
    component.remove()
    assert not inner._follow_alive()
