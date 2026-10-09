"""#208: nested routes, guards and lazy screens in a window view."""

import pytest

from tesserae import App
from tesserae.spec.nodes import LoadError

SHELL = """name: shell
widget: Window
title: App
state: {signed: false}
style: {width: 600, height: 300}
children:
  - {widget: Rect, name: sign_in, style: {width: 40, height: 20, background: primary}, handlers: {on_click: 'signed = True'}}
  - {widget: Home, name: home, route: ""}
  - {widget: Settings, name: settings, route: settings}
  - widget: Admin
    name: admin
    route: {path: admin, guard: signed, redirect: ""}
  - widget: Reports
    name: reports
    route: {path: reports, lazy: true}
"""
LEAF = "name: {n}\nwidget: Container\nstate: {{count: 0}}\nstyle: {{width: 100, height: 50}}\nchildren:\n  - {{widget: Rect, name: bump, style: {{width: 20, height: 20, background: primary}}, handlers: {{on_click: 'count += 1'}}}}\n  - {{widget: Text, name: t, text: \"{n}\" , typography_role: body_medium, style: {{foreground: on_surface}}}}\n"
SETTINGS = """name: settings
widget: Container
style: {width: 300, height: 100}
children:
  - {widget: Text, name: t, text: settings, typography_role: body_medium, style: {foreground: on_surface}}
  - {widget: Profile, name: profile, route: profile}
  - {widget: Account, name: account, route: /account}
"""
ADMIN = """name: admin
widget: Container
style: {width: 300, height: 100}
children:
  - {widget: Text, name: t, text: admin, typography_role: body_medium, style: {foreground: on_surface}}
  - {widget: Users, name: users, route: users}
"""


@pytest.fixture
def shell(tmp_path):
    (tmp_path / "Views").mkdir()
    files = {"Shell": SHELL, "Settings": SETTINGS, "Admin": ADMIN}
    for n in ("Home", "Profile", "Account", "Users", "Reports"):
        files[n] = LEAF.format(n=n.lower())
    for n, text in files.items():
        (tmp_path / "Views" / f"{n}_View.yaml").write_text(text)
    app = App(root=tmp_path)
    view = app.open_view("Shell")
    app.window.advance(16)
    app.navigate_to("")
    app.window.advance(16)
    return app, view


def shown(view, *names):
    out = {}
    for name in names:
        path = {"home": "root.home", "settings": "root.settings", "profile": "root.settings.profile", "account": "root.settings.account",
                "admin": "root.admin", "users": "root.admin.users", "reports": "root.reports"}[name]
        out[name] = bool(view.node(path).get("visible")) if path in view._built.nodes else None
    return out


def test_a_nested_route_is_under_its_parents_path(shell):
    app, view = shell
    app.navigate_to("settings/profile")
    assert app.current == "Profile" and app.location == "settings/profile"
    app.navigate_to("settings")
    assert app.current == "Settings"


def test_an_absolute_nested_route_starts_from_the_root(shell):
    app, view = shell
    app.navigate_to("account")
    assert app.current == "Account"
    with pytest.raises(KeyError):
        app.navigate_to("settings/account")


def test_a_parent_shows_while_its_child_is_current_and_its_siblings_do_not(shell):
    app, view = shell
    app.navigate_to("settings/profile")
    app.window.advance(16)
    assert shown(view, "home", "settings", "profile", "account") == {"home": False, "settings": True, "profile": True, "account": False}
    app.navigate_to("account")
    app.window.advance(16)
    assert shown(view, "settings", "profile", "account") == {"settings": True, "profile": False, "account": True}
    app.navigate_to("")
    app.window.advance(16)
    assert shown(view, "home", "settings", "profile", "account") == {"home": True, "settings": False, "profile": False, "account": False}


def test_back_and_forward_walk_nested_screens(shell):
    app, view = shell
    app.navigate_to("settings/profile")
    app.navigate_to("account")
    app.back()
    assert app.current == "Profile"
    app.back()
    assert app.current == "Home"
    app.forward()
    assert app.current == "Profile"


def test_a_guard_that_fails_keeps_the_app_where_it_is_or_goes_to_the_redirect(shell):
    app, view = shell
    app.navigate_to("settings")
    app.navigate_to("admin")  # not signed in: sent to ""
    assert app.current == "Home" and app.can_go_back.get() is True


def test_a_guard_follows_the_state_it_reads(shell):
    app, view = shell
    app.navigate_to("admin")
    assert app.current == "Home"
    app.window.simulate("click", node=view.node("root.sign_in"))
    app.window.advance(16)
    app.navigate_to("admin")
    assert app.current == "Admin"


def test_a_parents_guard_covers_its_children(shell):
    app, view = shell
    app.navigate_to("admin/users")
    assert app.current == "Home"
    app.window.simulate("click", node=view.node("root.sign_in"))
    app.window.advance(16)
    app.navigate_to("admin/users")
    assert app.current == "Users"


def test_back_into_a_screen_a_guard_now_refuses_does_not_go(shell):
    app, view = shell
    app.window.simulate("click", node=view.node("root.sign_in"))
    app.window.advance(16)
    app.navigate_to("admin")
    app.navigate_to("settings")
    assert app.current == "Settings"
    app._frame.view.handle  # the shell is the frame
    app.guard("Admin", lambda params: False)
    assert app.back() is False and app.current == "Settings"


def test_a_python_guard_can_send_the_app_elsewhere(shell):
    app, view = shell
    app.guard("Settings", lambda params: "")
    app.navigate_to("reports")
    app.navigate_to("settings")
    assert app.current == "Home"


def test_guards_that_send_each_other_round_are_named(shell):
    app, view = shell
    app.guard("Settings", lambda params: "reports")
    app.guard("Reports", lambda params: "settings")
    with pytest.raises(ValueError, match="in a circle"):
        app.navigate_to("settings")


def test_show_is_a_jump_and_skips_guards(shell):
    app, view = shell
    app.show("Admin")
    assert app.current == "Admin"


def test_a_lazy_screen_is_not_built_until_it_is_reached_then_kept(shell):
    app, view = shell
    assert "root.reports" not in view._built.nodes and "reports" not in [r.view.lower() for r in view.handle.composition.routes if r.instance is not None]
    app.navigate_to("reports")
    app.window.advance(16)
    assert shown(view, "reports") == {"reports": True}
    app.window.simulate("click", node=view.node("root.reports.bump"))
    app.window.advance(16)
    app.navigate_to("")
    app.window.advance(16)
    assert shown(view, "reports", "home") == {"reports": False, "home": True}
    app.navigate_to("reports")
    assert view.handle.composition.find("root.reports") is not None


def test_a_lazy_screen_has_its_route_before_it_is_built(shell):
    app, view = shell
    assert app.location is not None
    app.navigate_to("reports")  # the route exists
    assert app.current == "Reports"


def test_a_lazy_route_with_if_is_refused(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Shell_View.yaml").write_text(
        "name: shell\nwidget: Window\ntitle: T\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Home, name: home, route: {path: '', lazy: true}, if: 'True'}\n")
    (tmp_path / "Views" / "Home_View.yaml").write_text(LEAF.format(n="home"))
    with pytest.raises(LoadError, match="a lazy route takes no 'if:'"):
        App(root=tmp_path).open_view("Shell")


def test_a_route_mapping_is_checked(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Shell_View.yaml").write_text(
        "name: shell\nwidget: Window\ntitle: T\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Home, name: home, route: {path: '', redirect: x}}\n")
    (tmp_path / "Views" / "Home_View.yaml").write_text(LEAF.format(n="home"))
    with pytest.raises(LoadError, match="redirect"):
        App(root=tmp_path).open_view("Shell")
