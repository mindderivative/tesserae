"""#222: `mask` on a TextInput (and so on a TextField): the typed or pasted text is put in the pattern."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.mask import Mask
from tesserae.spec.nodes import LoadError, parse_view

PHONE = "(###) ###-####"


@pytest.mark.parametrize("pattern, typed, shown", [
    (PHONE, "", ""), (PHONE, "1", "(1"), (PHONE, "123", "(123"), (PHONE, "1234", "(123) 4"),
    (PHONE, "1234567890", "(123) 456-7890"), (PHONE, "123-456-7890", "(123) 456-7890"), (PHONE, "(123) 456-7890", "(123) 456-7890"),
    (PHONE, "(123)", "(123)"), (PHONE, "(123) ", "(123) "), (PHONE, "abc12", "(12"), (PHONE, "12345678901234", "(123) 456-7890"),
    ("##/##/####", "123", "12/3"), ("##/##/####", "12/", "12/"), ("##/##/####", "1/2", "12"), ("##/##/####", "12/34/20201", "12/34/2020"),
    ("AA-####", "ab1234", "ab-1234"), ("AA-####", "a1b-1234", "ab-1234"), ("AA-####", "1234", ""),
    ("**-**", "a1b2", "a1-b2"), ("**-**", "a!1", "a1"),
    (r"\#\##", "5", "##5"), (r"\#\##", "##5", "##5"), ("+1 ###", "5", "+1 5"), ("+1 ###", "+1 55", "+1 55"),
])
def test_text_is_put_in_the_pattern(pattern, typed, shown):
    assert Mask(pattern).apply(typed) == shown


def test_applying_a_mask_to_its_own_output_changes_nothing():
    mask = Mask(PHONE)
    for typed in ("1", "12345", "1234567890", "(123) 4", "(123)"):
        once = mask.apply(typed)
        assert mask.apply(once) == once


def test_a_backspace_is_never_stuck_on_a_literal():
    mask = Mask(PHONE)
    text = mask.apply("1234567890")
    seen = [text]
    while text:
        text = mask.apply(text[:-1])
        seen.append(text)
    assert seen[-1] == "" and len(seen) <= len("(123) 456-7890") + 1


@pytest.mark.parametrize("pattern, message", [
    ("", "a mask is a pattern"), (None, "a mask is a pattern"), ("---", "has no slot"), ("##\\", "ends in a backslash"),
    (r"\#\#", "has no slot"),
])
def test_a_bad_pattern_says_so(pattern, message):
    with pytest.raises(ValueError, match=message):
        Mask(pattern)


# -- in a view -------------------------------------------------------------------------------------------------------------


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.phone = Signal("")


def opened(tmp_path, field):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 400, height: 200}\nchildren:\n" + field)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def type_into(view, node, text):
    node.focus()
    view.window.simulate("input", text=text)
    view.window.advance(16)


def test_typing_into_a_masked_input_formats_it_and_the_signal_gets_the_formatted_text(tmp_path):
    view, vm = opened(tmp_path, f"  - {{widget: TextInput, name: i, text: '{{{{ phone }}}}', mask: '{PHONE}', typography_role: body_large, "
                                "style: {width: 200, height: 30, foreground: '#000000', background: '#FFFFFF'}}\n")
    node = view.node("root.i")
    type_into(view, node, "5551234567")
    assert node.get("text") == "(555) 123-4567" and vm.phone.get() == "(555) 123-4567"


def test_a_text_field_takes_a_mask_through(tmp_path):
    view, vm = opened(tmp_path, f"  - {{widget: TextField, name: f, label: Phone, text: '{{{{ phone }}}}', mask: '{PHONE}'}}\n")
    node = view.node("root.f.box.body.input")
    type_into(view, node, "5551234")
    assert node.get("text") == "(555) 123-4" and vm.phone.get() == "(555) 123-4"


def test_an_input_without_a_mask_is_as_before(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: TextField, name: f, label: Phone, text: '{{ phone }}'}\n")
    type_into(view, view.node("root.f.box.body.input"), "abc-123")
    assert vm.phone.get() == "abc-123"


def test_a_bad_mask_is_a_load_error():
    with pytest.raises(LoadError, match="has no slot"):
        parse_view("widget: TextInput\nmask: '---'\n", "T_View.yaml")
    parse_view("widget: TextInput\nmask: ''\n", "T_View.yaml")
