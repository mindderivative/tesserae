"""#284: an editable `model` property given one bare name that cannot be written back looks two-way and is not, so the composer says so (a warning in the log,
with the file, line and column), once for the place in the file. Anything that is deliberately one-way, or is two-way, stays quiet."""

import pytest
from loguru import logger

from tesserae import Computed, Signal

from test_compose import VM, make

CALL = "params:\n  m: {type: bool, default: false, model: true}\n  p: {type: bool, default: false}\nwidget: Checkbox\nchecked: '{{ m }}'\n"


@pytest.fixture
def said():
    lines = []
    sink = logger.add(lambda message: lines.append(message.record["message"]), level="WARNING")
    yield lines
    logger.remove(sink)


class Flags(VM):
    def __init__(self):
        super().__init__()
        self.done = Signal(False)
        self.inverse = Computed(lambda: not self.done.get())
        self.plain = False
        self.caption = "hi"
        self.flags = Signal([True, False])


def checkbox(value, extra="", vm=None):
    return make(None, f"widget: Container\n{extra}children:\n  - {{widget: Checkbox, name: c, checked: '{value}'}}", viewmodel=vm or Flags())


@pytest.mark.parametrize("value, what", [("{{ inverse }}", "a Computed"), ("{{ plain }}", "a ViewModel attribute that is not a Signal")])
def test_a_bare_name_that_cannot_be_written_back_is_said_with_its_place(said, value, what):
    checkbox(value)
    assert len(said) == 1 and said[0].startswith("Main_View.yaml:3:") and what in said[0] and "Checkbox checked is given" in said[0]


def test_a_loop_variable_is_said(said):
    make(None, "widget: Container\nchildren:\n  - {for: f in flags, key: f, widget: Checkbox, name: c, checked: '{{ f }}'}", viewmodel=Flags())
    assert len(said) == 1 and "a read-only param or loop variable" in said[0]  # two rows, one line: it is said once for the place


def test_a_plain_param_given_to_a_model_property_is_said(said):
    view = "params:\n  p: {type: bool, default: false}\nwidget: Checkbox\nchecked: '{{ p }}'\n"
    make({"V": view}, "widget: Container\nchildren:\n  - {widget: V, name: v}")
    assert len(said) == 1 and "'p'" in said[0] and "V_View.yaml:4:" in said[0]


def test_a_call_that_gives_a_model_param_such_a_name_is_said(said):
    make({"V": CALL}, "widget: Container\nchildren:\n  - {widget: V, name: v, m: '{{ inverse }}'}", viewmodel=Flags())
    assert len(said) == 1 and "V m is given 'inverse', which is a Computed" in said[0] and "Main_View.yaml:3:" in said[0]


@pytest.mark.parametrize("value", ["{{ done }}", "{{ flag }}", "{{ not done }}", "{{ inverse and True }}"])
def test_a_two_way_binding_and_a_deliberate_one_way_expression_say_nothing(said, value):
    checkbox(value, extra="state: {flag: true}\n")
    assert said == []


def test_a_literal_says_nothing(said):
    make(None, "widget: Container\nchildren:\n  - {widget: Checkbox, name: c, checked: true}", viewmodel=Flags())
    assert said == []


def test_a_model_param_passed_on_is_two_way_and_says_nothing(said):
    out = "params:\n  q: {type: bool, default: false, model: true}\nwidget: V\nm: '{{ q }}'\n"
    make({"V": CALL, "Out": out}, "widget: Container\nchildren:\n  - {widget: Out, name: o, q: '{{ done }}'}", viewmodel=Flags())
    assert said == []


def test_a_property_the_user_does_not_edit_says_nothing(said):
    make(None, "widget: Container\nchildren:\n  - {widget: Text, name: t, text: '{{ caption }}'}", viewmodel=Flags())
    assert said == []


def test_a_name_nothing_has_is_not_this_warnings_to_make(said):
    with pytest.raises(Exception):
        checkbox("{{ nosuch }}")
    assert not any("is given" in line for line in said)
