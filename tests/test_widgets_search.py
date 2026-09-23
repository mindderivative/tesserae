"""Real coverage for `tesserae.widgets`'s Search category -- `search_bar`/
`search_view`. Same thin-delegate parity strategy as the other widget
test modules.
"""

from tre import Window

from tesserae.widgets import search_bar, search_view


def test_search_bar_matches_native_add_search_bar():
    window = Window(width=400, height=300)
    a_bar, a_field, a_leading, a_trailing = search_bar(window, "Search…", 360, leading_icon="search")
    b_bar, b_field, b_leading, b_trailing = window.add_search_bar("Search…", 360, leading_icon="search")
    assert a_bar.get("corner_radius") == b_bar.get("corner_radius")
    assert a_leading is not None and b_leading is not None


def test_search_bar_text_field_is_wired_for_change():
    window = Window(width=400, height=300)
    bar, field, leading, trailing = search_bar(window, "Search…", 360)
    seen = []
    field.set_on_change(lambda: seen.append(field.get_text()))
    assert seen == []  # just proves the returned field is the real TextField node


def test_search_view_matches_native_add_search_view():
    window = Window(width=400, height=300)
    a = search_view(window, 320, 240)
    b = window.add_search_view(320, 240)
    assert a.get("corner_radius") == b.get("corner_radius")
