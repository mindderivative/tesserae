"""#266: `surface.dismiss` in a handler closes the nearest `widget: Overlay` the widget is in: the layer hides, a bound `open` goes false, `on_dismiss` runs. It
did nothing in a view (it only found Python overlays)."""

import pytest

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal(True)
        self.inner = Signal(True)
        self.dismissed = []

    def on_closed(self):
        self.dismissed.append("outer")

    def on_inner_closed(self):
        self.dismissed.append("inner")


def opened(tmp_path, body, files=None):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, flex_direction: vertical, background: surface}\nchildren:\n" + body)
    for name, text in (files or {}).items():
        (tmp_path / "Views" / name).write_text(text)
    app = App(root=tmp_path, width=400, height=300)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(50)
    return app, view, app.bindings.viewmodel_for("main")


CLOSE = "{widget: Button, name: close, label: Close, handlers: {on_click: surface.dismiss}}"
ONE = f"""  - widget: Overlay
    name: dlg
    open: "{{{{ open }}}}"
    modal: true
    handlers: {{on_dismiss: on_closed}}
    style: {{width: 200, height: 100, background: surface_container_high}}
    children:
      - {CLOSE}
"""


def click(view, path):
    view.window.simulate("click", node=view.node(path))
    view.window.advance(50)


def test_dismiss_in_an_overlay_closes_it_and_writes_false_to_open(tmp_path):
    app, view, vm = opened(tmp_path, ONE)
    assert vm.open.get() is True and "root.dlg" in view._shown_layers
    click(view, "root.dlg.close")
    assert vm.open.get() is False and "root.dlg" not in view._shown_layers


def test_on_dismiss_runs_once(tmp_path):
    app, view, vm = opened(tmp_path, ONE)
    click(view, "root.dlg.close")
    assert vm.dismissed == ["outer"]


def test_it_can_be_opened_again_after_it_was_dismissed(tmp_path):
    app, view, vm = opened(tmp_path, ONE)
    click(view, "root.dlg.close")
    vm.open.set(True)
    view.window.advance(50)
    assert "root.dlg" in view._shown_layers


def test_an_overlay_whose_open_is_not_a_signal_stays_closed_until_it_goes_false(tmp_path):
    app, view, vm = opened(tmp_path, ONE.replace('open: "{{ open }}"', "open: true"))
    assert "root.dlg" in view._shown_layers
    click(view, "root.dlg.close")
    assert "root.dlg" not in view._shown_layers
    view.window.advance(50)
    assert "root.dlg" not in view._shown_layers


def test_a_button_in_a_view_the_overlay_calls_dismisses_it(tmp_path):
    body = ONE.replace(f"      - {CLOSE}\n", "      - {widget: Panel, name: panel}\n")
    app, view, vm = opened(tmp_path, body, {"Panel_View.yaml": f"widget: Container\nchildren:\n  - {CLOSE}\n"})
    assert "root.dlg" in view._shown_layers
    click(view, "root.dlg.panel.close")
    assert vm.open.get() is False and "root.dlg" not in view._shown_layers


def test_in_nested_overlays_the_inner_one_closes_and_the_outer_stays(tmp_path):
    nested = f"""  - widget: Overlay
    name: outer
    open: "{{{{ open }}}}"
    modal: true
    handlers: {{on_dismiss: on_closed}}
    style: {{width: 300, height: 200, background: surface_container_high}}
    children:
      - widget: Overlay
        name: inner
        open: "{{{{ inner }}}}"
        modal: true
        handlers: {{on_dismiss: on_inner_closed}}
        style: {{width: 100, height: 60, background: surface_container_highest}}
        children:
          - {CLOSE}
"""
    app, view, vm = opened(tmp_path, nested)
    click(view, "root.outer.inner.close")
    assert vm.inner.get() is False and vm.open.get() is True
    assert vm.dismissed == ["inner"]


def test_a_dismiss_outside_any_overlay_does_nothing_and_says_nothing(tmp_path):
    app, view, vm = opened(tmp_path, ONE.replace('open: "{{ open }}"', "open: false") + f"  - {CLOSE.replace('name: close', 'name: loose')}\n")
    click(view, "root.loose")  # no overlay holds it (the Overlay beside it is closed): nothing to close, and no error
    assert "root.dlg" not in view._shown_layers and vm.dismissed == []


def test_with_no_overlay_in_the_view_a_python_overlay_around_it_is_asked(tmp_path, monkeypatch):
    """A view shown inside a `tesserae.overlays` surface has no `widget: Overlay`: the old way, `dismiss_surface` from the view's root, is what runs."""
    import tesserae.overlays as overlays

    app, view, vm = opened(tmp_path, f"  - {CLOSE}\n")
    asked = []
    monkeypatch.setattr(overlays, "dismiss_surface", lambda node: asked.append(node) or True)
    click(view, "root.close")
    assert asked == [view.root]
