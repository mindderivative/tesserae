"""#201: a status bar -- items at the start, centre and end, pressable ones, a progress edge, announced politely."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.clicked = Signal("")
        self.msg = Signal("Ready")
        self.pct = Signal(None)


ITEMS = "[{text: Ready}, {text: 'Ln 4, Col 2', side: end, value: goto, tooltip: Go to line}, {text: UTF-8, side: end, icon: home, value: encoding}, {text: Saved, side: center}]"


def opened(tmp_path, props="", items=ITEMS):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, width: 500, height: 300}}
children:
  - {{widget: Container, name: spacer, style: {{height: 276}}}}
  - {{widget: StatusBar, name: s, items: {items}, clicked: "{{{{ clicked }}}}"{', ' + props if props else ''}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def test_it_is_shipped():
    assert "StatusBar" in shipped_views()


def text(view, path):
    return view.node(f"root.s.{path}")


def test_it_is_a_24_pixel_surface_container_strip_the_width_of_its_place(tmp_path):
    view, _ = opened(tmp_path)
    bar = view.node("root.s")
    assert (bar.get("layout_width"), bar.get("layout_height")) == (500.0, 24.0) and bar.get("fill") == role(view, "surface_container")
    assert bar.get("layout_y") == 276.0


def test_the_items_sit_at_the_start_the_centre_and_the_end(tmp_path):
    view, _ = opened(tmp_path)
    left, mid, right = text(view, "section[start].note[Ready].note_text"), text(view, "section[center].note[Saved].note_text"), text(view, "section[end].item[goto].text")
    assert left.get("layout_x") < 20
    assert abs((mid.get("layout_x") + mid.get("layout_width") / 2) - 250) < 3
    assert right.get("layout_x") + right.get("layout_width") <= 500 - 8 - 4 + 1 and right.get("layout_x") > 300


def test_the_text_is_label_small_in_on_surface_variant(tmp_path):
    view, _ = opened(tmp_path)
    t = text(view, "section[start].note[Ready].note_text")
    assert t.get("font_size") == 11.0 and t.get("fill") == role(view, "on_surface_variant")


def test_an_item_with_a_value_is_a_button_and_pressing_it_reports_it(tmp_path):
    view, vm = opened(tmp_path)
    goto = text(view, "section[end].item[goto]")
    assert goto.get("role") == "button" and goto.get("label") == "Ln 4, Col 2" and goto.get("focusable")
    view.window.simulate("click", node=goto)
    view.window.advance(16)
    assert vm.clicked.get() == "goto"
    view.window.simulate("click", node=text(view, "section[end].item[encoding]"))
    view.window.advance(16)
    assert vm.clicked.get() == "encoding"


def test_an_item_with_no_value_is_not_pressable(tmp_path):
    view, vm = opened(tmp_path)
    note = text(view, "section[start].note[Ready]")
    assert not note.get("focusable")
    view.window.simulate("click", node=note)
    view.window.advance(16)
    assert vm.clicked.get() == ""


def test_an_item_can_have_an_icon_and_a_tooltip(tmp_path):
    view, _ = opened(tmp_path)
    assert text(view, "section[end].item[encoding].icon").get("layout_width") == 16.0
    goto = text(view, "section[end].item[goto]")
    view.window.simulate("pointer_move", x=goto.get("layout_x") + 4, y=goto.get("layout_y") + 4)
    for _ in range(40):
        view.window.advance(16)
    assert [t.get("text") for layer in view._tips.values() for t in layer[0].children()] == ["Go to line"]


def test_the_bar_is_announced_politely(tmp_path):
    view, _ = opened(tmp_path)
    assert view.node("root.s").get("live") == "polite" and view.node("root.s").get("role") == "group"


def test_it_follows_the_items_it_is_given(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {flex_direction: vertical, width: 500, height: 100}
children:
  - {widget: StatusBar, name: s, items: "{{ [{'text': msg}] }}"}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    assert text(view, "section[start].note[Ready].note_text").get("text") == "Ready"
    app.bindings.viewmodel_for("main").msg.set("Saving")
    for _ in range(4):
        view.window.advance(16)
    assert text(view, "section[start].note[Saving].note_text").get("text") == "Saving"


def test_a_progress_edge_shows_while_busy_or_given_a_value(tmp_path):
    view, vm = opened(tmp_path)
    assert "root.s.edge.bar" not in view._built.specs
    view2, _ = opened(tmp_path / "b" if (tmp_path / "b").mkdir() is None else tmp_path, "busy: true")
    bar = view2.node("root.s.edge.bar")
    assert (bar.get("layout_width"), bar.get("layout_height")) == (500.0, 4.0) and bar.get("layout_y") == 276.0
    (tmp_path / "c").mkdir()
    view3, _ = opened(tmp_path / "c", "progress: 0.5")
    assert view3.node("root.s.edge").get("layout_height") == 4.0


def test_text_and_width_are_for_a_bar_that_says_one_thing(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {flex_direction: vertical, width: 500, height: 100}
children:
  - {widget: StatusBar, name: s, text: Ready, width: 300}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    assert text(view, "section[start].note[Ready].note_text").get("text") == "Ready" and view.node("root.s").get("layout_width") == 300.0
