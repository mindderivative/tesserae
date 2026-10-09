"""#224: `open_url(url)` in a handler and `tesserae.urls`: links go to the OS opener, and only the kinds that are links."""

import pytest

from tesserae import App, Signal, ViewModel, urls


@pytest.mark.parametrize("url", ["https://example.com", "http://example.com/a?b=c#d", "HTTPS://Example.com", "mailto:a@b.example", "tel:+15551234567",
                                 "https://user@example.com:8080/x"])
def test_these_links_are_allowed(url):
    assert urls.check_url(url) == url


@pytest.mark.parametrize("url, message", [
    ("", "takes a link"), ("   ", "takes a link"), (None, "takes a link"), (3, "takes a link"),
    ("example.com", "no scheme"), ("file:///etc/passwd", "not file:"), ("javascript:alert(1)", "not javascript:"),
    ("data:text/html,<b>x</b>", "not data:"), ("myapp://do/it", "not myapp:"), ("ftp://example.com", "not ftp:"),
    ("https://exa mple.com", "spaces or control"), ("https://example.com/\n", "spaces or control"), ("https://example.com/\x00", "spaces or control"),
    ("https:///path", "has no host"), ("http://", "has no host"),
])
def test_these_are_refused_and_say_why(url, message):
    with pytest.raises(ValueError, match=message):
        urls.check_url(url)


def test_open_url_hands_the_link_to_the_opener_and_returns_what_it_said():
    seen = []
    assert urls.open_url("https://example.com", lambda u: seen.append(u) or True) is True
    assert seen == ["https://example.com"]
    assert urls.open_url("https://example.com", lambda u: False) is False
    assert urls.open_url("https://example.com", lambda u: None) is False  # whatever the opener returns is a bool


def test_a_refused_link_never_reaches_the_opener():
    seen = []
    with pytest.raises(ValueError):
        urls.open_url("file:///etc/passwd", seen.append)
    assert seen == []


def test_the_default_opener_is_the_standard_librarys(monkeypatch):
    import webbrowser

    seen = []
    monkeypatch.setattr(webbrowser, "open", lambda url: seen.append(url) or True)
    assert urls.open_url("https://example.com/x") is True and seen == ["https://example.com/x"]


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.site = Signal("https://example.com/docs")
        self.ok = Signal(None)


VIEW = """name: main
widget: Container
style: {width: 200, height: 100}
children:
  - {widget: Container, name: go, handlers: {on_click: "ok = open_url(site)"}}
  - {widget: Container, name: mail, handlers: {on_click: "open_url('mailto:hi@example.com')"}}
  - {widget: Container, name: bad, handlers: {on_click: "open_url('file:///etc/passwd')"}}
"""


def opened(tmp_path):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    return app, view, app.bindings.viewmodel_for("main")


def fire(view, name):
    next(i for i in view.handle.composition.walk() if i.id == f"root.{name}").fire("on_click")


def test_a_handler_opens_a_link(tmp_path, monkeypatch):
    opened_links = []
    monkeypatch.setattr(urls, "open_url", lambda url: opened_links.append(url) or True)
    _, view, vm = opened(tmp_path)
    fire(view, "go")
    fire(view, "mail")
    assert opened_links == ["https://example.com/docs", "mailto:hi@example.com"] and vm.ok.get() is True


def test_a_handler_that_asks_for_a_file_link_is_an_error_naming_the_call(tmp_path, monkeypatch):
    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda url: pytest.fail("the OS should never be asked"))
    _, view, _ = opened(tmp_path)
    with pytest.raises(Exception, match=r"open_url\(\) failed: ValueError: open_url\(\) opens http, https, mailto, tel links, not file:"):
        fire(view, "bad")


def test_the_view_is_clean_when_checked(tmp_path):
    app, _, _ = opened(tmp_path)
    assert app.check() == []
