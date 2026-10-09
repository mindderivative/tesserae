"""#227: `widget: Overlay` -- a layer over the window, anchored or modal, opened by `open` and closed by Escape or a press outside."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.shown = Signal(False)
        self.present = Signal(True)
        self.gap = Signal(0)
        self.log = []

    def toggle(self):
        self.shown.set(not self.shown.get())

    def picked(self):
        self.log.append("picked")


MENU = """name: main
widget: Container
style: {flex_direction: vertical, width: 400, height: 300}
children:
  - {widget: Container, name: trigger, style: {width: 100, height: 40, background: primary}, handlers: {on_click: toggle}}
  - widget: Overlay
    name: menu
    open: "{{ shown }}"
    anchor: trigger
    style: {width: 120, height: 80, background: surface_container}
    children:
      - {widget: Container, name: item, style: {width: 120, height: 40, background: secondary}, handlers: {on_click: picked}}
"""
MODAL = """name: main
widget: Container
style: {flex_direction: vertical, width: 400, height: 300}
children:
  - widget: Overlay
    name: dialog
    open: "{{ shown }}"
    modal: true
    children:
      - {widget: Container, name: card, style: {width: 200, height: 100, background: surface}, children: [{widget: Container, name: ok, style: {width: 50, height: 30, background: primary}, handlers: {on_click: picked}}]}
"""


def opened(tmp_path, text=MENU):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return app, view, app.bindings.viewmodel_for("main")


def layer(view, name="menu"):
    return view._built.nodes[f"root.{name}"]


def showing(view, name="menu"):
    return f"root.{name}" in view._shown_layers


def test_a_closed_overlay_takes_no_room_and_shows_nothing(tmp_path):
    _, view, _ = opened(tmp_path)
    assert not showing(view) and view.node("root.trigger").get("layout_y") == 0.0
    assert view._built.outer["root.menu"].get("layout_width") == 0.0


def test_opening_it_shows_the_layer_below_its_anchor(tmp_path):
    _, view, vm = opened(tmp_path)
    vm.shown.set(True)
    view.window.advance(16)
    anchor = view.node("root.trigger")
    node = layer(view)
    assert showing(view)
    assert node.get("layout_y") >= anchor.get("layout_y") + anchor.get("layout_height")  # on the side asked for
    assert node.get("layout_width") == 120.0 and view.node("root.menu.item").get("layout_height") == 40.0


def test_clicking_the_trigger_opens_and_closing_the_signal_hides(tmp_path):
    _, view, vm = opened(tmp_path)
    view.window.simulate("click", node=view.node("root.trigger"))
    view.window.advance(16)
    assert vm.shown.get() is True and showing(view)
    vm.shown.set(False)
    view.window.advance(16)
    assert not showing(view)


def test_escape_closes_it_and_writes_false_back(tmp_path):
    _, view, vm = opened(tmp_path)
    vm.shown.set(True)
    view.window.advance(16)
    view.window.simulate("key_down", key="escape")
    view.window.advance(16)
    assert vm.shown.get() is False and not showing(view)


def test_a_press_outside_closes_it(tmp_path):
    _, view, vm = opened(tmp_path)
    vm.shown.set(True)
    view.window.advance(16)
    view.window.simulate("pointer_down", x=390, y=290)
    view.window.simulate("pointer_up", x=390, y=290)
    view.window.advance(16)
    assert vm.shown.get() is False and not showing(view)


def test_its_content_works_while_it_is_open(tmp_path):
    _, view, vm = opened(tmp_path)
    vm.shown.set(True)
    view.window.advance(16)
    view.window.simulate("click", node=view.node("root.menu.item"))
    assert vm.log == ["picked"]


def test_a_modal_one_is_a_scrim_over_the_window_with_its_content_centred(tmp_path):
    _, view, vm = opened(tmp_path, MODAL)
    vm.shown.set(True)
    view.window.advance(16)
    scrim = layer(view, "dialog")
    window = view.window.root
    assert (scrim.get("layout_width"), scrim.get("layout_height")) == (window.get("layout_width"), window.get("layout_height"))
    assert scrim.get("fill")[3] == round(0.32 * 255)  # a 32% scrim
    card = view.node("root.dialog.card")
    assert card.get("layout_x") == (window.get("layout_width") - 200) / 2 and card.get("layout_y") == (window.get("layout_height") - 100) / 2


def test_a_modal_one_follows_the_window_size(tmp_path):
    app, view, vm = opened(tmp_path, MODAL)
    vm.shown.set(True)
    view.window.advance(16)
    view.window.simulate("resize", width=500, height=350)
    view.window.advance(16)
    scrim = layer(view, "dialog")
    assert (scrim.get("layout_width"), scrim.get("layout_height")) == (500.0, 350.0)


def test_a_modal_one_blocks_what_is_under_it_and_a_press_on_the_scrim_closes_it(tmp_path):
    _, view, vm = opened(tmp_path, MODAL.replace("children:\n  - widget: Overlay", "children:\n  - {widget: Container, name: under, style: {width: 400, height: 300, background: primary}, handlers: {on_click: picked}}\n  - widget: Overlay"))
    vm.shown.set(True)
    view.window.advance(16)
    view.window.simulate("pointer_down", x=5, y=5)
    view.window.simulate("pointer_up", x=5, y=5)
    view.window.advance(16)
    assert vm.log == [] and vm.shown.get() is False


def test_not_dismissible_ignores_escape(tmp_path):
    _, view, vm = opened(tmp_path, MODAL.replace("modal: true", "modal: true\n    dismissible: false"))
    vm.shown.set(True)
    view.window.advance(16)
    view.window.simulate("key_down", key="escape")
    view.window.advance(16)
    assert vm.shown.get() is True and showing(view, "dialog")


def test_an_open_that_is_not_a_signal_closes_for_good_until_it_goes_false(tmp_path):
    _, view, _ = opened(tmp_path, MODAL.replace('open: "{{ shown }}"', "open: true"))
    assert showing(view, "dialog")
    view.window.simulate("key_down", key="escape")
    view.window.advance(16)
    assert not showing(view, "dialog")
    view._effect._run()  # a re-sync does not open it again
    assert not showing(view, "dialog")


def test_a_view_that_goes_takes_its_layers_with_it(tmp_path):
    _, view, vm = opened(tmp_path)
    vm.shown.set(True)
    view.window.advance(16)
    view.close()
    assert not view._shown_layers


def test_the_anchor_must_exist(tmp_path):
    _, view, vm = opened(tmp_path, MENU.replace("anchor: trigger", "anchor: nowhere"))
    with pytest.raises(Exception, match="anchor 'nowhere' is no node by that name"):
        vm.shown.set(True)


def test_a_bad_placement_is_a_load_error(tmp_path):
    with pytest.raises(LoadError, match="placement"):
        opened(tmp_path, MENU.replace("anchor: trigger", "anchor: trigger\n    placement: sideways"))


def test_taking_the_overlay_out_of_the_view_hides_its_layer(tmp_path):
    _, view, vm = opened(tmp_path, MENU.replace("  - widget: Overlay\n", "  - widget: Overlay\n    if: present\n"))
    vm.shown.set(True)
    view.window.advance(16)
    assert showing(view)
    vm.present.set(False)
    view.window.advance(16)
    assert not view._shown_layers


def test_a_change_to_the_view_while_it_is_open_keeps_a_modal_layer_the_size_of_the_window(tmp_path):
    _, view, vm = opened(tmp_path, MODAL.replace("    modal: true", "    modal: true\n    style: {gap: \"{{ gap }}\"}"))
    vm.shown.set(True)
    view.window.advance(16)
    vm.gap.set(4)  # restyles the layer: the patch puts back its own size, which the renderer sets again
    view.window.advance(16)
    scrim = layer(view, "dialog")
    assert scrim.get("layout_width") == view.window.root.get("layout_width")


@pytest.mark.parametrize("placement", ["above", "start", "end"])
def test_the_placement_picks_the_side_of_the_anchor(tmp_path, placement):
    text = MENU.replace("anchor: trigger", f"anchor: trigger\n    placement: {placement}").replace(
        "style: {width: 100, height: 40, background: primary}", "style: {width: 100, height: 40, background: primary, margin: {top: 120, left: 150}}")
    _, view, vm = opened(tmp_path, text)
    vm.shown.set(True)
    view.window.advance(16)
    anchor, node = view.node("root.trigger"), layer(view)
    ax, ay = anchor.get("layout_x"), anchor.get("layout_y")
    if placement == "above":
        assert node.get("layout_y") + node.get("layout_height") <= ay
    elif placement == "end":
        assert node.get("layout_x") >= ax + anchor.get("layout_width")
    else:
        assert node.get("layout_x") + node.get("layout_width") <= ax


def test_a_press_on_the_content_of_a_modal_one_does_not_close_it(tmp_path):
    _, view, vm = opened(tmp_path, MODAL)
    vm.shown.set(True)
    view.window.advance(16)
    card = view.node("root.dialog.card")
    x, y = card.get("layout_x") + 5, card.get("layout_y") + 5
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.simulate("pointer_up", x=x, y=y)
    view.window.advance(16)
    assert vm.shown.get() is True and showing(view, "dialog")
