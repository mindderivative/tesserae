"""#280, step 2: `style: {anchor: name, placement: ..., offset: [dx, dy]}` places a node against another node of the view, in the tree (tre 0.5.7): it follows its anchor,
stays clipped by its parent, and is looked for, checked and cleaned up by Tesserae."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.build import SpecBuildError
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.show = Signal(True)
        self.x = Signal(150)
        self.place = Signal("top_end")
        self.rows = Signal([1, 2])


def opened(tmp_path, body, files=None, size="width: 400, height: 300"):
    (tmp_path / "Views").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"name: main\nwidget: Container\nstyle: {{{size}, background: surface}}\nchildren:\n" + body)
    for name, text in (files or {}).items():
        (tmp_path / "Views" / name).write_text(text)
    app = App(root=tmp_path, width=400, height=300)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(50)
    return app, view, app.bindings.viewmodel_for("main")


TARGET = '  - {widget: Rect, name: target, if: show, style: {position: absolute, x: "{{ x }}", y: 120, width: 60, height: 40, background: primary}}\n'
DOT = "  - {widget: Rect, name: dot, style: {anchor: target, placement: top_end, %s width: 12, height: 12, background: error}}\n"


def where(view, path="root.dot"):
    node = view.node(path)
    return node.get("layout_x"), node.get("layout_y")


def test_a_node_sits_on_the_corner_of_another(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + DOT % "")
    assert where(view) == (204.0, 114.0)  # its centre on the target's top-right corner (210, 120)


def test_an_offset_moves_it(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + DOT % "offset: [2, -2],")
    assert where(view) == (206.0, 112.0)


@pytest.mark.parametrize("placement, expected", [("below", (150.0, 160.0)), ("above", (150.0, 108.0)), ("start", (138.0, 120.0)), ("end", (210.0, 120.0)),
                                                 ("center", (174.0, 134.0)), ("bottom_start", (144.0, 154.0))])
def test_the_placements(tmp_path, placement, expected):
    app, view, vm = opened(tmp_path, TARGET + (DOT % "").replace("top_end", placement))
    assert where(view) == expected


def test_it_leaves_the_flow_by_itself(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + DOT % "")
    assert view.node("root.dot").get("position") == "absolute"


def test_it_follows_its_anchor_with_no_lag(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + DOT % "")
    vm.x.set(200)
    view.window.advance(16)
    assert where(view) == (254.0, 114.0)


def test_a_placement_that_is_an_expression_follows_it(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + (DOT % "").replace("placement: top_end", 'placement: "{{ place }}"'))
    assert where(view) == (204.0, 114.0)
    vm.place.set("center")
    view.window.advance(16)
    assert where(view) == (174.0, 134.0)


def test_when_the_anchor_goes_the_node_is_hidden_and_when_it_is_back_it_is_shown(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + DOT % "")
    vm.show.set(False)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is False
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is True and where(view) == (204.0, 114.0)


def test_a_node_that_says_visible_false_stays_hidden_when_its_anchor_returns(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + "  - {widget: Rect, name: dot, visible: false, style: {anchor: target, placement: top_end, width: 12, height: 12, background: error}}\n")
    vm.show.set(False)
    view.window.advance(16)
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is False


def test_the_anchor_may_be_the_parent(tmp_path):
    app, view, vm = opened(tmp_path, "  - widget: Container\n    name: host\n    style: {position: absolute, x: 100, y: 100, width: 80, height: 40}\n    children:\n"
                                      "      - {widget: Rect, name: dot, style: {anchor: parent, placement: top_end, width: 12, height: 12, background: error}}\n")
    assert where(view, "root.host.dot") == (174.0, 94.0)  # the host's top-right corner is (180, 100)


def test_in_a_for_each_row_the_name_means_its_own_rows_node(tmp_path):
    body = ("  - for: n in rows\n    key: n\n    widget: Container\n    name: row\n    style: {position: absolute, x: 20, y: \"{{ n * 100 }}\", width: 100, height: 40}\n    children:\n"
            "      - {widget: Rect, name: field, style: {width: 100, height: 40, background: primary}}\n"
            "      - {widget: Rect, name: badge, style: {anchor: field, placement: top_end, width: 10, height: 10, background: error}}\n")
    app, view, vm = opened(tmp_path, body)
    first, second = where(view, "root.row[1].badge"), where(view, "root.row[2].badge")
    assert first[1] < 100 and second[1] > 150  # each on its own row's field, not both on the first


def test_the_anchor_is_found_in_the_view_that_called_this_one(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + "  - {widget: Marker, name: m}\n", {"Marker_View.yaml":
                           "widget: Container\nchildren:\n  - {widget: Rect, name: dot, style: {anchor: target, placement: top_end, width: 12, height: 12, background: error}}\n"})
    assert where(view, "root.m.dot") == (204.0, 114.0)


def test_a_node_in_a_clipped_parent_is_clipped_like_any_child(tmp_path):
    body = ("  - widget: Container\n    name: box\n    style: {position: absolute, x: 250, y: 10, width: 100, height: 50, clip_children: true}\n    children:\n"
            "      - {widget: Rect, name: host, style: {position: absolute, x: 80, y: 5, width: 40, height: 30, background: primary}}\n"
            "      - {widget: Rect, name: dot, style: {anchor: host, placement: top_end, width: 12, height: 12, background: error}}\n")
    app, view, vm = opened(tmp_path, body)
    x = where(view, "root.box.dot")[0]
    assert x > 350 and view.node("root.box").get("clip_children") is True  # it sits past the box's right edge (350), and the box cuts it off


def test_a_stylesheet_rule_can_give_the_placement(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, background: surface}\nchildren:\n" + TARGET.replace('if: "{{ show }}", ', "") +
        "  - {widget: Rect, name: dot, classes: [badge], style: {width: 12, height: 12, background: error}}\n")
    app = App(root=tmp_path, width=400, height=300, stylesheet_spec={"styles": [{"classes": ["badge"], "widget": "Rect", "style": {"anchor": "target", "placement": "top_end"}}]})
    app.bind(VM)
    view = app.open_view("Main")
    view.window.advance(50)
    assert where(view) == (204.0, 114.0)


def test_when_the_style_stops_saying_it_the_node_goes_back_to_the_flow(tmp_path):
    app, view, vm = opened(tmp_path, TARGET + DOT % "")
    node = view.node("root.dot")
    assert node.get("position") == "absolute"
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, background: surface}\nchildren:\n" + TARGET +
        "  - {widget: Rect, name: dot, style: {width: 12, height: 12, background: error}}\n")
    from tesserae.spec.watch import ComposedWatcher
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library, doc: app._composed_rules(library, doc=doc)[0])
    import os
    stat = view.source.stat()
    os.utime(view.source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    assert watcher.poll() is True
    view.window.advance(50)
    assert view.node("root.dot").get("position") == "relative" and where(view)[0] < 100


@pytest.mark.parametrize("style, fragment", [
    ("anchor: ''", "style.anchor is the name of the node"),
    ("anchor: target, placement: above_end", "style.placement is one of"),
    ("anchor: target, offset: [1]", "style.offset is a pair of pixels"),
    ("anchor: target, offset: 3", "style.offset is a pair of pixels"),
])
def test_a_mistake_in_the_fields_is_found_at_load_with_its_position(tmp_path, style, fragment):
    with pytest.raises(LoadError) as caught:
        opened(tmp_path, TARGET + f"  - {{widget: Rect, name: dot, style: {{{style}, width: 12, height: 12, background: error}}}}\n")
    assert fragment in str(caught.value) and "Main_View.yaml:" in str(caught.value)


def test_an_anchor_no_node_has_is_named_with_the_nearest_name(tmp_path):
    with pytest.raises(ValueError) as caught:
        opened(tmp_path, TARGET + "  - {widget: Rect, name: dot, style: {anchor: tarbet, placement: top_end, width: 12, height: 12, background: error}}\n")
    assert "anchor 'tarbet' is no node by that name" in str(caught.value) and "did you mean 'target'" in str(caught.value)


def test_a_placement_worked_out_to_something_wrong_is_named(tmp_path):
    with pytest.raises(ValueError, match="style.placement is one of"):
        opened(tmp_path, TARGET + (DOT % "").replace("placement: top_end", "placement: \"{{ 'sideways' }}\""))


def test_an_overlay_in_a_row_sits_against_its_own_rows_node(tmp_path):
    """The lookup an Overlay's `anchor` uses prefers the node nearest it, so each row's popover opens by its own button."""
    body = ("  - for: n in rows\n    key: n\n    widget: Container\n    name: row\n    style: {position: absolute, x: 20, y: \"{{ n * 100 }}\", width: 100, height: 40}\n    children:\n"
            "      - {widget: Rect, name: field, style: {width: 100, height: 40, background: primary}}\n"
            "      - widget: Overlay\n        name: pop\n        anchor: field\n        placement: end\n        open: true\n        dismissible: false\n        children:\n"
            "          - {widget: Rect, name: dot, style: {width: 10, height: 10, background: error}}\n")
    app, view, vm = opened(tmp_path, body)
    first, second = where(view, "root.row[1].pop.dot"), where(view, "root.row[2].pop.dot")
    assert second[1] - first[1] == 100.0 and first[0] == second[0] == 120.0  # one row apart, each beside its own field


# -- #282: an anchor that is hidden hides the node anchored to it (tre leaves the node at the window's corner, drawn and pressable) ------------------

SHOWN = '  - {widget: Rect, name: target, visible: "{{ show }}", style: {position: absolute, x: 150, y: 120, width: 60, height: 40, background: primary}}\n'


def test_an_anchor_hidden_at_load_hides_the_node(tmp_path):
    body = '  - {widget: Rect, name: target, visible: false, style: {position: absolute, x: 150, y: 120, width: 60, height: 40, background: primary}}\n' + DOT % ""
    app, view, vm = opened(tmp_path, body)
    assert view.node("root.dot").get("visible") is False


def test_hiding_the_anchor_hides_the_node_at_once_and_showing_it_puts_it_back(tmp_path):
    app, view, vm = opened(tmp_path, SHOWN + DOT % "")
    assert view.node("root.dot").get("visible") is True and where(view) == (204.0, 114.0)
    vm.show.set(False)
    assert view.node("root.dot").get("visible") is False  # in the same step, before any frame can draw it at the corner
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is True and where(view) == (204.0, 114.0)


def test_an_anchor_in_a_hidden_container_hides_the_node(tmp_path):
    body = ('  - {widget: Container, name: box, visible: "{{ show }}", style: {position: absolute, x: 150, y: 120}, children: [{widget: Rect, name: target, style: {width: 60, height: 40, background: primary}}]}\n'
            + DOT % "")
    app, view, vm = opened(tmp_path, body)
    assert view.node("root.dot").get("visible") is True
    vm.show.set(False)
    assert view.node("root.dot").get("visible") is False
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is True and where(view) == (204.0, 114.0)


def test_the_nodes_own_visible_false_wins_when_the_anchor_is_shown_again(tmp_path):
    body = SHOWN + "  - {widget: Rect, name: dot, visible: false, style: {anchor: target, placement: top_end, width: 12, height: 12, background: error}}\n"
    app, view, vm = opened(tmp_path, body)
    vm.show.set(False)
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is False


def test_a_node_whose_own_visible_comes_while_the_anchor_is_hidden_stays_hidden(tmp_path):
    body = (SHOWN + '  - {widget: Rect, name: dot, visible: "{{ on }}", style: {anchor: target, placement: top_end, width: 12, height: 12, background: error}}\n')
    app, view, vm = opened(tmp_path, body.replace("{{ on }}", "{{ x > 100 }}"))
    vm.show.set(False)
    vm.x.set(50)
    vm.x.set(150)  # its own `visible:` goes false and true again while the anchor is hidden
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is False
    vm.show.set(True)
    view.window.advance(16)
    assert view.node("root.dot").get("visible") is True


def test_a_labelled_control_as_the_anchor_is_hidden_with_its_row(tmp_path):
    body = ('  - {widget: Checkbox, name: target, label: ok, visible: "{{ show }}", style: {position: absolute, x: 150, y: 120}}\n' + DOT % "")
    app, view, vm = opened(tmp_path, body)
    assert view.node("root.dot").get("visible") is True
    vm.show.set(False)
    assert view.node("root.dot").get("visible") is False


def test_the_node_is_shown_again_when_its_style_stops_saying_anchor_while_the_anchor_is_hidden(tmp_path):
    app, view, vm = opened(tmp_path, SHOWN + DOT % "")
    vm.show.set(False)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, background: surface}\nchildren:\n" + SHOWN +
        "  - {widget: Rect, name: dot, style: {width: 12, height: 12, background: error}}\n")
    from tesserae.spec.watch import ComposedWatcher
    import os
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library, doc: app._composed_rules(library, doc=doc)[0])
    stat = view.source.stat()
    os.utime(view.source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    assert watcher.poll() is True
    view.window.advance(50)
    assert view.node("root.dot").get("visible") is True


def test_the_anchor_may_be_in_the_view_that_called_this_one_and_hidden_there(tmp_path):
    files = {"Tag_View.yaml": "widget: Rect\nstyle: {anchor: target, placement: top_end, width: 12, height: 12, background: error}\n"}
    app, view, vm = opened(tmp_path, SHOWN + "  - {widget: Tag, name: tag}\n", files)
    assert view.node("root.tag").get("visible") is True
    vm.show.set(False)
    assert view.node("root.tag").get("visible") is False
