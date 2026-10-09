"""The build order of the 0.5.0 components (`tools/component_order.yaml` -> `design/component-order.md`) is a real order: every component issue is placed once,
every need exists, nothing needs itself, and the document is what the generator writes."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("generate_component_order", ROOT / "tools" / "generate_component_order.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_component_issue_is_in_exactly_one_unit_and_every_need_exists(tool):
    assert tool.problems(tool.load()) == []


def test_the_graph_has_no_cycle_and_levels_follow_needs(tool):
    nodes = tool.load()
    level = tool.levels(nodes)
    for name, node in nodes.items():
        assert all(level[need] < level[name] for need in node["needs"]), name
        assert (level[name] == 0) == (not node["needs"]), name


def test_a_step_always_comes_after_everything_it_needs(tool):
    nodes = tool.load()
    position = {name: i for i, name in enumerate(tool.order(nodes))}
    for name, node in nodes.items():
        assert all(position[need] < position[name] for need in node["needs"]), name


def test_a_cycle_is_named(tool):
    nodes = {"a": {"id": "a", "kind": "tesserae", "needs": ["b"], "issues": []}, "b": {"id": "b", "kind": "tesserae", "needs": ["a"], "issues": []}}
    with pytest.raises(ValueError, match="a cycle: a -> b -> a"):
        tool.levels(nodes)


def test_a_missing_or_repeated_issue_is_reported(tool):
    nodes = tool.load()
    nodes["text"]["issues"] = []
    assert "#195 is in no unit" in tool.problems(nodes)
    nodes = tool.load()
    nodes["svg"]["issues"] = [197, 195]
    assert "#195 is in text and svg" in tool.problems(nodes)
    nodes = tool.load()
    nodes["svg"]["issues"] = [197, 500]
    assert "#500 is not a component issue" in tool.problems(nodes)


def test_the_things_that_wait_on_tre_are_marked_and_have_something_waiting(tool):
    nodes = tool.load()
    below = tool.dependents(nodes)
    for name, node in nodes.items():
        if node.get("gated"):
            assert node["kind"] == "tre" and any(nodes[d]["kind"] == "component" for d in below[name]), name
    assert {n for n, node in nodes.items() if node["kind"] == "tre"} >= {"engine-a11y", "engine-layout-animation", "engine-input"}


def test_a_requested_tre_change_is_asked_for_only_after_what_it_rests_on(tool):
    nodes = tool.load()
    level = tool.levels(nodes)
    assert level["engine-layout-animation"] > level["transition-paint"] and level["engine-a11y"] > level["a11y-now"]
    assert level["transition-layout"] > level["engine-layout-animation"] and level["a11y-full"] > level["engine-a11y"]


def test_the_texts_loose_ends_come_after_everything_they_need(tool):
    nodes = tool.load()
    position = {name: i for i, name in enumerate(tool.order(nodes))}
    finish = nodes["textfield-finish"]
    assert {"transition-layout", "corner-radius", "a11y-full", "focus", "input-mask", "menu", "engine-input"} <= set(finish["needs"])
    assert all(position[need] < position["textfield-finish"] for need in finish["needs"])


def test_the_document_is_what_the_generator_writes(tool):
    assert (ROOT / "design" / "component-order.md").read_text(encoding="utf-8") == tool.render(), \
        "design/component-order.md is out of date: run `python tools/generate_component_order.py`"
