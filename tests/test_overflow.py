"""#260 (part of #257): `style.overflow` -- `hidden` and `visible`, another way to write `clip_children`."""

import pytest

from tesserae import App, ViewModel


class VM(ViewModel):
    views = "main"


def opened(tmp_path, panel_style, background="surface"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        f"name: main\nwidget: Container\nstyle: {{width: 300, height: 200, background: {background}}}\nchildren:\n"
        f"  - widget: Container\n    name: panel\n    style: {{position: absolute, x: 0, y: 0, width: 100, height: 100, background: surface_container_highest, {panel_style}}}\n"
        "    children:\n"
        "      - {widget: Rect, name: spill, style: {position: absolute, x: 80, y: 20, width: 60, height: 40, background: primary}}\n")
    app = App(root=tmp_path, theme_seed=(0x67, 0x50, 0xA4, 0xFF), dark=False)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view


def pixel(view, x, y):
    rgba, width, _ = view.window.snapshot()
    i = (y * width + x) * 4
    return tuple(rgba[i:i + 3])


def is_color(view, found, role, tolerance=3):
    want = tuple(round(c) for c in view.theme.role(role))[:3]
    return all(abs(a - b) <= tolerance for a, b in zip(found, want))


def test_hidden_cuts_what_spills_out_of_the_node(tmp_path):
    app, view = opened(tmp_path, "overflow: hidden")
    assert view.node("root.panel").get("clip_children") is True
    assert is_color(view, pixel(view, 90, 40), "primary")                      # inside the panel
    assert not is_color(view, pixel(view, 120, 40), "primary")                 # the part that spills past it is cut


def test_visible_lets_it_spill(tmp_path):
    app, view = opened(tmp_path, "overflow: visible")
    assert view.node("root.panel").get("clip_children") is False
    assert is_color(view, pixel(view, 120, 40), "primary")


def test_it_is_the_same_as_clip_children(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _, by_overflow = opened(tmp_path / "a", "overflow: hidden")
    _, by_clip = opened(tmp_path / "b", "clip_children: true")
    assert by_overflow.node("root.panel").get("clip_children") is by_clip.node("root.panel").get("clip_children") is True
    assert pixel(by_overflow, 120, 40) == pixel(by_clip, 120, 40)


def test_the_engine_style_has_clip_children_and_not_our_name_for_it():
    from tesserae.spec.layout import engine_style

    engine = engine_style("n", {"overflow": "hidden"})
    assert engine["clip_children"] is True and "overflow" not in engine
    assert engine_style("n", {"overflow": "visible"})["clip_children"] is False


def test_saying_both_the_same_way_is_fine(tmp_path):
    app, view = opened(tmp_path, "overflow: hidden, clip_children: true")
    assert view.node("root.panel").get("clip_children") is True


@pytest.mark.parametrize("style", ["overflow: hidden, clip_children: false", "clip_children: true, overflow: visible"])
def test_saying_both_differently_is_an_error_that_names_both(tmp_path, style):
    with pytest.raises(Exception, match=r"style\.overflow: \w+ and style\.clip_children: \w+ disagree; say one of them"):
        opened(tmp_path, style)


@pytest.mark.parametrize("value", ["scroll", "auto", "clip", "true"])
def test_a_value_that_is_not_hidden_or_visible_is_refused_naming_the_node(tmp_path, value):
    with pytest.raises(Exception, match="style.overflow must be one of hidden, visible"):
        opened(tmp_path, f"overflow: {value}")


def test_a_node_that_does_not_say_it_keeps_what_it_had(tmp_path):
    app, view = opened(tmp_path, "padding: 0")
    assert view.node("root.panel").get("clip_children") is False


def test_overflow_is_not_the_texts_own_overflow_property(tmp_path):
    """A Text has an `overflow` property (clip or ellipsis); the style field of the same name is the other thing."""
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 200}\nchildren:\n"
        "  - {widget: Text, name: t, text: 'a long line of text', overflow: ellipsis, wrap: none, typography_role: body_medium, style: {foreground: on_surface, width: 40, overflow: hidden}}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    t = view.node("root.t")
    assert t.get("clip_children") is True and t.get("overflow") == "ellipsis"
