# `instantiate`

**`instantiate(parent, path, viewmodel_cls, into, *args, **kwargs) ->
(component, viewmodel)`**

Instantiates the component at `path` into `into` (a `Node`, e.g. from
`parent.node(widget_id)`), constructs `viewmodel_cls(component, *args,
**kwargs)`, and returns `(component, viewmodel)`.

- `parent` -- whatever already has a real `instantiate(path, into)` of
  its own: a `View` or another `Component` (they nest, so a component
  can itself hold further nested components this same way).
- `path` -- a `*_View.yaml` file, checked against the same naming
  convention `App.load` enforces (see
  [Naming Convention](../guide/naming-convention.md)).
- `viewmodel_cls` -- checked against the same convention (its own
  defining file must end `_ViewModel.py`, sharing `path`'s prefix).
- `into` -- the `Node` to embed under.
- `*args`/`**kwargs` -- forwarded to `viewmodel_cls(component, *args,
  **kwargs)`.

Raises `ValueError` immediately on a naming-convention mismatch,
before any real embedding happens.

See [Components & Embedding](../guide/components.md) for a full
worked example.
