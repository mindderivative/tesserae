"""M51 Phase 2: components keep their file, so hot reload can find them
(M51, named whatever Q1 says). `tesserae.instantiate` records the file
on the component; a reload that rebuilds a component's root keeps it in
place among its siblings (a `Repeater`'s rows keep their order); and a
host reload that destroys a component's nodes forgets it, unwired.
"""

import importlib.util
import sys

from tesserae import View, instantiate
from tesserae.spec import expand_components_to_spec

HOST = """
id: root
kind: Container
style: {flex_direction: vertical, width: 300, height: 300}
children:
  - id: rows
    kind: Container
    style: {flex_direction: vertical, width: 280, height: 280}
"""

ROW = """
id: row
kind: Rect
style: {width: 260, height: 32, background: "#112233"}
bindings: {width: "{{ size.get() }}"}
"""


ROW_VM = """
from tesserae import Signal, ViewModel


class RowViewModel(ViewModel):
    def __init__(self, view, size=100):
        self.size = Signal(size)
        super().__init__(view)
"""


def _vm_class(tmp_path):
    path = tmp_path / "Row_ViewModel.py"
    path.write_text(ROW_VM)
    spec = importlib.util.spec_from_file_location(f"Row_ViewModel_{id(tmp_path)}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # the naming check finds the class's file through it
    spec.loader.exec_module(module)
    return module.RowViewModel


def _host(tmp_path):
    (tmp_path / "Host_View.yaml").write_text(HOST)
    (tmp_path / "Row_View.yaml").write_text(ROW)
    return View(tmp_path / "Host_View.yaml"), tmp_path / "Row_View.yaml", _vm_class(tmp_path)


def test_instantiate_keeps_the_components_file(tmp_path):
    host, row, Row_ViewModel = _host(tmp_path)
    component, _ = instantiate(host, row, Row_ViewModel, host.node("rows"))
    assert component.path == row
    assert host.instantiate("", host.node("rows"), spec={"id": "x", "kind": "Rect", "style": {"background": "#000000"}}).path is None


def test_a_rebuilt_root_keeps_its_place_among_its_siblings(tmp_path):
    host, row, Row_ViewModel = _host(tmp_path)
    rows = [instantiate(host, row, Row_ViewModel, host.node("rows"), size=100 + i)[0] for i in range(3)]
    middle = rows[1]
    changed = expand_components_to_spec(ROW.replace("id: row", "id: row2"))  # a new root id: rebuilt
    middle.reconcile(changed)
    children = host.node("rows").children()
    assert children.index(middle.root) == 1 and len(children) == 3
    assert middle.root.get("width") == 101.0  # rewired to its own ViewModel


def test_a_host_reload_that_destroys_a_components_nodes_forgets_it(tmp_path):
    host, row, Row_ViewModel = _host(tmp_path)
    component, vm = instantiate(host, row, Row_ViewModel, host.node("rows"))
    assert host._components == [component]
    spec = expand_components_to_spec(HOST.replace("id: rows", "id: rows2"))
    host.reconcile(spec)  # `rows` is gone (a new id): destroyed, and the row with it
    assert host._components == []
    vm.size.set(5)  # its bindings are gone: nothing to update, nothing raises
    component.remove()  # a Repeater removing it later is fine too


def test_a_live_component_survives_its_hosts_reload(tmp_path):
    host, row, Row_ViewModel = _host(tmp_path)
    component, _ = instantiate(host, row, Row_ViewModel, host.node("rows"))
    host.reconcile(expand_components_to_spec(HOST.replace("width: 300", "width: 320")))
    assert host._components == [component] and component.root.parent() == host.node("rows")
