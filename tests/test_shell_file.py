"""M52 Phase 2: a declarative app shell -- a `*_Shell.yaml` loaded with
`app.load_shell(path)` builds M45's `AppShell` (M52 Q1): the same shell a
Python-built one is, every key optional, and a mistake named by file and
key.
"""

import pytest
import yaml

from tesserae import App, Theme, View
from tesserae.shell import AppShell
from tesserae.shell_file import ShellSpecError, load_shell_spec, parse_shell_spec
from tesserae.widgets import navigation_rail, status_bar, top_app_bar

SEED = (0x67, 0x50, 0xA4, 0xFF)

STUDIO = """
top_bar: {title: Studio, trailing_icons: [settings]}
navigation:
  items:
    - {screen: Home, icon: home}
    - {screen: Notes, icon: search}
status_bar: {text: Ready}
zones: {left: 220, right: 260, bottom: 160}
"""


def _file(tmp_path, text, name="Studio_Shell.yaml"):
    path = tmp_path / name
    path.write_text(text)
    return path


def _box(node):
    return tuple(round(node.get(k)) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


def _boxes(shell):
    nodes = [shell.node, shell.top_bar.node, shell.navigation.node, shell.status_bar.node, shell.content,
             *(shell._zone_nodes[s] for s in ("left", "right", "bottom")),
             *(shell._handles[s].node for s in ("left", "right", "bottom"))]
    return [_box(n) for n in nodes]


def test_a_shell_file_builds_the_same_shell_as_python(tmp_path):
    app = App(width=1000, height=600)
    from_file = app.load_shell(_file(tmp_path, STUDIO))
    app.window.advance(16)
    other = App(width=1000, height=600)
    w = other.window
    by_hand = AppShell(w, top_bar=top_app_bar(w, "Studio", trailing_icons=["settings"], width=1000),
                       navigation=navigation_rail(w, ["Home", "Notes"], ["home", "search"], selected=0),
                       status_bar=status_bar(w, "Ready", width=1000), zones={"left": 220, "right": 260, "bottom": 160})
    w.advance(16)
    assert _boxes(from_file) == _boxes(by_hand)
    assert from_file.top_bar.part("title").get("text") == "Studio" and from_file.top_bar.part("trailing0")
    assert from_file.navigation.part("item1.label").get("text") == "Notes"
    assert from_file.status_bar.part("text").get("text") == "Ready"
    assert {s: from_file.size(s) for s in ("left", "right", "bottom")} == {"left": 220, "right": 260, "bottom": 160}


def test_load_shell_uses_it_and_a_showing_screen_moves_in(tmp_path):
    app = App(width=800, height=500)
    home = View({"id": "root", "kind": "Rect", "style": {"width": 100, "height": 50, "background": "#112233"}},
                window=app.window)
    app.register("Home", home, None)
    app.show("Home")
    shell = app.load_shell(_file(tmp_path, STUDIO))
    assert app._shell is shell and home.root.parent() == shell.content and app._shell_file.name == "Studio_Shell.yaml"


def test_center_true_makes_screens_center_tabs(tmp_path):
    app = App(width=800, height=500)
    shell = app.load_shell(_file(tmp_path, "zones: {left: 200}\ncenter: true\n"))
    assert shell.center and shell.content == shell.dock._zones["center"].node


def test_every_key_is_optional(tmp_path):
    app = App(width=800, height=500)
    shell = app.load_shell(_file(tmp_path, ""))
    app.window.advance(16)
    assert (shell.top_bar, shell.navigation, shell.status_bar, shell._zone_nodes) == (None, None, None, {})
    assert _box(shell.content)[2:] == (800, 500)


def test_the_bars_stretch_across_the_window_as_it_resizes(tmp_path):
    app = App(width=1000, height=600)
    shell = app.load_shell(_file(tmp_path, STUDIO))
    app.window.resize(1200, 700)
    app.window.advance(16)
    assert shell.top_bar.node.get("layout_width") == 1200.0 and shell.status_bar.node.get("layout_width") == 1200.0


def test_a_file_built_shell_follows_the_apps_theme(tmp_path):
    app = App(width=1000, height=600, theme_seed=SEED, dark=False)
    shell = app.load_shell(_file(tmp_path, STUDIO))
    app.set_dark(True)
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    assert shell.node.get("fill") == dark.role("surface") and shell.top_bar.node.get("fill") == dark.role("surface")
    assert shell.navigation.theme.dark and shell.status_bar.theme.dark


def test_the_file_must_be_named_like_a_shell(tmp_path):
    with pytest.raises(ShellSpecError, match=r"\*_Shell.yaml naming convention"):
        load_shell_spec(_file(tmp_path, STUDIO, name="Studio.yaml"))


def test_broken_yaml_names_the_file(tmp_path):
    with pytest.raises(ShellSpecError, match="Studio_Shell.yaml"):
        load_shell_spec(_file(tmp_path, "top_bar: {title: [\n"))


@pytest.mark.parametrize("text, message", [
    ("- a list", "a shell file is a mapping"),
    ("sidebar: {}", "sidebar: unknown key"),
    ("top_bar: Studio", "top_bar: a mapping of"),
    ("top_bar: {}", "top_bar.title: a top bar needs a title"),
    ("top_bar: {title: S, colour: red}", "top_bar.colour: unknown key"),
    ("top_bar: {title: S, leading_icon: 3}", "top_bar.leading_icon: text"),
    ("top_bar: {title: S, trailing_icons: settings}", "top_bar.trailing_icons: a list of names"),
    ("navigation: {items: []}", "navigation.items: a list of"),
    ("navigation: {items: [{screen: Home}]}", r"navigation.items\[0\]: needs a screen name and an icon"),
    ("navigation: {items: [{screen: Home, icon: home, badge: 2}]}", r"navigation.items\[0\].badge: unknown key"),
    ("navigation: {items: [{screen: Home, icon: home}], on_navigate: 5}", "navigation.on_navigate: text"),
    ("status_bar: {}", "status_bar.text: a status bar needs its text"),
    ("zones: [left]", "zones: a mapping of side to size"),
    ("zones: {middle: 100}", "zones.middle: not a side"),
    ("zones: {left: 0}", "zones.left: a size in pixels, more than 0"),
    ("zones: {left: true}", "zones.left: a size in pixels"),
    ("center: yes please", "center: true or false"),
    ("panels: [Files]", "panels: a mapping of side"),
    ("zones: {left: 200}\npanels: {right: [Files]}", "panels.right: no such zone here"),
    ("panels: {center: [Files]}", "panels.center: no such zone here"),
    ("zones: {left: 200}\npanels: {left: Files}", "panels.left: a list of names"),
    ("zones: {left: 200, right: 200}\npanels: {left: [Files], right: [Files]}", "panels.right: 'Files' is placed twice"),
])
def test_a_mistake_is_named_by_file_and_key(text, message):
    with pytest.raises(ShellSpecError, match=f"Studio_Shell.yaml: {message}"):
        parse_shell_spec(yaml.safe_load(text), "Studio_Shell.yaml")


def test_center_panels_are_allowed_when_center_is_on():
    spec = parse_shell_spec({"center": True, "panels": {"center": ["Files"]}})
    assert spec["panels"] == {"center": ["Files"]} and spec["zones"] == {}


STYLED = """
style: {padding: 6}
top_bar: {title: Studio, leading_icon: menu, trailing_icons: [settings], style: {height: 40, background: primary_container}}
navigation:
  items:
    - {screen: Home, icon: home}
  style: {width: 96}
status_bar: {text: Ready, style: {height: 32, corner_radius: 8}}
zones: {left: {size: 180, style: {background: tertiary_container}}, right: 200}
content: {style: {background: surface_container_low, corner_radius: 12}}
"""


def test_every_part_of_a_shell_file_takes_a_style(tmp_path):
    """0.3.3 (#81): the file itself, the bars, the content area and each zone."""
    app = App(width=900, height=500, theme_seed=SEED, dark=False)
    shell = app.load_shell(_file(tmp_path, STYLED))
    app.window.advance(16)
    theme = Theme.resolve(theme_seed=SEED, dark=False)
    assert shell.top_bar.node.get("layout_height") == 40.0  # a slimmer top bar ...
    assert shell.top_bar.part("leading").get("layout_height") == 40.0  # ... with icon buttons that fit it
    assert shell.top_bar.node.get("fill") == theme.role("primary_container")
    assert shell.navigation.node.get("layout_width") == 96.0
    assert shell.status_bar.node.get("layout_height") == 32.0 and shell.status_bar.node.get("corner_radius") == 8.0
    assert shell.node.get("padding_left") == 6.0  # the frame
    assert shell.content.get("corner_radius") == 12.0 and shell.content.get("fill") == theme.role("surface_container_low")
    assert shell.size("left") == 180 and shell.size("right") == 200  # `left: {size, style}` and `right: 200`
    assert shell._zone_nodes["left"].get("fill") == theme.role("tertiary_container")
    app.set_dark(True)  # a role in a style follows the theme
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    assert shell.top_bar.node.get("fill") == dark.role("primary_container")
    assert shell._zone_nodes["left"].get("fill") == dark.role("tertiary_container")
    assert shell.content.get("fill") == dark.role("surface_container_low")


def test_a_shell_file_with_no_styles_is_as_it_was(tmp_path):
    spec = parse_shell_spec(yaml.safe_load(STUDIO), "Studio_Shell.yaml")
    assert spec["styles"] == {} and spec["top_bar"]["style"] is None


@pytest.mark.parametrize("text, message", [
    ("top_bar: {title: S, style: {hieght: 40}}", r"top_bar.style.hieght: unknown style field -- did you mean 'height'\?"),
    ("top_bar: {title: S, style: {foreground: red}}", "top_bar.style.foreground: a bar or area has no text"),
    ("top_bar: {title: S, style: 40}", "top_bar.style: a mapping of style fields"),
    ("navigation: {items: [{screen: Home, icon: home}], style: {widht: 90}}", r"navigation.style.widht: unknown style field -- did you mean 'width'\?"),
    ("status_bar: {text: S, style: {colour: red}}", "status_bar.style.colour: unknown style field"),
    ("style: 5", "style: a mapping of style fields"),
    ("style: {paddin: 4}", r"style.paddin: unknown style field -- did you mean 'padding'\?"),
    ("content: {color: red}", "content.color: unknown key"),
    ("content: {style: {backgrund: red}}", "content.style.backgrund: unknown style field"),
    ("zones: {left: {size: 100, sizee: 3}}", "zones.left.sizee: unknown key"),
    ("zones: {left: {style: {gap: 2}}}", "zones.left: a size in pixels"),
    ("zones: {left: {size: 100, style: {width: 5}}}", "zones.left.style: a zone's size is its `size:`"),
])
def test_a_mistake_in_a_style_is_named_by_file_and_key(text, message):
    with pytest.raises(ShellSpecError, match=f"Studio_Shell.yaml: {message}"):
        parse_shell_spec(yaml.safe_load(text), "Studio_Shell.yaml")


def test_a_bad_style_value_is_an_error_naming_the_part(tmp_path):
    app = App(width=900, height=500, theme_seed=SEED)
    with pytest.raises(ValueError, match="the shell's content"):
        app.load_shell(_file(tmp_path, "content: {style: {background: notacolor}}"))
