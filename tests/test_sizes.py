"""#279: the size and inset check agrees with tre 0.5.7 (it takes what tre takes and refuses what tre refuses), so a mistake is found at load, where it is written."""

import pytest
import tre

from tesserae.spec.sizes import INSET_FIELDS, LIMIT_FIELDS, SIZE_FIELDS, size_problem

VALUES = [
    0, 40, 40.5, -3, True, None, "auto", "AUTO", "fit-content", "min-content", "stretch", "50%", "0%", "100%", "12.5%", "-50%", " 50% ", "50%%",
    "calc(100% - 16)", "calc(100% - 16px)", "calc(50% + 4)", "calc(100%)", "calc( 100% - 16 )", "calc(100%-16)", "calc()", "calc(100% - )",
    "calc(16px)", "calc(16)", "calc(16px - 4px)", "16px", "16px + 4", "16 + 4", "50% + 50%", "0", -1, -3.5, "calc(100% / 3)", "calc(2 * 10)", "calc(100% - 2 * 8)", "calc(fit-content)", "100% - 16", "100%-16", "100% - 16 + 4", "100% -16", "16 + 100%",
    "40px", "10vw", "2em", "1e3", "", "  ", "min(50%, 200)", "max(10, 20)",
]
FIELDS = [*SIZE_FIELDS, *LIMIT_FIELDS, "left", "top", "right", "bottom", "inset"]


def engine_takes(window, field, value):
    node = window.create("box", position="absolute") if field in ("left", "top", "right", "bottom", "inset") else window.create("box")
    try:
        node.set(**{field: value})
    except (ValueError, TypeError):
        return False
    return True


@pytest.fixture(scope="module")
def window():
    return tre.Window(width=300, height=200)


@pytest.mark.parametrize("field", FIELDS)
def test_the_check_agrees_with_tre(window, field):
    """For every value in the corpus: Tesserae finds no problem exactly when tre takes it."""
    disagree = [(v, size_problem(field, v), engine_takes(window, field, v)) for v in VALUES
                if (size_problem(field, v) is None) != engine_takes(window, field, v) and v is not None]
    assert not disagree, f"{field}: " + "; ".join(f"{v!r}: check says {p or 'fine'}, tre {'takes' if t else 'refuses'} it" for v, p, t in disagree)


def test_a_field_that_is_not_a_size_is_not_judged():
    assert size_problem("gap", "wide") is None and size_problem("background", 3) is None


@pytest.mark.parametrize("value, fragment", [
    ("40px", "sizes are pixels already: write 40"),
    ("10vw", "`vw` is not a unit here"),
    ("stretch", "flex: fill"),
    ("100%-16", "a space each side"),
    ("calc(2 * 10)", "only `+` and `-`"),
])
def test_the_message_says_what_to_write(value, fragment):
    problem = size_problem("width", value)
    assert problem and problem.startswith("style.width must be") and fragment in problem


def test_the_inset_fields_are_the_ones_tre_has():
    assert set(INSET_FIELDS) >= {"left", "top", "right", "bottom", "inset"}
