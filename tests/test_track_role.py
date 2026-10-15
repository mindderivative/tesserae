"""#267: a colour role that is not one (`track: surface_variant`) is an error that names the property and the role, at the place the view says it --
it was a bare `KeyError` from deep in the control's painting."""

import pytest

from tesserae import App, ViewModel, controls

HEAD = "name: main\nwidget: Container\nstyle: {width: 300, height: 200, flex_direction: vertical}\nchildren:\n"


class VM(ViewModel):
    views = "main"


def open_with(tmp_path, widget, track):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(HEAD + f"  - {{widget: {widget}, name: bar, value: 0.5, track: {track}}}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    view.window.advance(16)
    return view


@pytest.mark.parametrize("widget", ["LinearProgress", "CircularProgress"])
def test_a_track_that_is_no_role_is_named_when_the_view_is_built(tmp_path, widget):
    with pytest.raises(Exception) as caught:
        open_with(tmp_path, widget, "surface_variantt")
    text = str(caught.value)
    assert "track" in text and "surface_variantt" in text and "bar" in text, text
    assert not isinstance(caught.value, KeyError)


def test_the_error_suggests_the_nearest_role(tmp_path):
    with pytest.raises(Exception) as caught:
        open_with(tmp_path, "LinearProgress", "surface_container_hihgest")
    assert "surface_container_highest" in str(caught.value)


@pytest.mark.parametrize("widget", ["LinearProgress", "CircularProgress"])
def test_a_real_role_still_works(tmp_path, widget):
    view = open_with(tmp_path, widget, "surface_container_low")
    assert view.node("root.bar") is not None


def test_a_control_made_in_python_says_so_too():
    app = App(width=300, height=200)
    with pytest.raises(ValueError, match="track.*nope|nope.*track"):
        controls.LinearProgress(app.window, value=0.5, track="nope")


@pytest.mark.parametrize("widget", ["LinearProgress", "CircularProgress"])
def test_a_role_of_the_full_scheme_that_the_few_published_baseline_values_lack_works_without_a_theme(tmp_path, widget):
    """The first form of this issue: `track: surface_variant` is a real role, and it was a `KeyError` because an unthemed control looked it up in
    `tokens.BASELINE`, which holds only some of the roles."""
    from tesserae import tokens

    assert "surface_variant" not in tokens.BASELINE
    assert open_with(tmp_path, widget, "surface_variant").node("root.bar") is not None


def test_a_control_without_a_theme_paints_every_role_of_the_scheme():
    from tesserae import tokens

    app = App(width=300, height=200)
    bar = controls.LinearProgress(app.window, value=0.5)
    for role in tokens.baseline_scheme():
        assert len(bar.color(role)) == 4
