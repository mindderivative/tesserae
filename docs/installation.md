# Installation

Tesserae is on PyPI as [**`tesserae-ui`**](https://pypi.org/project/tesserae-ui/)
(you import `tesserae`; `tesserae` on PyPI is an unrelated project):

```bash
pip install tesserae-ui
```

That also installs the rendering engine, `tre`, which is on PyPI as
[`tesserae-engine`](https://pypi.org/project/tesserae-engine/) (imported as
`tre`), and the libraries Tesserae reads files with. A virtual environment keeps
it tidy:

```bash
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install tesserae-ui
python -c "import tesserae; print('Tesserae is ready')"
```

## Requirements

- **Python 3.12 or newer.** On macOS, the `python3` that comes with Xcode's
  command-line tools is older: install Python from python.org or Homebrew.
- **Linux x86-64, macOS on Apple silicon, or Windows x64.** On these every
  dependency, the engine included, installs as a prebuilt wheel. Elsewhere
  (Linux ARM, Intel macOS) pip builds `tre` from source, which needs Rust; see
  [`tre`'s installation guide](https://mindderivative.github.io/tre/installation/).
- **A graphics driver the engine can use.** On Linux that means Vulkan.

### If a window won't open on Linux

A session with no Vulkan driver ends with `no GPU adapter available`: install your
distribution's Mesa Vulkan driver.

```bash
sudo apt install mesa-vulkan-drivers      # Debian, Ubuntu
sudo dnf install mesa-vulkan-drivers      # Fedora
```

An X11 session also needs `libxkbcommon-x11` (a Wayland session doesn't); if an
error names it:

```bash
sudo apt install libxkbcommon-x11-0       # Debian, Ubuntu
sudo dnf install libxkbcommon-x11         # Fedora
```

On Debian and Ubuntu, `python3 -m venv` needs `sudo apt install python3-venv`.

## Working on Tesserae

To change Tesserae itself, work from a checkout:

```bash
git clone https://github.com/mindderivative/tesserae.git
cd tesserae
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
python examples/counter/app.py
```

The last command opens a window with a `Count: 0` label and a button that counts.

- **A newer or local `tre`.** `pip install --upgrade tesserae-engine` picks up
  the newest `tre` Tesserae's requirements allow; re-run the tests after. To try
  a `tre` checkout you're working on, install it editable with
  `python -m maturin develop --release --manifest-path /path/to/tre/crates/engine-py/Cargo.toml`
  with Tesserae's environment active, and reinstall the released one with
  `pip install --force-reinstall tesserae-engine` before trusting a test run. A test
  that reads a font file from `tre`'s source tree needs `TRE_SOURCE_DIR` set to
  that checkout.
- **Documentation.** `pip install mkdocs mkdocs-material`, then `mkdocs serve`. The Python and
  YAML references and the component and stylesheet pages are written from the code
  (`tools/generate_api_docs.py`, `tools/generate_yaml_docs.py`,
  `tools/generate_component_docs.py`) and tests fail if they are out of date.
- **Editor support.** `tools/generate_yaml_schema.py` writes the YAML schemas; see
  [Editor Support](guide/editor-support.md).
