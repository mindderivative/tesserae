"""#195: `widget: Text` -- the type scale, headings for a screen reader, and MD3's tracking when a theme asks for it."""

import pytest

from tesserae import App, View, ViewModel, tokens
from tesserae.spec.nodes import LoadError

SEED = (103, 80, 164, 255)

#: Material 3's type scale: role -> (size, line height in px)
MD3 = {
    "display_large": (57, 64), "display_medium": (45, 52), "display_small": (36, 44),
    "headline_large": (32, 40), "headline_medium": (28, 36), "headline_small": (24, 32),
    "title_large": (22, 28), "title_medium": (16, 24), "title_small": (14, 20),
    "body_large": (16, 24), "body_medium": (14, 20), "body_small": (12, 16),
    "label_large": (14, 20), "label_medium": (12, 16), "label_small": (11, 16),
}


class VM(ViewModel):
    views = "main"


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 300, height: 300}\nchildren:\n" + body)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view


@pytest.mark.parametrize("role, size_and_line", sorted(MD3.items()))
def test_every_type_role_is_the_md3_size_and_line_height(tmp_path, role, size_and_line):
    view = opened(tmp_path, f"  - {{widget: Text, name: t, text: Hello, typography_role: {role}, style: {{foreground: on_surface}}}}\n")
    node = view.node("root.t")
    size, line = size_and_line
    assert node.get("font_size") == size and round(node.get("font_size") * node.get("line_height")) == line


def test_a_heading_is_a_heading_of_its_level(tmp_path):
    view = opened(tmp_path, "  - {widget: Text, name: t, text: Title, typography_role: headline_large, heading: 2, style: {foreground: on_surface}}\n"
                            "  - {widget: Text, name: p, text: Body, typography_role: body_large, style: {foreground: on_surface}}\n")
    t, p = view.node("root.t"), view.node("root.p")
    assert (t.get("role"), t.get("level")) == ("heading", 2) and p.get("role") != "heading"


def test_a11y_on_the_node_beats_heading(tmp_path):
    view = opened(tmp_path, "  - {widget: Text, name: t, text: Title, typography_role: headline_large, heading: 2, a11y: {level: 3}, style: {foreground: on_surface}}\n")
    assert (view.node("root.t").get("role"), view.node("root.t").get("level")) == ("heading", 3)


@pytest.mark.parametrize("level", [0, 7, "big"])
def test_a_heading_level_is_one_to_six(tmp_path, level):
    with pytest.raises(LoadError, match="heading"):
        opened(tmp_path, f"  - {{widget: Text, name: t, text: Title, heading: {level}, typography_role: body_large, style: {{foreground: on_surface}}}}\n")


def test_text_follows_a_signal(tmp_path):
    from tesserae import Signal

    class Greeting(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.name = Signal("Ada")

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 100}\nchildren:\n"
        "  - {widget: Text, name: t, text: \"Hello {{ name }}, you have {{ 3 + 4 }} notes\", typography_role: body_large, style: {foreground: on_surface}}\n")
    app = App(root=tmp_path)
    app.bind(Greeting)
    view = app.open_view("Main")
    assert view.node("root.t").get("text") == "Hello Ada, you have 7 notes"
    app.bindings.viewmodel_for("main").name.set("Grace")
    assert view.node("root.t").get("text") == "Hello Grace, you have 7 notes"


def test_tracking_is_not_applied_unless_a_theme_asks(tmp_path):
    view = opened(tmp_path, "  - {widget: Text, name: t, text: Hello, typography_role: body_large, style: {foreground: on_surface}}\n")
    assert view.node("root.t").get("letter_spacing") == 0.0


def test_md3_tracking_is_a_theme_away(tmp_path):
    spec = {"typography": tokens.MD3_TRACKING_TYPOGRAPHY}
    view = opened(tmp_path, "  - {widget: Text, name: t, text: Hello, typography_role: body_large, style: {foreground: on_surface}}\n"
                            "  - {widget: Text, name: d, text: Hello, typography_role: display_large, style: {foreground: on_surface}}\n"
                            "  - {widget: Text, name: own, text: Hello, typography_role: body_large, letter_spacing: 2, style: {foreground: on_surface}}\n",
                  default_theme_spec=spec)
    assert view.node("root.t").get("letter_spacing") == 0.5 and view.node("root.d").get("letter_spacing") == -0.25
    assert view.node("root.own").get("letter_spacing") == 2.0  # the node's own wins


def test_a_theme_can_set_one_roles_tracking(tmp_path):
    view = opened(tmp_path, "  - {widget: Text, name: t, text: Hello, typography_role: label_large, style: {foreground: on_surface}}\n"
                            "  - {widget: Text, name: u, text: Hello, typography_role: body_large, style: {foreground: on_surface}}\n",
                  default_theme_spec={"typography": {"label_large": {"tracking": 1.5}}})
    assert view.node("root.t").get("letter_spacing") == 1.5 and view.node("root.u").get("letter_spacing") == 0.0


def test_a_text_input_keeps_its_own_tracking(tmp_path):
    view = opened(tmp_path, "  - {widget: TextInput, name: i, text: '', typography_role: body_large, style: {width: 100, height: 30, background: '#FFFFFF', foreground: '#000000'}}\n",
                  default_theme_spec={"typography": tokens.MD3_TRACKING_TYPOGRAPHY})
    assert view.node("root.i").get("kind") == "text_input"  # builds: a text input has no letter spacing for a theme to set


def test_the_md3_tracking_table_is_every_role():
    assert set(tokens.MD3_TRACKING) == set(tokens.TYPE_SCALE)
