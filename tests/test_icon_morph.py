"""A glyph that changes eases into the next one (`transition: {icon: ms}` on an Icon): the toggle icons of an IconButton morph."""

import pytest

from tesserae import App
from tesserae.icons import ICONS, MDI_VIEW_BOX, icon_view_box


def opened(tmp_path, extra=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 400}}
children:
  - {{widget: IconButton, name: b, icon: add, selected_icon: remove, toggle: true, label: Play}}
{extra}""")
    app = App(root=tmp_path)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view


def data(view):
    return view.node("root.b.icon").get("data")


def click(view):
    view.window.simulate("click", node=view.node("root.b"))


def test_a_toggle_morphs_through_shapes_that_are_neither_glyph_and_ends_on_the_new_one(tmp_path):
    view = opened(tmp_path)
    play = data(view)
    click(view)
    assert data(view) == play  # it has not jumped
    view.window.advance(100)
    middle = data(view)
    view.window.advance(200)
    pause = data(view)
    assert middle not in (play, pause) and pause != play
    (tmp_path / "other").mkdir()
    fresh = opened(tmp_path / "other")
    click(fresh)
    fresh.window.advance(400)
    assert data(fresh) == pause


def test_the_glyph_comes_back_when_toggled_again(tmp_path):
    view = opened(tmp_path)
    play = data(view)
    click(view)
    view.window.advance(300)
    click(view)
    view.window.advance(300)
    assert data(view) == play


def test_a_reduced_motion_app_swaps_at_once(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 300}\nchildren:\n  - {widget: IconButton, name: b, icon: add, selected_icon: remove, toggle: true, label: Play}\n")
    app = App(root=tmp_path, reduced_motion=True)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    play = data(view)
    click(view)
    view.window.advance(16)
    assert data(view) != play


MDI = next(n for n in ICONS if icon_view_box(n) == MDI_VIEW_BOX)


def test_a_different_set_of_glyphs_cannot_morph_so_it_swaps(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 300}\nstate: {on: false}\nchildren:\n"
        f"  - {{widget: Icon, name: i, icon: \"{{{{ 'home' if not on else '{MDI}' }}}}\", style: {{foreground: on_surface, transition: {{icon: 300}}}}}}\n"
        "  - {widget: Rect, name: go, style: {width: 20, height: 20, background: primary}, handlers: {on_click: 'on = True'}}\n")
    assert icon_view_box("home") != icon_view_box(MDI)
    app = App(root=tmp_path)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    before = view.node("root.i").get("data")
    view.window.simulate("click", node=view.node("root.go"))
    view.window.advance(16)
    after = view.node("root.i").get("data")
    assert after != before
    view.window.advance(400)
    assert view.node("root.i").get("data") == after


def test_icon_transition_is_for_icons_only(tmp_path):
    from tesserae.spec import transition
    assert list(transition.plan("x", "Icon", {"transition": {"icon": 100}})) == ["data"]
    assert transition.plan("x", "Container", {"transition": {"icon": 100}}) == {}
    assert "data" not in transition.plan("x", "Icon", {"transition": {"all": 100}})
