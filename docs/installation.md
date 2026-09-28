# Installation

Tesserae is pre-alpha and not yet published to PyPI -- install it as a
local editable checkout. It will be published as **`tesserae-ui`**
(`tesserae` on PyPI is an unrelated project), and it's still imported as
`tesserae` ([#15](https://github.com/mindderivative/tesserae/issues/15)). It targets one specific `tre` release, the same
one its CI pins: **`tre` v0.3.5.1**.

## Requirements

- Python 3.9 or newer
- Linux, macOS, or Windows -- whatever `tre` itself supports (see
  [`tre`'s own installation guide](https://mindderivative.github.io/tre/installation/))
- A Rust toolchain, only if you build `tre` from source (`rustup`'s
  default stable toolchain works)

## Install `tre` v0.3.5.1

Create a virtual environment in your Tesserae checkout:

```bash
git clone https://github.com/mindderivative/tesserae.git
cd tesserae
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

Then install `tre` v0.3.5.1, either from the wheel for your platform on the
[v0.3.5.1 release page](https://github.com/mindderivative/tre/releases/tag/v0.3.5.1)
(CPython 3.9–3.15 on Linux, macOS arm64 and Windows):

```bash
pip install /path/to/downloaded/tre-0.3.5.1-<your-platform>.whl
```

or by building that tag from source:

```bash
git clone --branch v0.3.5.1 https://github.com/mindderivative/tre.git ../tre-v0.3.5.1
pip install maturin
python -m maturin build --release --manifest-path ../tre-v0.3.5.1/crates/engine-py/Cargo.toml --out dist
pip install dist/tre-0.3.5.1-*.whl
```

0.3.5 (and its 0.3.5.1 fix) has only `tre`'s building blocks: its declarative views,
reactivity, MD3 widgets and theming are gone, and Tesserae provides them
(see `tre`'s [migration page](https://github.com/mindderivative/tre/blob/v0.3.5/docs/migrating-0.3.5.md)
if you also use `tre` directly).

!!! note "Testing against unreleased `tre`"
    To try Tesserae against a `tre` checkout you're working on, install
    it editable instead: `python -m maturin develop --release
    --manifest-path /path/to/tre/crates/engine-py/Cargo.toml` with
    Tesserae's `.venv` active. From then on your local results follow
    that checkout -- every rebuild changes them -- so switch back to the
    v0.3.5.1 wheel (`pip install --force-reinstall ...`) before trusting a
    test run.

Then install Tesserae itself, editable, with dev extras:

```bash
pip install -e ".[dev]"
```

This also installs Tesserae's own dependencies from PyPI: PyYAML, for
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
