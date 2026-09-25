"""M29 Phase 4: Tesserae reads theme, stylesheet and font files itself
and hands `tre` only dicts (`*_spec=`, tre M86) and bytes
(`tre.register_font`).

A theme's or stylesheet's effect is observed through `corner_radius`,
which both can set via `styles:` and `Node.get` can read back.
"""

import warnings
from pathlib import Path

import pytest
import tre

import tesserae
import tesserae.fonts as fonts
import tesserae.spec.load as load_module
from tesserae.fonts import FontFallbackWarning, available_families
from tesserae.spec import load_stylesheet, load_theme, load_view

SEED = (0x67, 0x50, 0xA4, 0xFF)
RECT_VIEW = 'id: box\nkind: Rect\nstyle: {width: 10, height: 10, background: "#112233"}\n'
ROBOTO = Path(tre.__file__).parents[2] / "crates" / "engine-render" / "assets" / "fonts" / "Roboto-Regular.ttf"


@pytest.fixture(autouse=True)
def _fresh_font_registry(monkeypatch):
    monkeypatch.setattr(fonts, "_registered", set())


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _view(tmp_path: Path, text: str = RECT_VIEW) -> Path:
    return _write(tmp_path / "Box_View.yaml", text)


# -- load_theme / load_stylesheet -------------------------------------


def test_load_theme_reads_a_mapping(tmp_path: Path):
    theme = _write(tmp_path / "t.yaml", "colors: {primary: '#00FF00'}\ndark: true\n")
    assert load_theme(theme) == {"colors": {"primary": "#00FF00"}, "dark": True}


def test_an_empty_theme_file_is_an_empty_theme(tmp_path: Path):
    assert load_theme(_write(tmp_path / "t.yaml", "")) == {}


@pytest.mark.parametrize(
    "text, match",
    [("- not\n- a mapping\n", "must be a mapping"), ("colors: [unclosed\n", "invalid YAML")],
)
def test_bad_theme_files_are_named_in_the_error(tmp_path: Path, text, match):
    theme = _write(tmp_path / "bad.yaml", text)
    with pytest.raises(ValueError, match=rf"bad\.yaml: .*{match}"):
        load_theme(theme)


def test_load_stylesheet_reads_a_mapping(tmp_path: Path):
    sheet = _write(tmp_path / "s.yaml", "styles:\n  - kind: Rect\n    style: {corner_radius: 8}\n")
    assert load_stylesheet(sheet) == {"styles": [{"kind": "Rect", "style": {"corner_radius": 8}}]}


# -- load_view ---------------------------------------------------------


def test_load_view_reads_theme_and_stylesheet_files_and_gives_tre_only_dicts(tmp_path: Path, monkeypatch):
    theme = _write(tmp_path / "Theme.yaml", "colors: {primary: '#00FF00'}\n")
    sheet = _write(tmp_path / "Sheet.yaml", "styles:\n  - kind: Rect\n    style: {corner_radius: 8}\n")
    seen = {}

    def recording_view(*args, **kwargs):
        seen.update(kwargs, args=args)
        return tre.View(*args, **kwargs)

    monkeypatch.setattr(load_module, "View", recording_view)
    view = load_view(_view(tmp_path), theme_seed=SEED, custom_theme=theme, stylesheet=sheet)

    assert seen["args"] == ()
    assert "custom_theme" not in seen and "stylesheet" not in seen
    assert seen["custom_theme_spec"] == {"colors": {"primary": "#00FF00"}}
    assert seen["stylesheet_spec"] == {"styles": [{"kind": "Rect", "style": {"corner_radius": 8}}]}
    assert view.node("box").get("corner_radius") == 8.0


def test_a_theme_file_really_applies(tmp_path: Path):
    theme = _write(tmp_path / "Theme.yaml", "styles:\n  - kind: Rect\n    style: {corner_radius: 12}\n")
    view = load_view(_view(tmp_path), theme_seed=SEED, default_theme=theme)
    assert view.node("box").get("corner_radius") == 12.0


def test_a_spec_dict_still_passes_straight_through(tmp_path: Path):
    view = load_view(
        _view(tmp_path),
        theme_seed=SEED,
        stylesheet_spec={"styles": [{"kind": "Rect", "style": {"corner_radius": 5}}]},
    )
    assert view.node("box").get("corner_radius") == 5.0


def test_giving_both_a_theme_file_and_its_spec_is_an_error(tmp_path: Path):
    theme = _write(tmp_path / "Theme.yaml", "{}\n")
    with pytest.raises(ValueError, match="custom_theme= or custom_theme_spec=, not both"):
        load_view(_view(tmp_path), custom_theme=theme, custom_theme_spec={})


def test_a_bad_key_in_a_theme_file_names_the_theme_file(tmp_path: Path):
    theme = _write(tmp_path / "Theme.yaml", "colours: {primary: '#00FF00'}\n")
    with pytest.raises(ValueError, match=r"Theme\.yaml: custom_theme_spec=: unknown field `colours`"):
        load_view(_view(tmp_path), theme_seed=SEED, custom_theme=theme)


def test_set_theme_takes_a_loaded_theme(tmp_path: Path):
    view = load_view(_view(tmp_path), theme_seed=SEED)
    theme = _write(tmp_path / "Round.yaml", "styles:\n  - kind: Rect\n    style: {corner_radius: 20}\n")
    view.set_theme(theme_seed=SEED, custom_theme_spec=load_theme(theme))
    assert view.node("box").get("corner_radius") == 20.0


# -- fonts -------------------------------------------------------------


@pytest.mark.skipif(not ROBOTO.is_file(), reason="needs tre's source tree for a real font file")
def test_register_font_hands_tre_the_bytes_and_returns_families():
    assert tesserae.register_font(ROBOTO) == ["Roboto"]


def test_register_font_records_a_new_family(tmp_path: Path, monkeypatch):
    font = tmp_path / "Inter.ttf"
    font.write_bytes(b"pretend font bytes")
    received = []
    monkeypatch.setattr(tre, "register_font", lambda data: received.append(data) or ["Inter"])

    assert tesserae.register_font(font) == ["Inter"]
    assert received == [b"pretend font bytes"]
    assert "Inter" in available_families()


def test_register_font_rejects_a_file_with_no_font_faces(tmp_path: Path):
    junk = tmp_path / "junk.ttf"
    junk.write_bytes(b"definitely not a font")
    with pytest.raises(ValueError, match=r"junk\.ttf: .*no font faces"):
        tesserae.register_font(junk)


def test_register_font_missing_file_raises_oserror(tmp_path: Path):
    with pytest.raises(OSError):
        tesserae.register_font(tmp_path / "nope.ttf")


def test_a_theme_naming_an_unavailable_font_warns(tmp_path: Path):
    theme = _write(tmp_path / "Inter.yaml", "typography: {body_large: {font_family: Inter}}\n")
    with pytest.warns(FontFallbackWarning, match=r"Inter\.yaml: font_family 'Inter' is not bundled or registered"):
        load_theme(theme)


def test_a_bundled_or_registered_font_does_not_warn(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(tre, "register_font", lambda data: ["Inter"])
    font = tmp_path / "Inter.ttf"
    font.write_bytes(b"x")
    tesserae.register_font(font)
    theme = _write(
        tmp_path / "Ok.yaml",
        "typography:\n  body_large: {font_family: Inter}\n  label_large: {font_family: Roboto}\n",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", FontFallbackWarning)
        load_theme(theme)


def test_a_view_naming_an_unavailable_font_warns(tmp_path: Path):
    view_path = _view(
        tmp_path,
        "id: root\nkind: Container\nchildren:\n"
        "  - {id: t, kind: Text, text: {content: Hi, font_family: Comic Sans, font_size: 16},"
        ' style: {width: 50, height: 20, background: "#000000"}}\n',
    )
    with pytest.warns(FontFallbackWarning, match=r"Box_View\.yaml: font_family 'Comic Sans'"):
        load_view(view_path)
