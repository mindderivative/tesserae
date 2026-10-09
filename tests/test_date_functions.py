"""The date functions of the expression language: `date_add_days`, `date_weekday`, `days_in_month` and `format_date`."""

import pytest

from tesserae.expr import ExprError, compile_expr


def run(source, **names):
    from tesserae.expr import MapScope

    return compile_expr(source).evaluate(MapScope(names))


def test_a_date_moves_by_days_across_months_and_years():
    assert run("date_add_days('2026-10-09', 1)") == "2026-10-10"
    assert run("date_add_days('2026-10-31', 1)") == "2026-11-01"
    assert run("date_add_days('2026-01-01', -1)") == "2025-12-31"
    assert run("date_add_days('2024-02-28', 2)") == "2024-03-01"  # a leap year


def test_the_weekday_counts_from_monday_as_zero():
    assert run("date_weekday('2026-10-05')") == 0 and run("date_weekday('2026-10-11')") == 6


def test_the_days_in_a_month_know_leap_years():
    assert run("days_in_month(2026, 2)") == 28 and run("days_in_month(2024, 2)") == 29 and run("days_in_month(2026, 10)") == 31


def test_a_date_is_written_as_asked():
    assert run("format_date('2026-10-09')") == "Fri, Oct 09"
    assert run("format_date('2026-10-09', '%A, %B %e')") == "Friday, October 9"
    assert run("format_date('2026-03-04', '%d/%m/%Y')") == "04/03/2026" and run("format_date('2026-03-04', '%y 100%%')") == "26 100%"


@pytest.mark.parametrize("source", ["date_add_days('soon', 1)", "date_weekday('2026-13-01')", "format_date('2026-10-09', '%Q')", "format_date('2026-10-09', '%')"])
def test_a_wrong_date_or_pattern_is_an_error(source):
    with pytest.raises((ExprError, ValueError)):
        run(source)
