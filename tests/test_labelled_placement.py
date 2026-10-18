"""#281: a Checkbox, RadioButton or Switch with a `label:` is a row of the control and its text; where the view puts the control is where the row goes."""

import os

import pytest

from tesserae import App
from test_anchor_style import VM, opened, where  # noqa: F401  (the fixture builders)


def at(view, path):
    node = view.node(path)
    return node.get("layout_x"), node.get("layout_y"), node.get("layout_width"), node.get("layout_height")


def row(view, name="cb"):
    key = next(k for k in view._built.outer if k.endswith(f".{name}.field"))
    node = view._built.outer[key]
    return node.get("layout_x"), node.get("layout_y"), node.get("layout_width"), node.get("layout_height")


@pytest.mark.parametrize("widget", ["Checkbox", "RadioButton", "Switch"])
def test_the_row_is_placed_by_the_insets_with_or_without_a_label(tmp_path, widget):
    labelled = opened(tmp_path / "a", f"  - {{widget: {widget}, name: cb, label: ok, style: {{position: absolute, right: 8, bottom: 4}}}}\n")[1]
    x, y, w, h = row(labelled)
    assert x + w == 392.0 and y + h == 296.0  # 8 in from the right edge, 4 up from the bottom: the row, label and all
    bare = opened(tmp_path / "b", f"  - {{widget: {widget}, name: cb, style: {{position: absolute, right: 8, bottom: 4}}}}\n")[1]
    bx, by, bw, bh = at(bare, "root.cb")
    assert (bx + bw, by + bh) == (392.0, 296.0)


def test_x_and_y_place_the_row_where_the_wrapper_is_not_at_the_corner(tmp_path):
    view = opened(tmp_path, "  - {widget: Container, style: {position: absolute, x: 50, y: 60, width: 200, height: 100}, children: [{widget: Switch, name: cb, label: ok, style: {position: absolute, x: 20, y: 10}}]}\n")[1]
    assert row(view)[:2] == (70.0, 70.0)


def test_the_box_stays_at_the_start_of_the_row_and_the_label_follows_it(tmp_path):
    view = opened(tmp_path, "  - {widget: Checkbox, name: cb, label: ok, style: {position: absolute, x: 100, y: 50}}\n")[1]
    x, y, w, h = row(view)
    box = view.node("root.cb")
    assert box.get("layout_x") + x >= x and (x, y) == (100.0, 50.0) and w > box.get("layout_width")


def test_a_margin_and_a_flex_grow_are_the_rows(tmp_path):
    body = ("  - widget: Container\n    style: {flex_direction: horizontal, width: 300, height: 40}\n    children:\n"
            "      - {widget: Checkbox, name: cb, label: ok, style: {margin: {left: 30}, flex: fill}}\n"
            "      - {widget: Rect, name: next, style: {width: 20, height: 20, background: primary}}\n")
    view = opened(tmp_path, body)[1]
    x, _, w, _ = row(view)
    assert x == 30.0 and x + w == 280.0  # moved 30 in, grown to fill the room the Rect leaves


def test_a_stylesheet_rule_that_places_a_labelled_control_places_its_row(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("name: main\nwidget: Container\nstyle: {width: 400, height: 300}\nchildren:\n  - {widget: Checkbox, name: cb, label: ok}\n")
    app = App(root=tmp_path, width=400, height=300, stylesheet_spec={"styles": [{"widget": "Checkbox", "style": {"position": "absolute", "x": 120, "y": 90}}]})
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(50)
    assert row(view)[:2] == (120.0, 90.0)


def test_a_placement_that_follows_a_signal_moves_the_row(tmp_path):
    app, view, vm = opened(tmp_path, '  - {widget: Checkbox, name: cb, label: ok, style: {position: absolute, x: "{{ x }}", y: 10}}\n')
    assert row(view)[0] == 150.0
    vm.x.set(40)
    view.window.advance(50)
    assert row(view)[0] == 40.0


def test_a_label_is_hidden_with_the_control(tmp_path):
    app, view, vm = opened(tmp_path, '  - {widget: Checkbox, name: cb, label: ok, visible: "{{ show }}"}\n')
    assert view.node("root.cb.label").get("layout_width") > 0
    vm.show.set(False)
    view.window.advance(50)
    assert view._built.outer[next(k for k in view._built.outer if k.endswith(".cb.field"))].get("visible") is False


def test_a_labelled_control_can_be_the_anchor_of_a_node_and_can_anchor_to_one(tmp_path):
    body = ('  - {widget: Checkbox, name: cb, label: a long enough label, style: {position: absolute, x: 20, y: 100}}\n'
            '  - {widget: Rect, name: dot, style: {anchor: cb, placement: top_end, width: 12, height: 12, background: error}}\n'
            '  - {widget: Checkbox, name: tag, label: ok, style: {anchor: cb, placement: below}}\n')
    view = opened(tmp_path, body)[1]
    cx, cy, cw, ch = row(view)
    dx, dy = where(view, "root.dot")
    assert (dx + 6, dy + 6) == (cx + cw, cy)  # centred on the row's top end corner, not the box's
    tx, ty = row(view, "tag")[:2]
    assert (tx, ty) == (cx, cy + ch)  # the tag's row sits below the row


def test_an_unlabelled_control_is_unchanged(tmp_path):
    view = opened(tmp_path, "  - {widget: Switch, name: cb, style: {position: absolute, x: 30, y: 40}}\n")[1]
    assert at(view, "root.cb")[:2] == (30.0, 40.0)


def test_a_file_that_moves_a_labelled_control_moves_its_row(tmp_path):
    app, view, vm = opened(tmp_path, "  - {widget: Checkbox, name: cb, label: ok, style: {position: absolute, x: 10, y: 10}}\n")
    assert row(view)[:2] == (10.0, 10.0)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, background: surface}\nchildren:\n"
        "  - {widget: Checkbox, name: cb, label: ok, style: {position: absolute, x: 70, y: 80}}\n")
    from tesserae.spec.watch import ComposedWatcher
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library, doc: app._composed_rules(library, doc=doc)[0])
    stat = view.source.stat()
    os.utime(view.source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    assert watcher.poll() is True
    view.window.advance(50)
    assert row(view)[:2] == (70.0, 80.0)


def test_a_transition_on_x_eases_the_row(tmp_path):
    app, view, vm = opened(tmp_path, '  - {widget: Switch, name: cb, label: ok, style: {position: absolute, x: "{{ x }}", y: 10, transition: {x: 400}}}\n')
    assert row(view)[0] == 150.0
    vm.x.set(250)
    view.window.advance(100)
    assert 150.0 < row(view)[0] < 250.0
    view.window.advance(800)
    assert row(view)[0] == 250.0
