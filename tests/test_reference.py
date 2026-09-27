"""M43 Phase 3: `tests/reference.py`, the recorded `tre` answers the parity
tests replay. Its encoding must give back exactly what `tre` answered."""

import json

import pytest

import reference


@pytest.mark.parametrize("value", [
    None, True, 3, 2.5, "text", (1, 2, (3, 4)), [1, (2, 3)], {"a": (1, 2)}, {1: "one", "k": [None]},
    {"__tuple__": 1}, [((0, 0, 0, 77), 0.0, 1.0, 2.0, 0.0)],
])
def test_answers_round_trip_exactly(value):
    decoded = reference.decode(json.loads(json.dumps(reference.encode(value))))
    assert decoded == value and type(decoded) is type(value)


def test_an_object_that_isnt_plain_data_cant_be_recorded():
    with pytest.raises(TypeError, match="have fn return plain data"):
        reference.encode(object())


def test_a_recorded_exception_is_raised_again_with_its_type_and_message(monkeypatch):
    monkeypatch.setattr(reference, "RECORDING", False)
    monkeypatch.setitem(reference.STORE.modules, "fake", {
        "x#1": {"__raises__": ["ValueError", 'widget "x": bad']},
        "x#2": {"__raises__": ["PanicException", "boom"]},
    })
    reference.begin("fake", "x")
    with pytest.raises(ValueError, match='widget "x": bad'):
        reference.tre(lambda: pytest.fail("not called when replaying"))
    with pytest.raises(Exception, match="boom"):  # not a builtin: a generic stand-in
        reference.tre(lambda: None)
    with pytest.raises(reference.MissingAnswer, match="run tools/record_tre_reference.py"):
        reference.tre(lambda: None)
