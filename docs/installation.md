# Installation

Tesserae is pre-alpha and not yet published to PyPI -- both it and
`tre` are installed as local editable checkouts for now.

## Requirements

- Python 3.9 or newer
- A Rust toolchain (`tre` compiles a real Rust extension module;
  `rustup`'s default stable toolchain works)
- Linux, macOS, or Windows -- whatever `tre` itself supports (see
  [`tre`'s own installation guide](https://mindderivative.github.io/tre/installation/))

## Set up both repos

Clone `tre` and `tesserae` as sibling directories:

```bash
git clone https://github.com/mindderivative/tre.git
git clone https://github.com/mindderivative/tesserae.git
```

Create a virtual environment and install `tre` editable first (Tesserae
depends on it directly):

```bash
cd tesserae
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install maturin
cd ../tre && python -m maturin develop --release --manifest-path crates/engine-py/Cargo.toml
```

!!! note
    `maturin develop` needs to run against the same virtual environment
    Tesserae itself will use -- either activate `tesserae`'s `.venv`
    first, or point `maturin` at it directly (`--python
    /path/to/tesserae/.venv/bin/python`).

Then install Tesserae itself, editable, with dev extras:

```bash
cd ../tesserae
pip install -e ".[dev]"
```

This also installs Tesserae's own two dependencies from PyPI: PyYAML,
for reading view files, and Pillow, for decoding images -- Tesserae
reads and decodes every file itself and hands `tre` only the data.

## Verify it worked

```bash
pytest tests/
python examples/counter/app.py
```

A real window should open with a `Count: 0` label and a button --
clicking it increments the count through a genuine dispatched click and
render loop.

## Keeping `tre` up to date

`tre` ships real releases (tags/GitHub Releases) roughly one per
accumulated batch of changes rather than one per commit -- when you
pull a new `tre` version, re-run `maturin develop --release` inside
`tre`'s own checkout (targeting Tesserae's `.venv`) and re-run
Tesserae's own test suite before assuming nothing broke; a real
breaking API/schema change (like `tre` v0.3.0's `flex_direction`
rename) is possible between versions and is documented in `tre`'s own
release notes.
