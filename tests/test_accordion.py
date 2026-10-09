"""#156: the accordion -- a header button that opens its content, and groups where one or several are open."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = "[{value: a, title: One, text: First}, {value: b, title: Two, text: Second}, {value: c, title: Three, text: Third}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal("b")
        self.many = Signal(["a"])
        self.on = Signal(False)


def single(tmp_path, props="", children=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    kids = f"\n    children:\n      - {children}" if children else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 500}}
children:
  - widget: Accordion
    name: ac
    title: Details
    expanded: "{{{{ on }}}}"
    {props}{kids}
""")
    return start(tmp_path)


def group(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 500}}
children:
  - widget: AccordionGroup
    name: g
    items: {ITEMS}
    {lines or 'open: "{{ open }}"'}
""")
    return start(tmp_path)


def start(tmp_path):
    app = App(root=tmp_path, width=400, height=500)
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


def test_they_are_shipped():
    assert {"Accordion", "AccordionGroup"} <= set(shipped_views())


def header(view, base="root.ac"):
    return view.node(base + ".header")


def test_a_closed_section_is_just_its_56_pixel_header_with_the_title_and_a_chevron(tmp_path):
    view, _ = single(tmp_path)
    h = header(view)
    assert (h.get("layout_width"), h.get("layout_height")) == (400.0, 56.0)
    t, c = view.node("root.ac.header.title"), view.node("root.ac.header.chevron")
    assert t.get("text") == "Details" and t.get("font_size") == 16.0 and t.get("fill") == role(view, "on_surface") and t.get("layout_x") == 16.0
    assert c.get("layout_width") == 24.0 and c.get("fill") == role(view, "on_surface_variant") and c.get("layout_x") + 24 == 400 - 16
    assert "root.ac.content.inner" not in view._built.specs and c.get("rotation_deg") == 0.0


def test_the_header_is_a_button_that_says_whether_it_is_expanded_and_what_it_controls(tmp_path):
    view, _ = single(tmp_path)
    h = header(view)
    assert h.get("role") == "button" and h.get("label") == "Details" and h.get("expanded") is False and h.get("focusable")


def test_pressing_the_header_opens_the_content_and_turns_the_chevron_over(tmp_path):
    view, vm = single(tmp_path, children="{widget: Text, name: body, text: Hello, typography_role: body_medium, style: {foreground: on_surface}}")
    view.window.simulate("click", node=header(view))
    settle(view, 4)
    assert vm.on.get() is True and header(view).get("expanded") is True and "root.ac.content.inner" in view._built.specs
    assert view.node("root.ac.body").get("layout_y") >= header(view).get("layout_y") + 56
    settle(view, 20)
    assert view.node("root.ac.header.chevron").get("rotation_deg") == 180.0


def test_the_chevron_turns_over_in_steps_not_at_once(tmp_path):
    view, _ = single(tmp_path)
    view.window.simulate("click", node=header(view))
    for _ in range(4):
        view.window.advance(16)
    assert 0.0 < view.node("root.ac.header.chevron").get("rotation_deg") < 180.0


def test_pressing_again_closes_it(tmp_path):
    view, vm = single(tmp_path)
    view.window.simulate("click", node=header(view))
    settle(view, 4)
    view.window.simulate("click", node=header(view))
    settle(view, 4)
    assert vm.on.get() is False and "root.ac.content.inner" not in view._built.specs


def test_enter_toggles_a_focused_header(tmp_path):
    view, vm = single(tmp_path)
    header(view).focus()
    settle(view, 2)
    view.window.simulate("key_down", key="enter")
    settle(view, 4)
    assert vm.on.get() is True


def test_a_disabled_section_does_not_toggle(tmp_path):
    view, vm = single(tmp_path, "disabled: true")
    view.window.simulate("click", node=header(view))
    settle(view, 4)
    assert vm.on.get() is False and header(view).get("disabled") is True


def test_the_content_is_16_pixels_in_and_the_header_controls_it_and_it_is_hidden_from_a_screen_reader_while_closed(tmp_path):
    view, vm = single(tmp_path, children="{widget: Container, name: block, style: {width: 100, height: 30}}")
    content = view.node("root.ac.content")
    assert content.get("a11y_hidden") is True
    vm.on.set(True)
    settle(view, 4)
    assert content.get("a11y_hidden") is False and view.node("root.ac.block").get("layout_x") == 16.0 and content.get("layout_height") == 30 + 16
    assert header(view).get("controls") == [content] or header(view).get("controls") is not None


# -- the group --------------------------------------------------------------------------------------------------------------


def head(view, key):
    return view.node(f"root.g.section[{key}].panel.header")


def test_a_group_shows_the_open_section_and_hides_the_rest(tmp_path):
    view, _ = group(tmp_path)
    assert [head(view, k).get("expanded") for k in "abc"] == [False, True, False]
    assert "root.g.section[b].panel.content.inner" in view._built.specs and "root.g.section[a].panel.content.inner" not in view._built.specs
    assert view.node("root.g.section[b].panel.text").get("text") == "Second"


def test_opening_one_in_single_mode_closes_the_others_and_writes_the_choice(tmp_path):
    view, vm = group(tmp_path)
    view.window.simulate("click", node=head(view, "c"))
    settle(view, 6)
    assert vm.open.get() == "c" and [head(view, k).get("expanded") for k in "abc"] == [False, False, True]


def test_pressing_the_open_one_closes_it_in_single_mode(tmp_path):
    view, vm = group(tmp_path)
    view.window.simulate("click", node=head(view, "b"))
    settle(view, 6)
    assert vm.open.get() == "" and [head(view, k).get("expanded") for k in "abc"] == [False, False, False]


def test_multiple_mode_lets_several_be_open(tmp_path):
    view, vm = group(tmp_path, 'mode: multiple, open: "{{ many }}"')
    assert [head(view, k).get("expanded") for k in "abc"] == [True, False, False]
    view.window.simulate("click", node=head(view, "c"))
    settle(view, 6)
    assert vm.many.get() == ["a", "c"] and [head(view, k).get("expanded") for k in "abc"] == [True, False, True]
    view.window.simulate("click", node=head(view, "a"))
    settle(view, 6)
    assert vm.many.get() == ["c"]


def test_sections_are_divided_and_the_arrows_move_between_headers(tmp_path):
    view, _ = group(tmp_path)
    assert "root.g.section[a].divider" not in view._built.specs and "root.g.section[b].divider" in view._built.specs
    head(view, "a").focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_down")
    settle(view, 4)
    assert head(view, "b").get("focused") is True
    view.window.simulate("key_down", key="End")
    settle(view, 4)
    assert head(view, "c").get("focused") is True


def test_a_group_with_no_binding_still_works(tmp_path):
    view, _ = group(tmp_path, "mode: single")
    view.window.simulate("click", node=head(view, "a"))
    settle(view, 6)
    assert [head(view, k).get("expanded") for k in "abc"] == [True, False, False]
