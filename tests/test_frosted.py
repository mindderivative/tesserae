"""Frosted navigation, search and menus (step 72): `frosted: true` makes the surface 72% of its colour with a 20 pixel backdrop blur."""

import pytest

from tesserae import App, tokens

ITEMS = "[{value: a, label: Alpha, icon: home}, {value: b, label: Beta, icon: search}]"
ROWS = "[{value: a, label: Alpha}, {value: b, label: Beta}]"

# (widget line, the node holding the surface, the colour role it has)
CASES = {
    "rail": (f"{{widget: NavigationRail, name: w, items: {ITEMS}%s}}", "root.w", "surface"),
    "drawer": (f"{{widget: NavigationDrawer, name: w, items: {ITEMS}%s}}", "root.w", "surface"),
    "bar": ("{widget: SearchBar, name: w%s}", "root.w", "surface_container_high"),
    "top": ("{widget: TopAppBar, name: w, title: Notes%s}", "root.w", "surface"),
    "menu": (f"{{widget: Menu, name: w, open: '{{{{ o }}}}', items: {ROWS}%s}}", "root.w.surface", "surface_container"),
    "search": (f"{{widget: SearchView, name: w, open: '{{{{ o }}}}'%s}}", "root.w.panel", "surface_container_high"),
    "modal": (f"{{widget: NavigationDrawerModal, name: w, open: '{{{{ o }}}}', items: {ITEMS}%s}}", "root.w.sheet", "surface_container_low"),
}


def opened(tmp_path, case, frosted):
    line, node_id, role = CASES[case]
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstate: {o: true}\nstyle: {width: 500, height: 400, align_content: top_left}\nchildren:\n  - "
        + line % (", frosted: true" if frosted else "") + "\n")
    app = App(root=tmp_path, width=500, height=400)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, node_id, role


@pytest.mark.parametrize("case", sorted(CASES))
def test_frosted_is_a_translucent_surface_with_a_backdrop_blur(tmp_path, case):
    view, node_id, role = opened(tmp_path, case, True)
    node = view.node(node_id)
    colour = (view._scheme or tokens.BASELINE)[role]
    assert node.get("fill")[:3] == colour[:3] and node.get("fill")[3] == round(0.72 * 255)
    assert node.get("backdrop_blur") == 20.0


@pytest.mark.parametrize("case", sorted(CASES))
def test_the_default_is_solid_with_no_blur(tmp_path, case):
    view, node_id, role = opened(tmp_path, case, False)
    node = view.node(node_id)
    assert node.get("fill") == (view._scheme or tokens.BASELINE)[role] and node.get("backdrop_blur") == 0.0


def test_a_top_app_bar_keeps_its_scrolled_colour_when_frosted(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 500, height: 300}\nchildren:\n  - {widget: TopAppBar, name: w, title: T, scrolled: true, frosted: true}\n")
    app = App(root=tmp_path, width=500, height=300)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    fill = view.node("root.w").get("fill")
    assert fill[:3] == (view._scheme or tokens.BASELINE)["surface_container"][:3] and fill[3] == round(0.72 * 255)
