"""#226: elevation that eases on hover, press and drag -- a state rule gives a different `elevation` and `transition:` eases the shadows."""

import pytest

from tesserae import App, ViewModel, tokens


class VM(ViewModel):
    views = "main"


VIEW = """name: main
widget: Container
style: {flex_direction: vertical, width: 200, height: 200}
children:
  - widget: Container
    name: card
    classes: [lift]
    style: {width: 80, height: 80, background: surface_container_low}
    handlers: {on_click: noop}
"""
SHEET = {"styles": [
    {"widget": "Container", "classes": ["lift"], "style": {"elevation": 1, "transition": {"elevation": 200}}},
    {"widget": "Container", "classes": ["lift"], "state": "hovered", "style": {"elevation": 3}},
    {"widget": "Container", "classes": ["lift"], "state": "pressed", "style": {"elevation": 5}},
]}


class WithNoop(VM):
    def noop(self):
        pass


def opened(tmp_path, sheet=SHEET, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app = App(root=tmp_path, stylesheet_spec=sheet, **kwargs)
    app.bind(WithNoop)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view


def shadows(view):
    return view.node("root.card").get("shadows")


def centre(view):
    card = view.node("root.card")
    return card.get("layout_x") + 40, card.get("layout_y") + 40


def hover(view):
    x, y = centre(view)
    view.window.simulate("pointer_move", x=x, y=y)


def leave(view):
    view.window.simulate("pointer_move", x=150, y=150)


def level(n):
    return tokens.elevation_shadows(n)


def test_it_starts_at_its_own_level(tmp_path):
    _, view = opened(tmp_path)
    assert shadows(view) == level(1)


def test_hovering_lifts_it_by_easing_not_at_once(tmp_path):
    _, view = opened(tmp_path)
    hover(view)
    view.window.advance(16)
    mid = shadows(view)
    assert level(1) != mid != level(3)  # on its way
    assert level(1)[1][3] < mid[1][3] < level(3)[1][3]  # the ambient blur is between the two
    view.window.advance(400)
    assert shadows(view) == level(3)


def test_leaving_settles_it_back(tmp_path):
    _, view = opened(tmp_path)
    hover(view)
    view.window.advance(400)
    leave(view)
    view.window.advance(400)
    assert shadows(view) == level(1)


def test_pressing_lifts_it_higher_than_hovering_and_release_comes_back_to_hover(tmp_path):
    _, view = opened(tmp_path)
    hover(view)
    x, y = centre(view)
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.advance(400)
    assert shadows(view) == level(5)
    view.window.simulate("pointer_up", x=x, y=y)
    view.window.advance(400)
    assert shadows(view) == level(3)


def test_without_a_transition_the_change_is_at_once(tmp_path):
    sheet = {"styles": [{**r, "style": {k: v for k, v in r["style"].items() if k != "transition"}} for r in SHEET["styles"]]}
    _, view = opened(tmp_path, sheet)
    hover(view)
    view.window.advance(16)
    assert shadows(view) == level(3)


def test_an_app_that_reduces_motion_gets_the_level_at_once(tmp_path):
    app, view = opened(tmp_path)
    app.set_reduced_motion(True)
    hover(view)
    view.window.advance(16)
    assert shadows(view) == level(3)


def test_a_level_can_be_a_token_name(tmp_path):
    sheet = {"styles": [{"widget": "Container", "classes": ["lift"], "style": {"elevation": 1, "transition": {"elevation": 100}}},
                        {"widget": "Container", "classes": ["lift"], "state": "hovered", "style": {"elevation": "level_2"}}]}
    _, view = opened(tmp_path, sheet)
    hover(view)
    view.window.advance(300)
    assert shadows(view) == level(tokens.elevation("level_2"))


def test_a_press_in_the_middle_of_a_hover_retargets_from_where_it_is(tmp_path):
    _, view = opened(tmp_path)
    hover(view)
    view.window.advance(60)
    partway = shadows(view)
    x, y = centre(view)
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.advance(16)
    assert level(1)[1][3] < shadows(view)[1][3] and shadows(view) != level(3) and partway != shadows(view)
    view.window.advance(400)
    assert shadows(view) == level(5)


class DragVM(ViewModel):
    views = "main"

    def __init__(self):
        from tesserae import Signal

        super().__init__()
        self.dragging = Signal(False)


def test_a_drag_state_in_the_view_lifts_it_the_same_way(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 200, height: 200}\nchildren:\n"
        "  - {widget: Container, name: card, style: {width: 80, height: 80, background: surface, elevation: \"{{ 4 if dragging else 1 }}\","
        " transition: {elevation: 200}}}\n")
    app = App(root=tmp_path)
    app.bind(DragVM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    vm = app.bindings.viewmodel_for("main")
    assert shadows(view) == level(1)
    vm.dragging.set(True)
    view.window.advance(60)
    assert level(1) != shadows(view) != level(4)
    view.window.advance(400)
    assert shadows(view) == level(4)
    vm.dragging.set(False)
    view.window.advance(400)
    assert shadows(view) == level(1)
