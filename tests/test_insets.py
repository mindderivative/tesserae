"""#279: `left`, `top`, `right`, `bottom` and `inset` are style fields (tre 0.5.7), sizes may be sums and `fit-content`, and a size or an inset tre would refuse is
refused where it is written."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError
from tesserae.spec.build import SpecBuildError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.edge = Signal("calc(100% - 16)")


HEAD = "name: main\nwidget: Container\nstyle: {width: 300, height: 100, background: surface}\nchildren:\n"


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(HEAD + body)
    app = App(root=tmp_path, width=300, height=100, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    return view


def box(style, extra=""):
    return f"  - {{widget: Rect, name: a, {extra}style: {{background: primary, {style}}}}}\n"


def frame(view, name="a"):
    node = view.node(f"root.{name}")
    return tuple(node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


def test_an_absolute_node_is_stretched_between_left_and_right(tmp_path):
    view = opened(tmp_path, box("position: absolute, left: 8, right: 16, height: 20"))
    assert frame(view)[0::2] == (8.0, 276.0)  # 300 - 8 - 16


def test_x_still_means_left(tmp_path):
    view = opened(tmp_path, box("position: absolute, x: 8, right: 16, height: 20"))
    assert frame(view)[0::2] == (8.0, 276.0)


def test_top_and_bottom_stretch_it_down(tmp_path):
    view = opened(tmp_path, box("position: absolute, top: 10, bottom: 30, width: 40"))
    assert frame(view)[1::2] == (10.0, 60.0)  # 100 - 10 - 30


def test_inset_is_all_four(tmp_path):
    view = opened(tmp_path, box("position: absolute, inset: 4"))
    assert frame(view) == (4.0, 4.0, 292.0, 92.0)


def test_an_inset_may_be_a_percentage_or_negative(tmp_path):
    view = opened(tmp_path, box("position: absolute, right: 10%, bottom: -4, width: 20, height: 10"))
    assert frame(view)[:2] == (250.0, 94.0)  # 300 - 20 - 30 ; 100 - 10 + 4


def test_a_node_in_the_flow_is_moved_from_its_place(tmp_path):
    flow = opened(tmp_path, box("width: 50, height: 20"))
    moved = opened(tmp_path / "moved", box("width: 50, height: 20, left: 10, top: 5"))
    assert (frame(moved)[0] - frame(flow)[0], frame(moved)[1] - frame(flow)[1]) == (10.0, 5.0)


@pytest.mark.parametrize("style, first, second", [("x: 8, left: 9", "x", "left"), ("y: 8, top: 9", "y", "top"), ("x: 8, inset: 4", "x", "inset"),
                                                  ("y: 8, inset: 4", "y", "inset")])
def test_two_ways_to_place_one_edge_are_refused_naming_both(tmp_path, style, first, second):
    with pytest.raises(LoadError) as caught:
        opened(tmp_path, box(f"position: absolute, {style}, width: 10, height: 10"))
    assert f"style.{first} and style.{second} both place the node" in str(caught.value) and "Main_View.yaml:5:" in str(caught.value)


def test_a_sum_is_a_size(tmp_path):
    view = opened(tmp_path, box("width: 'calc(100% - 16)', height: 20"))
    assert frame(view)[2] == 284.0
    view = opened(tmp_path / "bare", box("width: '100% - 16 + 4', height: 20"))
    assert frame(view)[2] == 288.0


def test_a_sum_given_by_an_expression_follows_it(tmp_path):
    view = opened(tmp_path, box("width: '{{ edge }}', height: 20"))
    assert frame(view)[2] == 284.0
    app_vm = view.handle.viewmodel
    app_vm.edge.set("100% - 40")
    view.window.advance(32)
    assert frame(view)[2] == 260.0


def test_a_sum_from_an_expression_that_tre_would_refuse_is_named_when_it_is_worked_out(tmp_path):
    with pytest.raises(SpecBuildError, match=r'widget "root.a": style.width must be .*got \'100%-16\'.*a space each side'):
        opened(tmp_path, box("width: \"{{ '100%-16' }}\", height: 20"))


def test_fit_content_is_a_text_size(tmp_path):
    view = opened(tmp_path, "  - {widget: Text, name: a, text: hello, typography_role: body_large, style: {width: fit-content, foreground: on_surface}}\n")
    assert 20 < frame(view)[2] < 80


@pytest.mark.parametrize("style, fragment", [
    ("width: 40px", "sizes are pixels already: write 40"),
    ("width: 10vw", "`vw` is not a unit here"),
    ("width: stretch", "flex: fill"),
    ("width: -3", "a number from 0"),
    ("min_width: 'calc(100% - 4)'", "style.min_width must be a number from 0, `auto` or a percentage"),
    ("flex_basis: fit-content", "style.flex_basis must be"),
    ("right: 'calc(100% - 4)'", "style.right must be a number, `auto` or a percentage"),
    ("left: 12px", "style.left must be"),
    ("inset: -5%", "style.inset must be"),
])
def test_a_size_or_inset_tre_would_refuse_is_found_at_load_with_its_position(tmp_path, style, fragment):
    with pytest.raises(LoadError) as caught:
        opened(tmp_path, box(f"position: absolute, {style}"))
    text = str(caught.value)
    assert "Main_View.yaml:5:" in text and fragment in text, text


def test_a_stylesheet_rule_is_checked_where_it_is_written(tmp_path):
    from tesserae.spec.rules import RuleSheet
    from tesserae.spec.nodes import load_marked

    text = "styles:\n  - widget: Rect\n    style: {width: 40px}\n"
    with pytest.raises(LoadError) as caught:
        RuleSheet.of(load_marked(text, "App_Stylesheet.yaml"), "App_Stylesheet.yaml", text)
    assert "App_Stylesheet.yaml:3:" in str(caught.value) and "sizes are pixels already" in str(caught.value)
    RuleSheet.of(load_marked("styles:\n  - widget: Rect\n    style: {width: 'calc(100% - 4)', right: 4, inset: 2}\n", "ok"), "ok", "")


def test_an_inset_cannot_ease_and_the_error_says_what_can(tmp_path):
    with pytest.raises(Exception) as caught:
        opened(tmp_path, box("position: absolute, left: 4, width: 10, height: 10, transition: {left: 200}"))
    assert "left" in str(caught.value) and "x" in str(caught.value) and "cannot ease" in str(caught.value)


def test_a_position_that_eases_is_x_and_y(tmp_path):
    view = opened(tmp_path, "  - {widget: Container, name: wrap, children: []}\n" + box("position: absolute, x: 0, y: 0, width: 10, height: 10, transition: {x: 200}"))
    assert frame(view)[0] == 0.0


def test_a_link_is_placed_by_insets(tmp_path):
    view = opened(tmp_path, "  - {widget: Link, name: a, text: more, style: {position: absolute, right: 8, bottom: 4}}\n")
    x, y, w, h = frame(view)
    assert abs((x + w) - (300 - 8)) < 1 and abs((y + h) - (100 - 4)) < 1


def test_a_control_is_placed_by_insets(tmp_path):
    view = opened(tmp_path, "  - {widget: Checkbox, name: a, style: {position: absolute, right: 8, bottom: 4}}\n")
    x, y, w, h = frame(view)
    assert abs((x + w) - (300 - 8)) < 1 and abs((y + h) - (100 - 4)) < 1


def test_a_box_made_in_python_takes_the_insets_in_its_style():
    from tesserae.spec.build import style_props

    assert style_props({"left": 4, "top": 2, "right": 6, "bottom": 8, "inset": 1}, None) == {"left": 4, "top": 2, "right": 6, "bottom": 8, "inset": 1}


def test_a_restyle_that_drops_an_inset_puts_the_node_back(tmp_path):
    view = opened(tmp_path, "  - {widget: Container, name: wrap, children: []}\n" + box("position: absolute, left: 8, right: 16, height: 20"),
                  stylesheet_spec={"styles": [{"widget": "Rect", "style": {"inset": 4}}]})
    assert frame(view)[0::2] == (8.0, 276.0)  # the node's own insets beat the rule's


def test_an_edge_beats_inset_whichever_of_them_the_rule_gave(tmp_path):
    """The cascade merges a rule's fields with the node's own; tre applies `inset` after the edges, so Tesserae works `inset` out itself."""
    view = opened(tmp_path, box("position: absolute, height: 20, right: 16"), stylesheet_spec={"styles": [{"widget": "Rect", "style": {"inset": 4, "height": 20}}]})
    assert frame(view)[0::2] == (4.0, 280.0)  # the rule's 4 for left; the node's 16 for right
    view = opened(tmp_path / "x", box("position: absolute, height: 20, x: 12"), stylesheet_spec={"styles": [{"widget": "Rect", "style": {"inset": 4}}]})
    assert frame(view)[0] == 12.0  # the node's `x` is its left edge


def test_a_rule_that_gives_an_edge_twice_is_refused_where_it_is_written():
    from tesserae.spec.rules import RuleSheet
    from tesserae.spec.nodes import load_marked

    text = "styles:\n  - widget: Rect\n    style: {x: 4, inset: 2}\n"
    with pytest.raises(LoadError, match="App_Stylesheet.yaml:3:.*style.x and style.inset both place the node"):
        RuleSheet.of(load_marked(text, "App_Stylesheet.yaml"), "App_Stylesheet.yaml", text)


def test_a_list_items_divider_is_drawn_along_its_bottom_edge(tmp_path):
    """It was absolutely positioned at `y: 100%` with no width, so it was 0 wide and never showed; it takes `left: 16, right: 0, bottom: 0` now."""
    view = opened(tmp_path, "  - {widget: ListItem, name: li, headline: One, supporting: two, divider: true, style: {width: 300}}\n")
    x, y, w, h = frame(view, "li.line")
    item = frame(view, "li")
    assert (x, w, h) == (16.0, 284.0, 1.0) and abs((y + h) - (item[1] + item[3])) < 1.5
