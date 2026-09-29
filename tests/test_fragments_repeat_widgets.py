"""M56 (#9): the five widgets `repeat:` couldn't declare faithfully,
because their items differ (the selected one looks different), now have
fragments. Each item fragment takes a `selected` flag and picks its
colours with M55's `{if:}`; each container fragment repeats it over an
`items` list. Checked against the imperative widgets (`tesserae.widgets`),
which stay the path for live selection.
"""

import pytest
import yaml
from tre import Window

from tesserae import View
from tesserae.overlays import Menu
from tesserae.spec import expand_components_to_spec
from tesserae.widgets import button_group, navigation_drawer, navigation_rail, tabs

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _view(component, with_):
    spec = expand_components_to_spec(yaml.safe_dump({"id": "w", "component": component, "with": with_}))
    view = View(spec, theme_seed=SEED)
    view.window.advance(16)
    return view


def _widget_window():
    window = Window(width=600, height=400)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    return window


def _rel(node, root):
    return (round(node.get("layout_x") - root.get("layout_x")), round(node.get("layout_y") - root.get("layout_y")),
            round(node.get("layout_width")), round(node.get("layout_height")))


@pytest.mark.parametrize("selected", [0, 1, 2])
@pytest.mark.parametrize("icons", [None, ["home", "search", "settings"]])
def test_tabs(selected, icons):
    labels = ["Alpha", "Beta", "Gamma"]
    items = [{"label": text, **({"icon": icons[i]} if icons else {}), **({"selected": True} if i == selected else {})}
             for i, text in enumerate(labels)]
    view = _view("Tabs", {"items": items, "item_width": 90})
    window = _widget_window()
    widget = tabs(window, labels, icons, selected=selected, width=270, theme=view.theme)
    window.advance(16)
    for i in range(3):
        for part in ("label", *(["icon"] if icons else [])):
            assert view.node(f"w.item.{i}.{part}").get("fill") == widget.part(f"item{i}.{part}").get("fill"), (i, part)
        assert _rel(view.node(f"w.item.{i}.label"), view.root) == _rel(widget.part(f"item{i}.label"), widget.node)
    indicator = view.node(f"w.item.{selected}.indicator")
    assert indicator.get("fill") == widget.indicator.get("fill") == view.theme.role("primary")
    label = view.node(f"w.item.{selected}.label")
    assert indicator.get("layout_x") == label.get("layout_x") and indicator.get("layout_width") == label.get("layout_width")
    assert indicator.get("layout_y") - view.root.get("layout_y") == widget.indicator.get("y")
    unselected = view.node(f"w.item.{(selected + 1) % 3}.indicator")
    assert unselected.get("fill")[3] == 0  # clear: only the selected tab shows one
    assert view.node("w.divider").get("fill") == view.theme.role("surface_variant")


@pytest.mark.parametrize("selected", [0, 1])
def test_navigation_rail(selected):
    labels, icons = ["Home", "Search"], ["home", "search"]
    items = [{"label": text, "icon": icons[i], **({"selected": True} if i == selected else {})}
             for i, text in enumerate(labels)]
    view = _view("NavigationRail", {"items": items})
    window = _widget_window()
    widget = navigation_rail(window, labels, icons, selected=selected, theme=view.theme)
    window.advance(16)
    for i in range(2):
        for part in ("pill", "icon", "label"):
            assert view.node(f"w.item.{i}.{part}").get("fill") == widget.part(f"item{i}.{part}").get("fill"), (i, part)
            assert _rel(view.node(f"w.item.{i}.{part}"), view.root) == _rel(widget.part(f"item{i}.{part}"), widget.node)
    assert _rel(view.root, view.root)[2:] == _rel(widget.node, widget.node)[2:]


@pytest.mark.parametrize("selected", [0, 1])
def test_navigation_drawer(selected):
    labels, icons = ["Inbox", "Sent"], ["home", "search"]
    items = [{"label": text, "icon": icons[i], **({"selected": True} if i == selected else {})}
             for i, text in enumerate(labels)]
    view = _view("NavigationDrawer", {"items": items, "width": 360, "item_width": 336})
    window = _widget_window()
    widget = navigation_drawer(window, labels, icons, selected=selected, theme=view.theme)
    window.advance(16)
    for i in range(2):
        assert view.node(f"w.item.{i}").get("fill") == widget.part(f"item{i}").get("fill"), i
        for part in ("icon", "label"):
            assert view.node(f"w.item.{i}.{part}").get("fill") == widget.part(f"item{i}.{part}").get("fill"), (i, part)
        assert _rel(view.node(f"w.item.{i}.label"), view.root) == _rel(widget.part(f"item{i}.label"), widget.node)
    assert view.root.get("fill") == widget.node.get("fill")


def test_menu_panel():
    view = _view("Menu", {"items": [{"label": "Cut"}, {"label": "Copy"}, {"label": "Paste"}], "width": 200})
    window = _widget_window()
    menu = Menu(window, [("Cut", None), ("Copy", None), ("Paste", None)], width=200, theme=view.theme)
    menu.open_at(0, 0)
    window.advance(16)
    for i in range(3):
        slot, item = view.node(f"w.item.{i}"), menu.items[i]
        assert _rel(slot, view.root) == _rel(item, menu.node), i
        assert view.node(f"w.item.{i}.label").get("fill") == menu.widget.part(f"item{i}.label").get("fill")
    assert view.root.get("fill") == menu.node.get("fill") and view.root.get("corner_radius") == menu.node.get("corner_radius")


@pytest.mark.parametrize("button, variant", [("ButtonFilled", "filled"), ("ButtonOutlined", "outlined"),
                                             ("ButtonText", "text")])
def test_button_group(button, variant):
    view = _view("ButtonGroup", {"items": [{"label": "Day"}, {"label": "Week"}, {"label": "Month"}],
                                 "width": 80, "height": 40, "corner_radius": 20, "button": button})
    window = _widget_window()
    widget = button_group(window, ["Day", "Week", "Month"], 80, 40, variant=variant, theme=view.theme)
    window.advance(16)
    for i in range(3):
        assert _rel(view.node(f"w.b.{i}"), view.root) == _rel(widget.part(f"b{i}"), widget.node), i
        assert view.node(f"w.b.{i}").get("fill") == widget.part(f"b{i}").get("fill")
        assert view.node(f"w.b.{i}").get("corner_radius") == widget.part(f"b{i}").get("corner_radius") == 20.0


def test_button_group_defaults_to_filled_buttons():
    view = _view("ButtonGroup", {"items": [{"label": "A"}], "width": 80, "height": 40, "corner_radius": 20})
    assert view.node("w.b.0").get("fill") == view.theme.role("primary")
