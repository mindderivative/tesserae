# Installation

Tesserae is pre-alpha, and on PyPI as
[**`tesserae-ui`**](https://pypi.org/project/tesserae-ui/) (imported as
`tesserae`; `tesserae` on PyPI is an unrelated project):

```bash
pip install tesserae-ui
```

That also installs **`tre` 0.5.1 or newer, below 0.6**, which is on PyPI as
[`tesserae-engine`](https://pypi.org/project/tesserae-engine/) (imported
as `tre`). The rest of this page is for working on Tesserae itself, from
a local editable checkout.

## Requirements

- Python 3.12 or newer. (On macOS, the `python3` that comes with
  Xcode's command-line tools is 3.9: install 3.12+ from python.org or
  Homebrew.)
- Linux x86-64, macOS on Apple silicon, or Windows x64. On these, every
  dependency -- `tre`'s engine included -- installs as a prebuilt wheel,
  so one `pip install` is all it takes. Elsewhere (Linux ARM, Intel
  macOS) pip builds `tre` from source, which needs Rust 1.90 or newer
  (see [`tre`'s own installation guide](https://mindderivative.github.io/tre/installation/)).

## Get the checkout

```bash
git clone https://github.com/mindderivative/tesserae.git
cd tesserae
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

!!! note "Testing against unreleased `tre`"
    To try Tesserae against a `tre` checkout you're working on, install
    it editable instead: `python -m maturin develop --release
    --manifest-path /path/to/tre/crates/engine-py/Cargo.toml` with
    Tesserae's `.venv` active. From then on your local results follow
    that checkout -- every rebuild changes them -- so go back to the
    released one (`pip install --force-reinstall "tesserae-engine>=0.5.1,<0.6"`)
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

`tre` publishes to PyPI as `tesserae-engine`, and Tesserae's requirement
(`>=0.5.1,<0.6`) says which versions it works with. To pick up a newer
one inside that range, `pip install --upgrade tesserae-engine` and re-run
Tesserae's test suite. A new `tre` line (0.6) is a new Tesserae line.
