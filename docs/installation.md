# Installation

Tesserae is pre-alpha, and on PyPI as
[**`tesserae-ui`**](https://pypi.org/project/tesserae-ui/) (imported as
`tesserae`; `tesserae` on PyPI is an unrelated project):

```bash
pip install tesserae-ui
```

That also installs **`tre` 0.4.0 or newer**, which is on PyPI as
[`tesserae-engine`](https://pypi.org/project/tesserae-engine/) (imported
as `tre`). The rest of this page is for working on Tesserae itself, from
a local editable checkout.

## Requirements

- Python 3.9 or newer
- Linux, macOS, or Windows -- whatever `tre` itself supports (see
  [`tre`'s own installation guide](https://mindderivative.github.io/tre/installation/)).
  `tesserae-engine` 0.4.0 has wheels for CPython 3.9–3.15 (and the
  free-threaded 3.14t and 3.15t) on Linux x86_64, CPython 3.9–3.14 on
  macOS arm64 and Windows, and PyPy 3.11 on Linux. Elsewhere (Linux
  aarch64, Intel macOS) pip builds it from the sdist, which needs Rust
  1.90 or newer.

## Get the checkout

```bash
git clone https://github.com/mindderivative/tesserae.git
cd tesserae
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

!!! warning "Coming from a GitHub `tre` wheel"
    If this environment has a `tre-...` wheel from a GitHub release (Tesserae
    used them before 0.3.5.2), run `pip uninstall tre` **first**. pip treats
    `tesserae-engine` as a different project and leaves the old `tre`
    distribution installed; both then own the `tre` package, and a later
    `pip uninstall tre` would delete files `tesserae-engine` needs.

0.3.5 and later have only `tre`'s building blocks: its declarative views,
reactivity, MD3 widgets and theming are gone, and Tesserae provides them
(see `tre`'s [migration page](https://github.com/mindderivative/tre/blob/v0.3.5/docs/migrating-0.3.5.md)
if you also use `tre` directly).

!!! note "Testing against unreleased `tre`"
    To try Tesserae against a `tre` checkout you're working on, install
    it editable instead: `python -m maturin develop --release
    --manifest-path /path/to/tre/crates/engine-py/Cargo.toml` with
    Tesserae's `.venv` active. From then on your local results follow
    that checkout -- every rebuild changes them -- so go back to the
    released one (`pip install --force-reinstall "tesserae-engine>=0.4.0"`)
    before trusting a test run. A real-font test reads a font file from
    `tre`'s source tree: set `TRE_SOURCE_DIR` to a `tre` checkout to run
    it (CI does).

Then install Tesserae itself, editable, with dev extras:

```bash
pip install -e ".[dev]"
```

This also installs Tesserae's dependencies from PyPI: `tesserae-engine`
(`tre`); PyYAML, for
reading view files; Pillow, for decoding images; and watchfiles, for
hot reload. Tesserae reads, decodes and watches every file itself and
hands `tre` only the data.

## Verify it worked

```bash
pytest tests/
python examples/counter/app.py
```

A real window should open with a `Count: 0` label and a button --
clicking it increments the count through a genuine dispatched click and
render loop.

The parity tests (bindings, trees, the cascade, theme tokens) compare
Tesserae with `tre`'s answers recorded in `tests/reference/`, so they
need no `tre` reference at runtime. If you change what one asks `tre`,
record again with `python tools/record_tre_reference.py` in an
environment with `tre` 0.3.4 (0.3.5 has no `View` to ask); it writes the
files only if every test passes.

## Keeping `tre` up to date

`tre` ships real releases (tags/GitHub Releases) roughly one per
accumulated batch of changes rather than one per commit -- when you
pull a new `tre` version, re-run `maturin develop --release` inside
`tre`'s own checkout (targeting Tesserae's `.venv`) and re-run
Tesserae's own test suite before assuming nothing broke; a real
breaking API/schema change (like `tre` v0.3.0's `flex_direction`
rename) is possible between versions and is documented in `tre`'s own
release notes.
