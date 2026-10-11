"""#261 (part of #257): "the parent's size minus something" in the flow needs no calc: `flex: fill` with margins or a gap is exact. What cannot be said
(an absolute node stretched between two edges) is asked of tre in `design/tre-requests/absolute-insets.md`; the tests say what tre does today."""

import pytest

from tesserae import App, ViewModel


class VM(ViewModel):
    views = "main"


def opened(tmp_path, body, head_style="width: 300, height: 200, flex_direction: vertical"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"name: main\nwidget: Container\nstyle: {{{head_style}}}\nchildren:\n" + body)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    return view


def test_the_full_width_minus_a_gutter_is_flex_fill_with_margins(tmp_path):
    view = opened(tmp_path, "  - {widget: Rect, name: a, style: {height: 20, background: primary, flex: expand_horizontal, margin: {left: 8, right: 8}}}\n")
    a = view.node("root.a")
    assert (a.get("layout_x"), a.get("layout_width")) == (8.0, 284.0)  # 100% - 16, from 8


def test_two_columns_with_a_gutter_are_two_fills_and_a_gap(tmp_path):
    body = ("  - widget: Container\n    name: row\n    style: {height: 20, gap: 16}\n    children:\n"
            "      - {widget: Rect, name: l, style: {height: 20, flex: fill, background: primary}}\n"
            "      - {widget: Rect, name: r, style: {height: 20, flex: fill, background: secondary}}\n")
    view = opened(tmp_path, body)
    left, right = view.node("root.row.l"), view.node("root.row.r")
    assert (left.get("layout_width"), right.get("layout_width")) == (142.0, 142.0)  # 50% - 8 each, the parent's 300 less the gap, halved
    assert right.get("layout_x") == left.get("layout_x") + 142.0 + 16.0


def test_the_rest_of_the_row_after_a_fixed_part_is_a_fill(tmp_path):
    body = ("  - widget: Container\n    name: row\n    style: {height: 20}\n    children:\n"
            "      - {widget: Rect, name: fixed, style: {width: 80, height: 20, background: primary}}\n"
            "      - {widget: Rect, name: rest, style: {height: 20, flex: fill, background: secondary}}\n")
    view = opened(tmp_path, body)
    assert view.node("root.row.rest").get("layout_width") == 220.0  # 100% - 80


def test_the_recipes_follow_the_parent_when_it_changes(tmp_path):
    view = opened(tmp_path, "  - {widget: Rect, name: a, style: {height: 20, background: primary, flex: expand_horizontal, margin: {left: 8, right: 8}}}\n")
    view.node("root").set(width=200.0)
    view.window.advance(32)
    assert view.node("root.a").get("layout_width") == 184.0  # still the parent less 16: layout does it, not a number set once


def test_what_tre_takes_for_a_size_today():
    """The facts the request rests on; if tre changes one, this fails and the request needs its first section rewritten."""
    import tre

    window = tre.Window(width=300, height=200)
    node = window.create("box")
    for ok in (40, 40.5, "auto", "50%"):
        node.set(width=ok)
    for bad in ("calc(100% - 16)", "100% - 16", "40px", "10vw", "fit-content", "stretch"):
        with pytest.raises(ValueError, match='must be a number, "auto", or a percentage'):
            node.set(width=bad)
    for prop in ("right", "bottom", "inset", "inset_right", "x2"):
        with pytest.raises(ValueError, match="unknown node property"):
            node.set(**{prop: 8.0})


def test_an_absolute_node_is_not_stretched_by_a_margin_today():
    import tre

    window = tre.Window(width=300, height=200)
    node = window.create("box", position="absolute", x=8.0, width="100%", height=20.0, margin_right=16.0)
    window.root.add_child(node)
    window.advance(32)
    assert (node.get("layout_x"), node.get("layout_width")) == (8.0, 300.0)  # past the parent: the case the request is for
