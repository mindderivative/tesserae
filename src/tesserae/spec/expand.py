"""Component macro-expansion: `component: Name` / `with: {...}` in a
`*_View.yaml` expands to the referenced `*_Component.yaml` fragment's own
`WidgetSpec`-shaped subtree, before `tre` ever sees the file. Modeled
directly on pyCopper's own real, proven `source:`/`with:`/`params:`
design (`pycopper/spec/include.py`), adapted to `tre`'s real schema
(`id`/`kind`/`style`/`text`/`children`, confirmed against
`engine-spec/src/spec.rs` -- no `anchor:`-style cross-reference field
exists, so only `id:` needs namespacing, unlike pyCopper's own `name:`+
`anchor:` pair).

Deliberately does NOT touch a literal `include:` key -- `tre` already has
a real, working, parameterization-free splice mechanism for that
(`engine-spec/src/include.rs`); this module only adds the missing
capability, parameterized reuse.

M28: `repeat:` lets one `component:` entry expand to N sibling
instances from a literal, static list of per-item overrides -- real,
deliberately narrow scope, confirmed against `tre`'s own imperative
`add_list` first: it takes pre-built `Node`s and does pure layout
composition (`window_factory.rs`, no `NodeKind::List` primitive at
all), meaning "a list" is *already* expressible today as a plain
`kind: Container` with N `ListItem` children -- the real, missing
capability isn't a primitive, it's repeating a fragment call without
hand-duplicating N near-identical `component:` blocks. Deliberately
NOT reactive -- `repeat:`'s own items are known at macro-expansion
time, before `tre` ever sees the file (matching this whole module's
own "before `tre` ever sees the file" framing), so an app wanting
runtime-changing content (items added/removed, live reordering) still
uses the existing imperative `tesserae.Repeater`, not this. Checked
`pyCopper` directly (M26/M28's own scoping) -- no repeat/loop construct
exists there at all, confirming this is genuinely new design territory,
not a port.

Real, load-bearing design point: `{{ param }}` substitution preserves
the supplied value's own real Python type (int/float/bool/str) when a
string is *exactly* one placeholder with nothing else around it --
verified necessary directly: PyYAML's `safe_dump` quotes a numeric-
looking Python `str`, which would turn `width: "{{ width }}"` into
`width: '120'` after substitution -- a quoted string `tre`'s own
`serde_yaml_ng` parser rejects for an `f32` field. Only genuinely mixed
strings (a placeholder embedded in surrounding text) fall back to plain
string interpolation, where stringifying is correct. This same
whole-value rule is what lets `with: {label: "{{ some_signal.get() }}"}`
forward a live `tre` binding expression through untouched -- the
supplied value is itself the string `"{{ some_signal.get() }}"`, so a
whole-value substitution reproduces it exactly, for `tre`'s own
`binding.rs` to resolve later at `View._attach()` time.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

__all__ = ["ComponentError", "expand_components"]

_COMPONENT_KEY = "component"
_WITH_KEY = "with"
_PARAMS_KEY = "params"
_ID_KEY = "id"
_CHILDREN_KEY = "children"
_REPEAT_KEY = "repeat"

#: A guard against pathological/adversarial nesting, not a real depth
#: any legitimate component tree needs. `tre`'s own `include:` uses 8
#: for a simpler, unparameterized splice; this allows real component-
#: composing-component nesting (e.g. a `Card` fragment using `component:
#: Button` inside it) some real headroom without being unbounded.
MAX_DEPTH = 16

_WHOLE_PARAM_RE = re.compile(r"^\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}$")
_PARAM_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class ComponentError(ValueError):
    """A `component:` reference that cannot be expanded, with the call
    chain that led to it."""


def _chain_text(chain: tuple[str, ...]) -> str:
    return " -> ".join(chain) if chain else "<root>"


def _substitute(node: Any, values: dict[str, Any]) -> Any:
    """Replace every `{{ name }}` in `node` with its supplied value.

    A string that is *exactly* one placeholder (optionally surrounded by
    whitespace, nothing else) is replaced with the supplied value's own
    real type -- required so a numeric param round-trips as a real YAML
    number, not a quoted string. A placeholder embedded in a larger
    string is replaced via plain string interpolation instead.
    """
    if isinstance(node, str):
        whole = _WHOLE_PARAM_RE.match(node)
        if whole:
            name = whole.group(1)
            return values[name] if name in values else node
        return _PARAM_RE.sub(
            lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), node
        )
    if isinstance(node, dict):
        return {k: _substitute(v, values) for k, v in node.items()}
    if isinstance(node, list):
        return [_substitute(v, values) for v in node]
    return node


def _namespace_ids(node: Any, prefix: str) -> Any:
    """Prefix every `id:` inside `node` with `prefix.`, except the
    fragment's own root `id:`, which the caller already renamed to
    `prefix` directly (mirrors pyCopper's own `_namespace_names`,
    adapted from `name:`/`anchor:` to `tre`'s single `id:` field --
    `WidgetSpec` has no cross-reference field an id-rename could break).
    """
    if isinstance(node, list):
        return [_namespace_ids(v, prefix) for v in node]
    if not isinstance(node, dict):
        return node
    out: dict[str, Any] = {}
    for key, value in node.items():
        if key == _ID_KEY and isinstance(value, str):
            out[key] = f"{prefix}.{value}"
        else:
            out[key] = _namespace_ids(value, prefix)
    return out


def _find_component_file(name: str, component_dirs: list[Path]) -> Path:
    for directory in component_dirs:
        candidate = directory / f"{name}_Component.yaml"
        if candidate.is_file():
            return candidate
    searched = ", ".join(str(d) for d in component_dirs)
    raise ComponentError(f"unknown component {name!r} -- searched {searched}")


def _load_fragment(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ComponentError(f"{path}: invalid YAML: {exc}") from exc
    except OSError as exc:
        raise ComponentError(f"cannot read {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ComponentError(f"{path}: a component fragment must be a mapping, got {type(raw).__name__}")
    return raw


def _expand_component(
    node: dict[str, Any],
    component_dirs: list[Path],
    chain: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Replace one `{component: Name, with: {...}}` node with the
    fragment(s) it names, fully expanded and namespaced -- one element
    normally, or one per real `repeat:` entry (M28)."""
    if len(chain) >= MAX_DEPTH:
        raise ComponentError(f"{_chain_text(chain)}: components nested more than {MAX_DEPTH} deep")

    name = node[_COMPONENT_KEY]
    if not isinstance(name, str):
        raise ComponentError(f"{_chain_text(chain)}: `component:` must be a string, got {name!r}")
    if name in chain:
        raise ComponentError(f"component cycle: {_chain_text((*chain, name))}")

    call_id = node.get(_ID_KEY)
    if not isinstance(call_id, str):
        raise ComponentError(
            f"{_chain_text((*chain, name))}: a `component:` entry needs its own `id:` "
            "(used to namespace the fragment's own internal ids)"
        )

    path = _find_component_file(name, component_dirs)
    fragment_template = _load_fragment(path)
    declared = fragment_template.pop(_PARAMS_KEY, []) or []
    if not isinstance(declared, list):
        raise ComponentError(f"{path}: `params:` must be a list of names")

    with_supplied = node.get(_WITH_KEY) or {}
    if not isinstance(with_supplied, dict):
        raise ComponentError(f"{_chain_text((*chain, name))}: `with:` must be a mapping")

    extra = set(node) - {_COMPONENT_KEY, _WITH_KEY, _ID_KEY, _REPEAT_KEY}
    if extra:
        raise ComponentError(
            f"{_chain_text((*chain, name))}: a `component:` node takes only `id:`, `with:`, "
            f"and `repeat:`; got {sorted(extra)}. Pass configuration as parameters."
        )

    # M28: `repeat:` -- one iteration per entry, each a mapping of
    # per-item values merged on top of the shared `with:` values. A
    # real key given in both is rejected rather than silently letting
    # one win, matching this module's own "fail loudly on ambiguity"
    # convention every other real check here already follows.
    repeat_items = node.get(_REPEAT_KEY)
    if repeat_items is None:
        iterations = [(call_id, dict(with_supplied))]
    else:
        if not isinstance(repeat_items, list):
            raise ComponentError(
                f"{_chain_text((*chain, name))}: `repeat:` must be a list of mappings, "
                f"got {type(repeat_items).__name__}"
            )
        iterations = []
        for index, item in enumerate(repeat_items):
            if not isinstance(item, dict):
                raise ComponentError(
                    f"{_chain_text((*chain, name))}: `repeat:` entry {index} must be a "
                    f"mapping, got {type(item).__name__}"
                )
            overlap = set(item) & set(with_supplied)
            if overlap:
                raise ComponentError(
                    f"{_chain_text((*chain, name))}: `repeat:` entry {index} repeats "
                    f"key(s) {sorted(overlap)} already given in `with:` -- a value "
                    "that varies per item belongs in `repeat:`, a shared one in `with:`, "
                    "not both"
                )
            iterations.append((f"{call_id}.{index}", {**with_supplied, **item}))

    results = []
    for local_call_id, supplied in iterations:
        missing = [p for p in declared if p not in supplied]
        if missing:
            raise ComponentError(
                f"{_chain_text((*chain, name))}: missing parameter(s) {missing} for "
                f"{local_call_id!r}; {name} declares {declared}"
            )
        unknown = [k for k in supplied if k not in declared]
        if unknown:
            raise ComponentError(
                f"{_chain_text((*chain, name))}: unknown parameter(s) {unknown} for "
                f"{local_call_id!r}; {name} declares {declared or '[]'}"
            )

        fragment = _substitute(fragment_template, supplied)

        # Resolve any `component:` usage inside the fragment itself
        # before namespacing -- a nested fragment's own ids get
        # namespaced by the OUTER call site's id too, once, not twice.
        fragment = _walk(fragment, component_dirs, (*chain, name))

        local_id = fragment.get(_ID_KEY)
        fragment = _namespace_ids(fragment, local_call_id)
        if isinstance(local_id, str):
            # The fragment's own root gets the call site's id directly,
            # not a further "local_call_id.local_call_id"-prefixed one.
            fragment[_ID_KEY] = local_call_id
        results.append(fragment)

    return results


def _expand_list_item(item: Any, component_dirs: list[Path], chain: tuple[str, ...]) -> list[Any]:
    """One `children:` entry expands to 0+ real nodes -- 1 for an
    ordinary node (component or not), N for a real `repeat:` (M28)."""
    if isinstance(item, dict) and _COMPONENT_KEY in item:
        return _expand_component(dict(item), component_dirs, chain)
    return [_walk(item, component_dirs, chain)]


def _walk(node: Any, component_dirs: list[Path], chain: tuple[str, ...]) -> Any:
    if isinstance(node, list):
        out: list[Any] = []
        for item in node:
            out.extend(_expand_list_item(item, component_dirs, chain))
        return out
    if not isinstance(node, dict):
        return node
    if _COMPONENT_KEY in node:
        results = _expand_component(dict(node), component_dirs, chain)
        if len(results) != 1:
            raise ComponentError(
                f"{_chain_text(chain)}: `repeat:` produced {len(results)} nodes, but this "
                "position needs exactly one -- `repeat:` is only valid on a `component:` "
                "entry inside a `children:` list"
            )
        return results[0]
    return {
        k: (_walk(v, component_dirs, chain) if k == _CHILDREN_KEY else v) for k, v in node.items()
    }


def expand_components(yaml_text: str, *, component_dirs: list[Path] | None = None) -> str:
    """Expands every `component:` entry in `yaml_text`, returning fully
    expanded `WidgetSpec`-shaped YAML text with no `component:`/`with:`/
    `params:` keys remaining -- ready for `tre.View(source=...)`.

    `component_dirs` defaults to Tesserae's own built-in
    `spec/components/` directory; a caller may pass additional
    directories (searched in order) to add or shadow components with
    an app's own -- not yet exercised by any real caller.
    """
    dirs = component_dirs if component_dirs is not None else [Path(__file__).parent / "components"]
    data = yaml.safe_load(yaml_text)
    expanded = _walk(data, dirs, ())
    return yaml.safe_dump(expanded, sort_keys=False)
