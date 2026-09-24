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
) -> dict[str, Any]:
    """Replace one `{component: Name, with: {...}}` node with the
    fragment it names, fully expanded and namespaced."""
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
    fragment = _load_fragment(path)
    declared = fragment.pop(_PARAMS_KEY, []) or []
    if not isinstance(declared, list):
        raise ComponentError(f"{path}: `params:` must be a list of names")

    supplied = node.get(_WITH_KEY) or {}
    if not isinstance(supplied, dict):
        raise ComponentError(f"{_chain_text((*chain, name))}: `with:` must be a mapping")

    missing = [p for p in declared if p not in supplied]
    if missing:
        raise ComponentError(
            f"{_chain_text((*chain, name))}: missing parameter(s) {missing}; "
            f"{name} declares {declared}"
        )
    unknown = [k for k in supplied if k not in declared]
    if unknown:
        raise ComponentError(
            f"{_chain_text((*chain, name))}: unknown parameter(s) {unknown}; "
            f"{name} declares {declared or '[]'}"
        )

    fragment = _substitute(fragment, supplied)

    # Resolve any `component:` usage inside the fragment itself before
    # namespacing -- a nested fragment's own ids get namespaced by the
    # OUTER call site's id too, once, not twice.
    fragment = _walk(fragment, component_dirs, (*chain, name))

    local_id = fragment.get(_ID_KEY)
    fragment = _namespace_ids(fragment, call_id)
    if isinstance(local_id, str):
        # The fragment's own root gets the call site's id directly, not
        # a further "call_id.call_id"-prefixed one.
        fragment[_ID_KEY] = call_id

    extra = set(node) - {_COMPONENT_KEY, _WITH_KEY, _ID_KEY}
    if extra:
        raise ComponentError(
            f"{_chain_text((*chain, name))}: a `component:` node takes only `id:` and "
            f"`with:`; got {sorted(extra)}. Pass configuration as parameters."
        )
    return fragment


def _walk(node: Any, component_dirs: list[Path], chain: tuple[str, ...]) -> Any:
    if isinstance(node, list):
        return [_walk(v, component_dirs, chain) for v in node]
    if not isinstance(node, dict):
        return node
    if _COMPONENT_KEY in node:
        return _expand_component(dict(node), component_dirs, chain)
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
