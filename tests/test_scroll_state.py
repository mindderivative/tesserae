"""#218: a ScrollView's position is drawn from `scroll_offset`, and what it reports (`scroll_offset`, `at_top`, `at_end`, `scroll_direction`) is
readable in expressions through the Signals or state names it is bound to."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.composed import scroll_direction, scroll_edges
from tesserae.spec.build import SpecBuildError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.y = Signal(0.0)
        self.top = Signal(True)
        self.end = Signal(False)
        self.way = Signal("none")


VIEW = """name: main
widget: Container
style: {flex_direction: vertical, width: 200, height: 200}
children:
  - widget: ScrollView
    name: s
    style: {width: 200, height: 100}
    %s
    children:
      - {widget: Container, name: tall, style: {width: 200, height: 500}}
  - {widget: Text, name: label, font_family: Roboto, font_size: 14, style: {foreground: "#000000"}, text: "{{ 'top' if top else ('end' if end else way) }}"}
"""


def opened(tmp_path, props='scroll_offset: "{{ y }}"\n    at_top: "{{ top }}"\n    at_end: "{{ end }}"\n    scroll_direction: "{{ way }}"'):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW % props)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def scroller(view):
    return view._built.outer["root.s"]


def settle(view):
    for _ in range(3):
        view.window.advance(16)


def test_the_outputs_start_at_the_top_of_a_view_that_has_not_scrolled(tmp_path):
    view, vm = opened(tmp_path)
    assert vm.top.get() is True and vm.end.get() is False and vm.way.get() == "none" and vm.y.get() == 0.0
    assert view.node("root.label").get("text") == "top"


def test_scrolling_reports_the_offset_the_direction_and_leaving_the_top(tmp_path):
    view, vm = opened(tmp_path)
    scroller(view).set(scroll_offset=120.0)
    settle(view)
    assert vm.y.get() == 120.0 and vm.top.get() is False and vm.end.get() is False and vm.way.get() == "down"
    assert view.node("root.label").get("text") == "down"
    scroller(view).set(scroll_offset=60.0)
    settle(view)
    assert vm.y.get() == 60.0 and vm.way.get() == "up"


def test_at_end_is_true_when_scrolled_as_far_as_it_goes(tmp_path):
    view, vm = opened(tmp_path)
    scroller(view).set(scroll_offset=10000.0)  # tre clamps it to the end: 500 content - 100 view
    settle(view)
    assert vm.y.get() == 400.0 and vm.end.get() is True and vm.top.get() is False
    assert view.node("root.label").get("text") == "end"


def test_setting_the_bound_signal_scrolls_the_view(tmp_path):
    view, vm = opened(tmp_path)
    vm.y.set(150.0)
    settle(view)
    assert scroller(view).get("scroll_offset") == 150.0 and vm.top.get() is False and vm.way.get() == "down"


def test_a_scroll_view_that_nothing_reads_keeps_its_own_position(tmp_path):
    view, _ = opened(tmp_path, props="classes: []")
    scroller(view).set(scroll_offset=90.0)
    settle(view)
    assert scroller(view).get("scroll_offset") == 90.0


def test_a_literal_offset_is_where_it_starts(tmp_path):
    view, _ = opened(tmp_path, props="scroll_offset: 75")
    assert scroller(view).get("scroll_offset") == 75.0


@pytest.mark.parametrize("offset", ["-5", "-0.5", "'far'", "true", ".nan"])
def test_a_bad_offset_names_the_widget(tmp_path, offset):
    with pytest.raises((SpecBuildError, Exception), match="scroll_offset"):
        opened(tmp_path, props=f"scroll_offset: {offset}")


def test_the_direction_follows_the_event_and_holds_when_nothing_moved():
    assert scroll_direction("none", 0.0, 10.0) == "down" and scroll_direction("down", 10.0, 4.0) == "up"
    assert scroll_direction("up", 5.0, 5.0) == "up" and scroll_direction("down", None, 5.0) == "down" and scroll_direction("down", 5.0, None) == "down"


def test_the_edges_are_within_half_a_pixel_and_unknown_until_laid_out():
    assert scroll_edges(0.0, 100.0, 500.0) == (True, False) and scroll_edges(0.5, 100.0, 500.0) == (True, False)
    assert scroll_edges(0.6, 100.0, 500.0) == (False, False)
    assert scroll_edges(400.0, 100.0, 500.0) == (False, True) and scroll_edges(399.5, 100.0, 500.0) == (False, True)
    assert scroll_edges(399.4, 100.0, 500.0) == (False, False)
    assert scroll_edges(0.0, 0.0, 0.0) == (True, False) and scroll_edges(0.0, 100.0, 0.0) == (True, False) and scroll_edges(0.0, 0.0, 500.0) == (True, False)
    assert scroll_edges(0.0, 100.0, 100.0) == (True, True)  # content that fits is at both ends
