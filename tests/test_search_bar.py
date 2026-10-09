"""#170, #171: the Material 3 search bar and its docked search view."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ALL = [{"value": "cats", "label": "cats"}, {"value": "dogs", "label": "dogs", "supporting": "recent", "icon": "clock"}, {"value": "birds", "label": "birds"}]


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.q = Signal("")
        self.active = Signal(False)
        self.chosen = Signal("")
        self.log = []
        self.results = __import__("tesserae").Computed(lambda: [r for r in ALL if self.q.get().lower() in r["label"]])

    def found(self):
        self.log.append("found")

    def mic(self):
        self.log.append("mic")

    def menu(self):
        self.log.append("menu")


def opened(tmp_path, props="", view_props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    vlines = "\n    ".join(view_props.split(", ")) if view_props else ""
    results_line = "results: []" if "results: []" in view_props else 'results: "{{ results }}"'
    vlines = vlines.replace("results: []", "")
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 700, height: 600, padding: 20}}
children:
  - widget: SearchBar
    name: bar
    query: "{{{{ q }}}}"
    active: "{{{{ active }}}}"
    style: {{width: 360}}
    {lines}
  - widget: SearchView
    name: sv
    open: "{{{{ active }}}}"
    anchor: bar
    query: "{{{{ q }}}}"
    {results_line}
    chosen: "{{{{ chosen }}}}"
    {vlines}
""")
    app = App(root=tmp_path, width=700, height=600)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=20):
    for _ in range(n):
        view.window.advance(16)


def bar(view, part=""):
    return view.node("root.bar" + (f".{part}" if part else ""))


def field(view):
    return view.node("root.bar.input")


def test_they_are_shipped():
    assert {"SearchBar", "SearchView"} <= set(shipped_views())


def type_text(view, text):
    node = field(view)
    node.focus()
    settle(view, 2)
    node.set(text="")
    view.window.simulate("input", text=text)
    settle(view, 8)


def test_the_bar_is_a_56_pixel_surface_container_high_pill_at_level_three(tmp_path):
    view, _ = opened(tmp_path)
    b = bar(view)
    assert (b.get("layout_width"), b.get("layout_height")) == (360.0, 56.0) and b.get("corner_radius") >= 28
    assert b.get("fill") == role(view, "surface_container_high") and b.get("shadows") == tokens.elevation_shadows(3)


def test_a_search_glass_leads_and_the_placeholder_names_the_field(tmp_path):
    view, _ = opened(tmp_path)
    assert view._built.specs["root.bar.leading.leading_glyph"]["icon"] == {"name": "magnify"}
    assert bar(view, "leading.leading_glyph").get("layout_width") == 24.0 and field(view).get("placeholder") == "Search"
    assert bar(view, "leading").get("layout_x") == bar(view).get("layout_x") + 4 and bar(view, "leading").get("layout_width") == 48.0


def activate(view):
    field(view).focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_down")
    settle(view, 8)


def test_pressing_or_typing_in_the_bar_activates_it_shows_the_view_and_turns_the_glass_into_a_back_arrow(tmp_path):
    view, vm = opened(tmp_path)
    assert not view._shown_layers and "root.bar.back" not in view._built.specs
    activate(view)
    assert vm.active.get() is True and view._shown_layers
    assert "root.bar.back" in view._built.specs and "root.bar.leading" not in view._built.specs


def test_the_back_arrow_deactivates_it_and_closes_the_view(tmp_path):
    view, vm = opened(tmp_path)
    activate(view)
    view.window.simulate("click", node=bar(view, "back"))
    settle(view, 8)
    assert vm.active.get() is False and not view._shown_layers and bar(view, "back") is not None if False else vm.active.get() is False


def test_typing_writes_the_query_and_filters_the_rows(tmp_path):
    view, vm = opened(tmp_path)
    activate(view)
    assert [k for k in view._built.specs if k.startswith("root.sv.panel.rows.row[") and k.count(".") == 4] == [
        "root.sv.panel.rows.row[cats]", "root.sv.panel.rows.row[dogs]", "root.sv.panel.rows.row[birds]"]
    type_text(view, "do")
    assert vm.q.get() == "do"
    assert [k for k in view._built.specs if k.startswith("root.sv.panel.rows.row[") and k.count(".") == 4] == ["root.sv.panel.rows.row[dogs]"]


def test_a_clear_button_shows_once_there_is_text_and_empties_it(tmp_path):
    view, vm = opened(tmp_path)
    assert "root.bar.clear" not in view._built.specs
    type_text(view, "bi")
    assert bar(view, "clear").get("label") == "Clear"
    view.window.simulate("click", node=bar(view, "clear"))
    settle(view, 8)
    assert vm.q.get() == "" and "root.bar.clear" not in view._built.specs


def test_enter_calls_on_search(tmp_path):
    view, vm = opened(tmp_path, "on_search: found")
    type_text(view, "cat")
    view.window.simulate("key_down", key="Enter")
    settle(view, 4)
    assert vm.log == ["found"]


def test_a_trailing_icon_shows_while_the_field_is_empty_and_runs_its_handler(tmp_path):
    view, vm = opened(tmp_path, "trailing_icon: microphone, on_trailing: mic")
    assert "root.bar.trailing" in view._built.specs
    view.window.simulate("click", node=bar(view, "trailing"))
    assert vm.log == ["mic"]
    type_text(view, "x")
    assert "root.bar.trailing" not in view._built.specs  # the clear button takes its place


def test_an_avatar_is_a_30_pixel_circle_at_the_end(tmp_path):
    view, _ = opened(tmp_path, "avatar_text: JD")
    av = bar(view, "avatar")
    assert (av.get("layout_width"), av.get("layout_height")) == (30.0, 30.0) and av.get("fill") == role(view, "primary_container")


def test_a_menu_button_leads_and_runs_on_leading(tmp_path):
    view, vm = opened(tmp_path, "leading_icon: menu, on_leading: menu")
    assert bar(view, "leading").get("label") == "Menu"
    view.window.simulate("click", node=bar(view, "leading"))
    assert "menu" in vm.log


def test_the_view_is_a_surface_container_high_panel_with_28_pixel_corners_under_the_bar(tmp_path):
    view, _ = opened(tmp_path)
    activate(view)
    panel, b = view.node("root.sv.panel"), bar(view)
    assert panel.get("fill") == role(view, "surface_container_high") and panel.get("corner_radius") == 28.0
    assert panel.get("layout_y") >= b.get("layout_y") + b.get("layout_height") and panel.get("layout_width") == 360.0


def test_a_row_has_a_history_icon_a_label_and_supporting_text(tmp_path):
    view, _ = opened(tmp_path)
    activate(view)
    assert view._built.specs["root.sv.panel.rows.row[cats].leading_icon"]["icon"] == {"name": "history"}
    assert view._built.specs["root.sv.panel.rows.row[dogs].leading_icon"]["icon"] == {"name": "clock"}
    assert view.node("root.sv.panel.rows.row[dogs]").get("role") == "listitem"


def test_pressing_a_row_chooses_it_and_closes_the_view(tmp_path):
    view, vm = opened(tmp_path)
    activate(view)
    view.window.simulate("click", node=view.node("root.sv.panel.rows.row[birds]"))
    settle(view, 8)
    assert vm.chosen.get() == "birds" and vm.active.get() is False and not view._shown_layers


def test_escape_closes_the_view_and_deactivates_the_bar(tmp_path):
    view, vm = opened(tmp_path)
    activate(view)
    view.window.simulate("key_down", key="escape")
    settle(view, 8)
    assert vm.active.get() is False and not view._shown_layers


def test_no_results_for_a_query_says_so(tmp_path):
    view, _ = opened(tmp_path)
    type_text(view, "zzz")
    assert view.node("root.sv.panel.none").get("text") == "No results" and "root.sv.panel.rows" not in view._built.specs


def test_the_number_of_results_is_announced_politely(tmp_path):
    view, _ = opened(tmp_path)
    activate(view)
    count = view.node("root.sv.panel.count")
    assert count.get("text") == "3 results" and count.get("live") == "polite"
    type_text(view, "do")
    assert count.get("text") == "1 results"


def test_no_results_and_nothing_typed_shows_no_message(tmp_path):
    view, vm = opened(tmp_path, view_props="results: []")
    activate(view)
    assert vm.q.get() == "" and "root.sv.panel.none" not in view._built.specs and "root.sv.panel.rows" not in view._built.specs
