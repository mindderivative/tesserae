"""#174: `widget: Link` -- a primary-coloured link that opens its href, shows underlined under the pointer or the keyboard, and can be visited or disabled."""

import pytest

from tesserae import App, Signal, ViewModel, tokens, urls


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.seen = Signal(False)
        self.clicks = Signal(0)


def opened(tmp_path, body, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 300, height: 200}\nchildren:\n" + body)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def box(view, name="l"):
    return view._built.outer[f"root.{name}"]


def text(view, name="l"):
    return view._built.nodes[f"root.{name}"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def hover(view, name="l"):
    node = box(view, name)
    view.window.simulate("pointer_move", x=node.get("layout_x") + 4, y=node.get("layout_y") + 4)


def away(view):
    view.window.simulate("pointer_move", x=290, y=190)


LINK = "  - {widget: Link, name: l, text: Docs, href: 'https://example.com/docs'}\n"


@pytest.fixture
def opened_urls(monkeypatch):
    seen = []
    monkeypatch.setattr(urls, "open_url", lambda url: seen.append(url) or True)
    return seen


def test_a_link_is_primary_text_with_a_default_type_and_the_role_of_a_link(tmp_path):
    view, _ = opened(tmp_path, LINK)
    assert text(view).get("fill") == role(view, "primary") and text(view).get("font_size") == 14.0
    assert box(view).get("role") == "link" and box(view).get("focusable") is True and box(view).get("label") == "Docs"


def test_activating_it_opens_its_href(tmp_path, opened_urls):
    view, _ = opened(tmp_path, LINK)
    view.window.simulate("click", node=box(view))
    assert opened_urls == ["https://example.com/docs"]


def test_enter_activates_it_from_the_keyboard(tmp_path, opened_urls):
    view, _ = opened(tmp_path, LINK)
    box(view).focus()
    view.window.simulate("key_down", key="enter")
    assert opened_urls == ["https://example.com/docs"]


def test_opening_it_marks_a_bound_visited_and_the_rule_colours_it(tmp_path, opened_urls):
    view, vm = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, href: 'https://example.com', visited: \"{{ seen }}\"}\n")
    assert text(view).get("fill") == role(view, "primary")
    view.window.simulate("click", node=box(view))
    view.window.advance(16)
    assert vm.seen.get() is True and text(view).get("fill") == role(view, "secondary")


def test_a_link_with_a_handler_and_an_href_does_both(tmp_path, opened_urls):
    view, vm = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, href: 'https://example.com', handlers: {on_click: \"clicks += 1\"}}\n")
    view.window.simulate("click", node=box(view))
    assert vm.clicks.get() == 1 and opened_urls == ["https://example.com"]


def test_a_link_with_no_href_just_runs_its_handler(tmp_path, opened_urls):
    view, vm = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, handlers: {on_click: \"clicks += 1\"}}\n")
    view.window.simulate("click", node=box(view))
    assert vm.clicks.get() == 1 and opened_urls == []


def test_a_link_to_somewhere_that_is_not_allowed_is_refused_not_opened(tmp_path, monkeypatch):
    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda url: pytest.fail("the OS should never be asked"))
    view, vm = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, href: 'file:///etc/passwd', visited: \"{{ seen }}\"}\n")
    view.window.simulate("click", node=box(view))
    assert vm.seen.get() is False


def test_a_disabled_link_is_dimmed_out_of_the_tab_order_and_does_nothing(tmp_path, opened_urls):
    view, _ = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, href: 'https://example.com', disabled: true}\n")
    assert text(view).get("opacity") == 0.38 and not box(view).get("focusable") and box(view).get("disabled") is True
    view.window.simulate("click", node=box(view))
    assert opened_urls == []


def underlined(view, name="l"):
    return bool(text(view, name).get("spans"))


def test_it_is_underlined_under_the_pointer_and_not_otherwise(tmp_path):
    view, _ = opened(tmp_path, LINK)
    assert not underlined(view)
    hover(view)
    assert underlined(view)
    assert text(view).get("spans")[0][:2] == (0, 4)  # all of "Docs"
    away(view)
    assert not underlined(view)


def test_keyboard_focus_underlines_it_and_a_mouse_click_does_not(tmp_path):
    view, _ = opened(tmp_path, LINK + "  - {widget: Link, name: m, text: More, href: 'https://example.com'}\n")
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert underlined(view)
    view.window.simulate("key_down", key="tab")
    view.window.advance(16)
    assert not underlined(view) and underlined(view, "m")


def test_always_and_never(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, underline: always}\n  - {widget: Link, name: m, text: More, underline: never}\n")
    assert underlined(view)
    hover(view, "m")
    assert not underlined(view, "m")


def test_the_underline_survives_a_re_sync_while_the_pointer_is_over_it(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Link, name: l, text: \"{{ clicks }} clicks\", href: 'https://example.com'}\n")
    hover(view)
    assert underlined(view)
    vm.clicks.set(5)
    view.window.advance(16)
    assert text(view).get("text") == "5 clicks" and underlined(view) and text(view).get("spans")[0][1] == len("5 clicks")


def test_a_wrong_underline_is_a_load_error(tmp_path):
    from tesserae.spec.nodes import LoadError

    with pytest.raises(LoadError, match="underline"):
        opened(tmp_path, "  - {widget: Link, name: l, text: Docs, underline: wavy}\n")


def test_a_failed_open_does_not_mark_it_visited(tmp_path, monkeypatch):
    monkeypatch.setattr(urls, "open_url", lambda url: False)
    view, vm = opened(tmp_path, "  - {widget: Link, name: l, text: Docs, href: 'https://example.com', visited: \"{{ seen }}\"}\n")
    view.window.simulate("click", node=box(view))
    assert vm.seen.get() is False


def test_focus_a_mouse_click_gave_does_not_underline_it_once_the_pointer_has_gone(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Link, name: l, text: Docs}\n")
    node = box(view)
    x, y = node.get("layout_x") + 4, node.get("layout_y") + 4
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.simulate("pointer_up", x=x, y=y)
    away(view)
    view.window.advance(16)
    assert not underlined(view)


def test_the_underline_covers_text_that_is_more_than_one_byte_a_letter(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Link, name: l, text: \"Caf\u00e9\"}\n")
    hover(view)
    assert text(view).get("spans")[0][:2] == (0, 5)
