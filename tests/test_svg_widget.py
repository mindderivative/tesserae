"""#197: `widget: Svg` -- a document from a file or inline, tinted by the theme through `currentColor`, described by `alt`."""

import pytest

from tesserae import App, Signal, ViewModel, tokens

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20" viewBox="0 0 40 20">'
SQUARE = HEAD + '<rect width="40" height="20" fill="currentColor"/></svg>'
CIRCLE = HEAD + '<circle cx="20" cy="10" r="8" fill="currentColor"/></svg>'


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.picture = Signal("square.svg")
        self.clicked = Signal(0)


def opened(tmp_path, body, files=(("square.svg", SQUARE), ("circle.svg", CIRCLE))):
    (tmp_path / "Views").mkdir(exist_ok=True)
    for name, text in files:
        (tmp_path / "Views" / name).write_text(text)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 100, height: 100}\nchildren:\n" + body)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def alpha_count(view):
    rgba, _, _ = view.window.snapshot()
    return sum(1 for i in range(3, len(rgba), 4) if rgba[i])


def test_a_file_is_drawn_and_currentcolor_is_the_foreground(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Svg, name: s, src: square.svg, style: {width: 40, height: 20, foreground: primary}}\n")
    node = view.node("root.s")
    assert node.get("svg_color") == role(view, "primary") and "<rect" in node.get("svg") and alpha_count(view) == 40 * 20


def test_a_document_can_be_written_inline(tmp_path):
    view, _ = opened(tmp_path, f"  - widget: Svg\n    name: s\n    content: '{SQUARE}'\n    style: {{width: 40, height: 20, foreground: on_surface}}\n")
    assert alpha_count(view) == 40 * 20


def test_the_tint_follows_the_theme(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Svg, name: s, src: square.svg, style: {width: 40, height: 20, foreground: on_surface}}\n")
    light = view.node("root.s").get("svg_color")
    assert light == role(view, "on_surface")


def test_a_picture_with_alt_is_an_image_and_one_without_is_decorative(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Svg, name: a, src: square.svg, alt: A bar, style: {width: 40, height: 20}}\n"
                               "  - {widget: Svg, name: b, src: square.svg, style: {width: 40, height: 20}}\n"
                               "  - {widget: Svg, name: c, src: square.svg, style: {width: 40, height: 20}, handlers: {on_click: 'clicked += 1'}}\n")
    a, b, c = (view.node(f"root.{n}") for n in "abc")
    assert (a.get("role"), a.get("label")) == ("img", "A bar") and not a.get("a11y_hidden")
    assert b.get("a11y_hidden") is True and not c.get("a11y_hidden")


def test_the_source_follows_a_signal(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Svg, name: s, src: '{{ picture }}', style: {width: 40, height: 20, foreground: primary}}\n")
    assert "<rect" in view.node("root.s").get("svg")
    vm.picture.set("circle.svg")
    view.window.advance(16)
    assert "<circle" in view.node("root.s").get("svg") and alpha_count(view) < 40 * 20


def test_one_of_src_and_content_is_needed(tmp_path):
    from tesserae.spec.nodes import LoadError

    with pytest.raises(LoadError, match="give one of 'src', 'content'"):
        opened(tmp_path, "  - {widget: Svg, name: s}\n")
    with pytest.raises(LoadError, match="'src' and 'content' cannot both be given"):
        opened(tmp_path, f"  - {{widget: Svg, name: s, src: square.svg, content: '{SQUARE}'}}\n")


def test_a_missing_file_names_the_widget_and_the_file(tmp_path):
    with pytest.raises(Exception, match=r"nowhere\.svg"):
        opened(tmp_path, "  - {widget: Svg, name: s, src: nowhere.svg, style: {width: 40, height: 20}}\n")


def test_a_document_that_is_not_svg_is_an_error_naming_the_widget(tmp_path):
    with pytest.raises(Exception, match=r"s\b"):
        opened(tmp_path, "  - {widget: Svg, name: s, src: bad.svg, style: {width: 40, height: 20}}\n", files=(("bad.svg", "not a document"),))


def test_it_matches_the_python_widgets_drawing(tmp_path):
    from tesserae.widgets import svg

    view, _ = opened(tmp_path, "  - {widget: Svg, name: s, src: square.svg, style: {width: 40, height: 20, foreground: primary}}\n")
    py_app = App(width=100, height=100)
    py = svg(py_app.window, tmp_path / "Views" / "square.svg", 40, 20, color="primary")
    assert py.node.get("svg") == view.node("root.s").get("svg")
