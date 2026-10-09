"""#143, #144, #145: LinearProgress, CircularProgress and LoadingIndicator in the view language -- a value, or none for a wait with no end."""

import pytest

from tesserae import App, Signal, ViewModel, a11y, tokens


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.done = Signal(0.25)
        self.loaded = Signal(0.5)


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 300, height: 200, gap: 8}\nchildren:\n" + body)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def control(view, name="p"):
    return view._built.controls[f"root.{name}"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def run(view, ms):
    for _ in range(max(1, ms // 16)):
        view.window.advance(16)


def test_a_linear_progress_with_a_value_fills_that_share(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, style: {width: 200}}\n")
    run(view, 400)
    p = control(view)
    assert p.value.get() == 0.5 and not p.indeterminate
    assert p.bar.get("translate_x") == pytest.approx(-100.0, abs=1) and view.node("root.p").get("layout_height") == 4.0
    assert p.node.get("fill") == role(view, "surface_container_highest") and p.bar.get("fill") == role(view, "primary")


def test_with_no_value_it_is_a_wait_with_no_end(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, style: {width: 200}}\n  - {widget: CircularProgress, name: c}\n")
    assert control(view).indeterminate and control(view, "c").indeterminate
    run(view, 300)
    assert control(view).bar.get("translate_x") > -0.4 * 200  # the bar is sweeping across


def test_an_empty_value_expression_is_a_wait_with_no_end_and_a_number_ends_it(tmp_path):
    class Wait(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.progress = Signal(None)

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 100}\nchildren:\n  - {widget: LinearProgress, name: p, value: \"{{ progress }}\", style: {width: 200}}\n")
    app = App(root=tmp_path)
    app.bind(Wait)
    view = app.open_view("Main")
    app.show("main")
    run(view, 100)
    vm = app.bindings.viewmodel_for("main")
    assert control(view).indeterminate
    vm.progress.set(0.75)
    run(view, 500)
    assert control(view).value.get() == 0.75 and control(view).bar.get("translate_x") == pytest.approx(-50.0, abs=1)
    vm.progress.set(None)
    run(view, 100)
    assert control(view).indeterminate


def test_the_value_follows_a_signal(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: CircularProgress, name: p, value: "{{ done }}"}\n')
    run(view, 400)
    assert control(view).arc.get("trim_end") == pytest.approx(0.25, abs=0.01)
    vm.done.set(0.9)
    run(view, 500)
    assert control(view).arc.get("trim_end") == pytest.approx(0.9, abs=0.01)


@pytest.mark.parametrize("value", ["'half'", "true"])
def test_a_value_that_is_not_a_number_names_the_widget(tmp_path, value):
    with pytest.raises(Exception, match='widget "root.p": value is a number from 0 to 1|takes a number|must be'):
        opened(tmp_path, f"  - {{widget: LinearProgress, name: p, value: {value}}}\n")


def test_a_track_role_recolours_the_track(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, track: secondary_container}\n"
                               "  - {widget: CircularProgress, name: c, value: 0.5, track: secondary_container}\n")
    assert control(view).node.get("fill") == role(view, "secondary_container")
    ring = control(view, "c").ring
    assert ring.get("visible") is True and ring.get("stroke_color") == role(view, "secondary_container")


def test_a_circle_has_no_track_unless_asked(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: c, value: 0.5}\n")
    assert control(view, "c").ring.get("visible") is False


def test_a_stop_indicator_is_a_dot_at_the_end_of_the_track(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, stop_indicator: true, style: {width: 200}}\n"
                               "  - {widget: LinearProgress, name: q, value: 0.5, style: {width: 200}}\n")
    stop = control(view).stop
    assert stop.get("visible") is True and stop.get("layout_width") == 4.0 and stop.get("corner_radius") == 2.0
    assert control(view, "q").stop.get("visible") is False


def test_a_buffer_is_a_lighter_bar_behind_the_value(tmp_path):
    view, vm = opened(tmp_path, '  - {widget: LinearProgress, name: p, value: 0.25, buffer: "{{ loaded }}", style: {width: 200}}\n')
    run(view, 400)
    p = control(view)
    assert p.loaded.get("visible") is True and p.loaded.get("translate_x") == pytest.approx(-100.0, abs=1)
    assert p.loaded.get("fill")[:3] == p.bar.get("fill")[:3] and p.loaded.get("fill")[3] < 255
    vm.loaded.set(1.0)
    run(view, 100)
    assert p.loaded.get("translate_x") == pytest.approx(0.0, abs=1)


def test_no_buffer_hides_it(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5}\n")
    assert control(view).loaded.get("visible") is False


def test_a_loading_indicator_is_always_a_wait_and_morphs(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LoadingIndicator, name: p}\n")
    p = control(view)
    first = p.shape.get("data")
    run(view, 700)
    assert p.indeterminate and p.shape.get("data") != first


def test_a_label_names_it_for_a_screen_reader_and_it_is_a_progress_bar(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, label: Uploading}\n")
    node = view.node("root.p")
    assert (node.get("role"), node.get("label")) == ("progressbar", "Uploading") and node.get("value") == 0.5


def test_it_says_busy_with_no_value_and_a_percentage_with_one(tmp_path, monkeypatch):
    sent = []
    real = a11y.apply_extras
    monkeypatch.setattr(a11y, "apply_extras", lambda node, props: sent.append(dict(props)) or real(node, props))
    opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.42}\n  - {widget: LinearProgress, name: q}\n")
    assert {"busy": False, "value_text": "42%"} in sent and {"busy": True, "value_text": None} in sent


def test_a_wait_stands_still_for_an_app_that_reduces_motion(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, style: {width: 200}}\n  - {widget: CircularProgress, name: c}\n", reduced_motion=True)
    run(view, 300)
    bar, arc = control(view).bar, control(view, "c").arc
    first = (bar.get("translate_x"), arc.get("rotation_deg"))
    run(view, 300)
    assert (bar.get("translate_x"), arc.get("rotation_deg")) == first and first[1] == 0.0


def test_the_old_syntax_without_a_value_is_still_a_bar_at_zero(tmp_path):
    from tesserae import View

    spec = {"id": "root", "kind": "Container", "style": {"width": 300, "height": 100},
            "children": [{"id": "p", "kind": "LinearProgress", "style": {"width": 200}}]}
    view = View(spec, theme_seed=(103, 80, 164, 255))
    assert view.control("p").value.get() == 0.0
