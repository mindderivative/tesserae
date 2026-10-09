"""A Container's `measured_width` and `measured_height` tell the view how big it is laid out."""

from tesserae import App


def opened(tmp_path, width=400):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstate: {w: 0, h: 0}\nstyle: {flex_direction: vertical, width: 100%, height: 100%}\nchildren:\n"
        "  - {widget: Container, name: box, measured_width: '{{ w }}', measured_height: '{{ h }}', style: {width: 100%, height: 50}}\n"
        "  - {widget: Text, name: t, text: \"{{ str(w) + 'x' + str(h) }}\", typography_role: body_medium, style: {foreground: on_surface}}\n")
    app = App(root=tmp_path, width=width, height=300)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    return app, view


def said(view):
    return view._built.specs["root.t"]["text"]["content"]


def test_the_size_is_written_after_layout(tmp_path):
    _, view = opened(tmp_path)
    assert said(view) == "400.0x50.0"


def test_it_is_written_again_when_the_window_resizes(tmp_path):
    app, view = opened(tmp_path)
    app.window.resize(300, 300)
    app.window.simulate("resize", width=300, height=300)
    for _ in range(6):
        view.window.advance(16)
    assert said(view) == "300.0x50.0"
