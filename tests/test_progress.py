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


# -- #249: thicker sizes and the circular gap ------------------------------------------------------------------------------------


@pytest.mark.parametrize("thickness", [4, 8, 12])
def test_a_linear_bar_can_be_thicker(tmp_path, thickness):
    view, _ = opened(tmp_path, f"  - {{widget: LinearProgress, name: p, value: 0.5, thickness: {thickness}, stop_indicator: true, style: {{width: 200}}}}\n")
    c = control(view)
    assert c.node.get("layout_height") == c.bar.get("layout_height") == thickness and c.loaded.get("height") == thickness
    assert c.node.get("corner_radius") == thickness / 2 == c.bar.get("corner_radius")
    assert c.stop.get("layout_height") == min(4, thickness)  # the dot stays 4 px, or the bar's height if that is less


def test_the_standard_bar_is_four_pixels_and_a_thickness_below_one_pixel_is_refused(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, style: {width: 200}}\n")
    assert control(view).node.get("layout_height") == 4.0
    for n, bad in enumerate(("0", "-2", "wide")):
        (tmp_path / str(n)).mkdir()
        with pytest.raises(Exception, match="thickness"):
            opened(tmp_path / str(n), f"  - {{widget: LinearProgress, name: p, value: 0.5, thickness: {bad}}}\n")


def test_a_circle_can_be_thicker_and_keeps_a_two_pixel_margin(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5, thickness: 8, style: {width: 48}}\n")
    c = control(view)
    assert c.arc.get("stroke_width") == c.ring.get("stroke_width") == 8.0
    assert c.radius == 18.0 and "A18,18" in c.circle  # the outer edge of the stroke is where the 4 px ring's was


def test_a_larger_standard_circle_is_unchanged_and_a_thicker_one_keeps_the_same_outer_edge(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5, style: {width: 96}}\n")
    c = control(view)
    assert c.arc.get("stroke_width") == 4.0 and c.radius == 20.0  # the path has always been radius 20 of 48, scaled with the node
    (tmp_path / "thick").mkdir()
    view, _ = opened(tmp_path / "thick", "  - {widget: CircularProgress, name: p, value: 0.5, thickness: 8, style: {width: 96}}\n")
    thick = control(view)
    outer = lambda ring, size: (ring.radius * size / 48) + ring.thickness / 2  # noqa: E731
    assert outer(thick, 96) == pytest.approx(outer(c, 96))


def test_a_ring_too_thick_for_its_box_is_refused(tmp_path):
    with pytest.raises(Exception, match="thickness"):
        opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5, thickness: 40, style: {width: 48}}\n")


def test_the_track_leaves_a_gap_after_the_arc_and_before_the_top(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5, track: surface_container_highest, style: {width: 48}}\n")
    c = control(view)
    gap = c._gap
    assert gap == pytest.approx(8.0 / (2 * 3.141592653589793 * 20.0))  # the 4 px gap and the two 2 px caps, of the length of the ring
    assert c.arc.get("trim_end") == 0.5
    assert c.ring.get("trim_start") == pytest.approx(0.5 + gap) and c.ring.get("trim_end") == pytest.approx(1.0 - gap)


def test_with_nothing_done_the_track_is_whole_and_with_all_done_it_is_gone(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: '{{ done }}', track: surface_container_highest}\n")
    c = control(view)
    vm.done.set(0.0)
    run(view, 600)
    assert (c.ring.get("trim_start"), c.ring.get("trim_end")) == (0.0, 1.0)
    vm.done.set(1.0)
    run(view, 600)
    assert c.ring.get("trim_start") == c.ring.get("trim_end") == 1.0


def test_a_wait_has_a_whole_track_and_no_gap(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, track: surface_container_highest}\n")
    c = control(view)
    assert (c.ring.get("trim_start"), c.ring.get("trim_end")) == (0.0, 1.0)


def test_without_a_track_there_is_no_ring_to_trim(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5}\n")
    assert not control(view).ring.get("visible")


# -- #249: the two-bar sweep ------------------------------------------------------------------------------------------------------


def test_a_two_bar_wait_has_a_long_bar_and_a_short_one_a_little_behind(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, two_bar: true, style: {width: 200}}\n")
    c = control(view)
    assert c.bar2.get("visible") and c.bar.get("width") == pytest.approx(0.55 * 200) and c.bar2.get("width") == pytest.approx(0.3 * 200)
    assert c.bar2.get("translate_x") == -c.bar2.get("width")  # waiting off the left end for its turn
    run(view, 300)
    first = c.bar.get("translate_x")
    assert first > -c.bar.get("width")  # the long bar has started across
    assert c.bar2.get("translate_x") == -c.bar2.get("width")  # the short one has not
    run(view, 700)
    assert c.bar2.get("translate_x") > -c.bar2.get("width")  # now it has


def test_the_two_bars_keep_crossing_and_the_one_bar_sweep_is_still_the_default(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, two_bar: true, style: {width: 200}}\n  - {widget: LinearProgress, name: q, style: {width: 200}}\n")
    c, one = control(view), control(view, "q")
    seen = set()
    for _ in range(300):  # five seconds
        view.window.advance(16)
        seen.add(round(c.bar.get("translate_x") / 40))
    assert len(seen) > 4 and max(seen) * 40 > 150  # crossing the track and back to the start, more than once
    assert not one.bar2.get("visible") and one.bar.get("width") == pytest.approx(0.4 * 200)


def test_a_value_ends_a_two_bar_wait_and_hides_the_second_bar(tmp_path):
    class Wait(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.progress = Signal(None)

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 100}\nchildren:\n"
        "  - {widget: LinearProgress, name: p, value: \"{{ progress }}\", two_bar: true, style: {width: 200}}\n")
    app = App(root=tmp_path)
    app.bind(Wait)
    view = app.open_view("Main")
    app.show("main")
    run(view, 1000)
    vm, c = app.bindings.viewmodel_for("main"), control(view)
    assert c.indeterminate and c.bar2.get("visible")
    vm.progress.set(0.5)
    run(view, 600)
    assert not c.bar2.get("visible") and c.bar.get("width") == 200 and c.bar.get("translate_x") == pytest.approx(-100.0, abs=1)
    vm.progress.set(None)  # and a wait again starts both bars
    run(view, 100)
    assert c.indeterminate and c.bar2.get("visible")


def test_a_two_bar_wait_stands_still_for_an_app_that_reduces_motion(tmp_path, monkeypatch):
    from tesserae import motion

    monkeypatch.setattr(motion, "reduced", lambda window: True)
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, two_bar: true, style: {width: 200}}\n")
    c = control(view)
    run(view, 500)
    assert c.bar.get("translate_x") == pytest.approx((1 - 0.4) * 200 / 2) and not c.bar2.get("visible")


# -- #249: the contained loading indicator ---------------------------------------------------------------------------------------


def test_a_contained_loading_indicator_is_a_container_circle_with_the_shape_in_it(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LoadingIndicator, name: p, contained: true}\n  - {widget: LoadingIndicator, name: q}\n")
    p, plain = control(view), control(view, "q")
    assert p.node.get("fill") == role(view, "primary_container") and p.node.get("corner_radius") == 24.0
    assert p.shape.get("fill") == role(view, "on_primary_container") and (p.node.get("layout_width"), p.shape.get("layout_width")) == (48.0, 38.0)
    assert plain.shape.get("fill") == role(view, "primary") and plain.node.get("fill") != role(view, "primary_container")  # unchanged
    first = p.shape.get("data")
    run(view, 700)
    assert p.shape.get("data") != first  # it still morphs


def test_a_contained_indicator_takes_a_colour_for_its_shape(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LoadingIndicator, name: p, contained: true, style: {foreground: '#B3261E'}}\n")
    assert control(view).shape.get("fill") == (0xB3, 0x26, 0x1E, 255) and control(view).node.get("fill") == role(view, "primary_container")


# -- #249: wavy ---------------------------------------------------------------------------------------------------------------------


def test_a_wavy_bar_is_taller_by_the_waves_and_has_a_straight_track_under_it(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, wavy: true, style: {width: 200}}\n")
    c = control(view)
    assert c.node.get("layout_height") == 4 + 2 * c.AMPLITUDE == c.box
    assert c.track_line.get("visible") and c.track_line.get("layout_height") == 4.0 and c.track_line.get("layout_y") == c.AMPLITUDE
    assert c.track_line.get("fill") == role(view, "surface_container_highest") and c.node.get("fill") == (0, 0, 0, 0)  # the track is its own bar
    assert len(c.waves) == 2 and c.waves[0].get("stroke_color") == role(view, "primary") and c.waves[0].get("stroke_width") == 4.0
    assert c.bar.get("translate_x") == pytest.approx(-100.0, abs=1)  # half done: the bar and its wave are slid half out of the clip


def test_a_wavy_bar_is_a_sine_wave_a_crest_every_wavelength(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 1, wavy: true, style: {width: 200}}\n")
    c = control(view)
    points = [tuple(map(float, pair.split(","))) for pair in c._wave_data(80.0).lstrip("M").split(" L")]
    ys = [y for _, y in points]
    assert max(ys) == pytest.approx(c.box / 2 + c.AMPLITUDE) and min(ys) == pytest.approx(c.box / 2 - c.AMPLITUDE)
    start, end = points[0], points[-1]
    assert (start[0], end[0]) == (0.0, 80.0) and start[1] == pytest.approx(c.box / 2) and end[1] == pytest.approx(c.box / 2)  # whole wavelengths: it joins itself
    assert [round(x) for x, y in points if y == pytest.approx(c.box / 2 - c.AMPLITUDE, abs=0.01)][:2] == [10, 50]  # a crest a quarter wavelength in, every 40


def test_the_wave_flows_one_wavelength_at_a_time_and_goes_on(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 1, wavy: true, style: {width: 200}}\n")
    c = control(view)
    seen = []
    for _ in range(80):  # 1.3 s
        view.window.advance(16)
        seen.append(c.waves[0].get("translate_x"))
    assert min(seen) < -30 and max(seen) <= 0 and len({round(x) for x in seen}) > 10  # it moves along, and starts over (a whole wavelength is the same picture)
    assert any(b > a for a, b in zip(seen, seen[1:]))  # the jump back


def test_a_wavy_wait_sweeps_with_the_wave_inside_each_bar(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, two_bar: true, wavy: true, style: {width: 200}}\n")
    c = control(view)
    assert len(c.waves) == 2 and c.bar2.get("visible")
    run(view, 400)
    assert c.bar.get("translate_x") > -c.bar.get("width")


def test_a_wavy_bar_stands_still_for_an_app_that_reduces_motion(tmp_path, monkeypatch):
    from tesserae import motion

    monkeypatch.setattr(motion, "reduced", lambda window: True)
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 1, wavy: true, style: {width: 200}}\n")
    c = control(view)
    run(view, 500)
    assert c.waves[0].get("translate_x") == 0.0


def test_the_standard_bar_has_no_waves(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: LinearProgress, name: p, value: 0.5, style: {width: 200}}\n")
    c = control(view)
    assert c.waves == [] and not c.track_line.get("visible") and c.node.get("layout_height") == 4.0


def test_a_wavy_ring_is_a_wave_round_the_circle_that_flows(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 1, wavy: true, style: {width: 48}}\n")
    c = control(view)
    first = c.arc.get("data")
    assert c.arc.get("data") != c.circle  # not a plain arc
    run(view, 200)
    assert c.arc.get("data") != first  # the crests have moved
    assert c._middle == pytest.approx(20.0 - 1.5)  # the crests reach where the plain arc would, the middle line is a crest's less
    # every point of the wave stays between the troughs and the crests
    import re

    xy = [tuple(map(float, m)) for m in re.findall(r"(-?[\d.]+),(-?[\d.]+)", c.wave(0.7))]
    radii = [((x - 24) ** 2 + (y - 24) ** 2) ** 0.5 for x, y in xy]
    assert min(radii) == pytest.approx(18.5 - 1.5, abs=0.05) and max(radii) == pytest.approx(18.5 + 1.5, abs=0.05)


def test_a_wavy_ring_keeps_its_track_and_its_gap_on_the_middle_line(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5, wavy: true, track: surface_container_highest, style: {width: 48}}\n")
    c = control(view)
    assert c.ring.get("visible") and "A18.5,18.5" in c.circle
    assert c.ring.get("trim_start") == pytest.approx(0.5 + c._gap)


def test_a_wavy_ring_stops_flowing_when_it_is_disposed_and_stands_still_for_reduced_motion(tmp_path, monkeypatch):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 1, wavy: true}\n")
    c = control(view)
    run(view, 100)
    c.dispose()
    frozen = c.arc.get("data")
    run(view, 300)
    assert c.arc.get("data") == frozen and c._ticker is None
    from tesserae import motion

    monkeypatch.setattr(motion, "reduced", lambda window: True)
    (tmp_path / "again").mkdir()
    view, _ = opened(tmp_path / "again", "  - {widget: CircularProgress, name: p, value: 1, wavy: true}\n")
    still = control(view).arc.get("data")
    run(view, 300)
    assert control(view).arc.get("data") == still and control(view)._ticker is None


def test_the_standard_ring_has_no_wave_and_no_timer(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: CircularProgress, name: p, value: 0.5}\n")
    c = control(view)
    assert c._ticker is None and c._middle == 20.0
