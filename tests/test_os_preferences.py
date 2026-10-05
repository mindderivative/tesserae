"""#90: the window options of tre 0.5.4 and the user's wish for less motion and more contrast."""

import pytest

from tesserae import App, motion, tokens

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _app(**kwargs):
    app = App(width=400, height=300, theme_seed=SEED, **kwargs)
    app.window.advance(16)
    return app


def test_the_window_options_default_to_the_engines_good_ones():
    app = _app()
    assert app.dpi_scaling is True
    assert app.present_mode == "vsync"
    assert app.glyph_cache is False
    assert app.transparent is False


def test_options_are_passed_to_the_window():
    app = _app(dpi_scaling=False, present_mode="low_latency", glyph_cache=True)
    assert (app.dpi_scaling, app.present_mode, app.glyph_cache) == (False, "low_latency", True)


def test_a_transparent_app_asks_before_it_runs():
    assert _app(transparent=True).transparent is True


def test_reduced_motion_is_off_unless_asked_or_the_os_says():
    assert _app().reduced_motion is False
    assert _app(reduced_motion=True).reduced_motion is True


def test_motion_has_no_duration_when_reduced():
    app = _app(reduced_motion=True)
    assert motion.reduced(app.window) is True
    assert motion.duration(app.window, 200) == 0
    app.set_reduced_motion(False)
    assert motion.duration(app.window, 200) == 200


def test_set_reduced_motion_takes_a_bool_or_system():
    app = _app()
    with pytest.raises(ValueError):
        app.set_reduced_motion("sometimes")
    app.set_reduced_motion("system")
    assert app.reduced_motion_mode == "system"


def test_an_unknown_preference_is_refused():
    with pytest.raises(ValueError):
        _app(high_contrast="maybe")


def test_high_contrast_rethemes_the_app():
    app = _app()
    before = app.theme.role("primary")
    app.set_high_contrast(True)
    assert app.high_contrast is True and app.theme.contrast == 1.0
    after = app.theme.role("primary")
    assert after != before
    app.set_high_contrast(False)
    assert app.theme.contrast == 0.0


def test_the_contrast_level_changes_the_scheme():
    normal = tokens.color_scheme(SEED)
    higher = tokens.color_scheme(SEED, contrast=1.0)
    assert normal != higher


def test_an_indeterminate_progress_does_not_sweep_when_motion_is_reduced():
    from tesserae import controls

    app = _app(reduced_motion=True)
    bar = controls.LinearProgress(app.window, value=None)
    app.window.advance(50)
    assert bar.bar.get("translate_x") == pytest.approx((1.0 - bar.SWEEP) * bar.width / 2)


def test_an_indeterminate_progress_sweeps_otherwise():
    from tesserae import controls

    app = _app()
    bar = controls.LinearProgress(app.window, value=None)
    app.window.advance(200)
    assert bar.bar.get("translate_x") != pytest.approx((1.0 - bar.SWEEP) * bar.width / 2)


def test_frame_stats_and_handle_exist():
    app = _app()
    assert "frames" in app.frame_stats()
    assert app.stats_handle() is not None


def test_the_os_changing_its_preferences_is_followed():
    app = _app()
    app.window.simulate("reduced_motion", value=True)
    assert app.reduced_motion is True and motion.duration(app.window, 100) == 0
    before = app.theme.role("primary")
    app.window.simulate("high_contrast", value=True)
    assert app.high_contrast is True and app.theme.role("primary") != before
    app.window.simulate("reduced_motion", value=False)
    app.window.simulate("high_contrast", value=False)
    assert (app.reduced_motion, app.high_contrast) == (False, False)


def test_a_forced_preference_ignores_the_os():
    app = _app(reduced_motion=False, high_contrast=False)
    app.window.simulate("reduced_motion", value=True)
    app.window.simulate("high_contrast", value=True)
    assert (app.reduced_motion, app.high_contrast) == (False, False)


def test_the_stats_overlay_shows_and_goes():
    app = _app()
    assert app.stats_overlay is False
    app.stats_overlay = True
    assert app.stats_overlay is True
    app.frame_stats = lambda reset=False: {"recent": {"fps": 59.6, "total_ms": {"mean": 4.25, "p95": 7.5}}}
    for _ in range(15):  # the engine says each frame; the readout is rewritten every 15th
        app._on_frame(None)
    assert app._stats_label.get("text") == "60 fps  4.2 ms  p95 7.5"
    app.stats_overlay = False
    assert app.stats_overlay is False


def test_the_environment_turns_the_overlay_on(monkeypatch):
    monkeypatch.setenv("TESSERAE_STATS", "1")
    assert _app().stats_overlay is True


def test_a_drop_anywhere_on_the_window_is_heard():
    app = _app()
    heard = []
    app.on_file_drop(lambda event: heard.append(list(event.paths)))
    app.window.simulate("file_drop", x=10, y=10, paths=["/a.txt"])
    assert heard == [["/a.txt"]]
    app.on_file_drop(None)
    app.window.simulate("file_drop", x=10, y=10, paths=["/b.txt"])
    assert heard == [["/a.txt"]]
