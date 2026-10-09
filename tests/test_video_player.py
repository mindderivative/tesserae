"""#198: the video player -- a picture surface with transport controls, frames supplied by the app."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


def frame(value):
    return (bytes([value, value, value, 255]) * 4, 2, 2)


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.playing = Signal(False)
        self.position = Signal(0.0)
        self.muted = Signal(False)
        self.frame = Signal(frame(10))
        self.wait = Signal(False)
        self.words = Signal("")


def opened(tmp_path, props="duration: 125"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split("; ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 500, height: 500, align_content: top_left}}
children:
  - widget: VideoPlayer
    name: vp
    frame: "{{{{ frame }}}}"
    playing: "{{{{ playing }}}}"
    position: "{{{{ position }}}}"
    muted: "{{{{ muted }}}}"
    buffering: "{{{{ wait }}}}"
    caption: "{{{{ words }}}}"
    {lines}
""")
    app = App(root=tmp_path, width=500, height=500)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def settle(view, n=6):
    for _ in range(n):
        view.window.advance(16)


def test_it_is_shipped():
    assert "VideoPlayer" in shipped_views()


def test_the_picture_is_the_size_asked_and_the_controls_are_under_it(tmp_path):
    view, _ = opened(tmp_path, "duration: 125; width: 400; height: 225")
    stage, controls = view.node("root.vp.stage"), view.node("root.vp.controls")
    assert stage.get("layout_width") == 400.0 and stage.get("layout_height") == 225.0
    assert controls.get("layout_y") >= stage.get("layout_y") + 225.0


def test_the_play_button_flips_playing_and_its_icon_and_label(tmp_path):
    view, vm = opened(tmp_path)
    play = view.node("root.vp.controls.play")
    assert play.get("label") == "Play" and view._built.specs["root.vp.controls.play.icon"]["icon"] == {"name": "play"}
    view.window.simulate("click", node=play)
    settle(view)
    assert vm.playing.get() is True and play.get("label") == "Pause" and view._built.specs["root.vp.controls.play.icon"]["icon"] == {"name": "pause"}
    view.window.simulate("click", node=play)
    settle(view)
    assert vm.playing.get() is False


def test_the_time_labels_show_minutes_and_seconds(tmp_path):
    view, vm = opened(tmp_path)
    assert view._built.specs["root.vp.controls.elapsed"]["text"]["content"] == "0:00" and view._built.specs["root.vp.controls.total"]["text"]["content"] == "2:05"
    vm.position.set(65.0)
    settle(view)
    assert view._built.specs["root.vp.controls.elapsed"]["text"]["content"] == "1:05"


def test_the_seek_slider_follows_position_and_dragging_writes_it(tmp_path):
    view, vm = opened(tmp_path)
    vm.position.set(40.0)
    settle(view)
    seek = view.node("root.vp.controls.seek")
    assert seek.get("value") == 40.0
    x, y = seek.get("layout_x"), seek.get("layout_y") + seek.get("layout_height") / 2
    assert seek.get("layout_width") == 280.0  # as wide as the row leaves
    view.window.simulate("pointer_down", x=x + 140, y=y)
    view.window.simulate("pointer_up", x=x + 140, y=y)
    settle(view)
    assert 60 < vm.position.get() < 65  # the middle of 0 to 125


def test_the_volume_button_flips_muted(tmp_path):
    view, vm = opened(tmp_path)
    vol = view.node("root.vp.controls.volume")
    assert vol.get("label") == "Mute"
    view.window.simulate("click", node=vol)
    settle(view)
    assert vm.muted.get() is True and vol.get("label") == "Unmute" and view._built.specs["root.vp.controls.volume.icon"]["icon"] == {"name": "volume_off"}


def test_a_new_frame_shows_in_the_picture(tmp_path):
    view, vm = opened(tmp_path)
    assert view.node("root.vp.stage.picture").get("rgba")[:3] == bytes([10, 10, 10])
    vm.frame.set(frame(200))
    settle(view)
    node = view.node("root.vp.stage.picture")
    assert (node.get("rgba")[:3], node.get("pixel_width")) == (bytes([200, 200, 200]), 2)


def test_buffering_shows_a_ring_and_a_caption_a_band(tmp_path):
    view, vm = opened(tmp_path)
    assert "root.vp.stage.wait" not in view._built.specs and "root.vp.stage.caption" not in view._built.specs
    vm.wait.set(True)
    vm.words.set("Hello there")
    settle(view)
    assert "root.vp.stage.wait" in view._built.specs and view._built.specs["root.vp.stage.caption.caption_text"]["text"]["content"] == "Hello there"


def test_the_seek_slider_is_off_without_a_duration(tmp_path):
    view, _ = opened(tmp_path, "duration: 0")
    assert view.node("root.vp.controls.seek").get("disabled") is True


def test_space_plays_m_mutes_and_the_arrows_step(tmp_path):
    view, vm = opened(tmp_path)
    view.node("root.vp.controls.seek").focus()
    view.window.simulate("key_down", key="space")
    settle(view)
    assert vm.playing.get() is True
    view.window.simulate("key_down", key="m")
    settle(view)
    assert vm.muted.get() is True


def test_the_arrows_step_position_and_stay_inside_the_video(tmp_path):
    view, vm = opened(tmp_path, "duration: 120; step: 10")
    view.node("root.vp.controls.seek").focus()
    view.window.simulate("key_down", key="arrow_right")
    settle(view)
    assert vm.position.get() == 10.0
    view.window.simulate("key_down", key="arrow_left")
    view.window.simulate("key_down", key="arrow_left")
    settle(view)
    assert vm.position.get() == 0.0
    vm.position.set(120.0)
    settle(view)
    view.window.simulate("key_down", key="arrow_right")
    settle(view)
    assert vm.position.get() == 120.0


def test_space_on_the_play_button_flips_playing_once(tmp_path):
    view, vm = opened(tmp_path)
    view.node("root.vp.controls.play").focus()
    view.window.simulate("key_down", key="space")
    settle(view)
    assert vm.playing.get() is True


def test_a_frame_that_is_not_a_frame_is_named(tmp_path):
    view, vm = opened(tmp_path)
    with pytest.raises(ValueError, match="a frame is"):
        vm.frame.set((bytes(4), 2, 2))
