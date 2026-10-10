# Developing Tesserae

Everything needed to go from a clean OS install to a working checkout. (The standing rules for the AI assistant are in `CLAUDE.md`; this file is
for a person or a fresh session.)

## 1. The machine

Tesserae is pure Python on top of `tre` (the `tesserae-engine` package, imported as `tre`), which is Rust built with `maturin`. The checkout was developed on
Fedora/Nobara with KDE Plasma on Wayland; CI also runs Windows and macOS.

```bash
# Fedora / Nobara
sudo dnf install git python3 python3-devel gh gcc pkgconf-pkg-config fontconfig-devel
# Debian / Ubuntu: sudo apt install git python3 python3-venv python3-dev gh build-essential pkg-config libfontconfig1-dev
```

Python 3.12 or newer (the developer's was 3.14). `gh auth login` once, with the `project` scope (`gh auth refresh -s project`), to use the board.

## 2. The checkout and the venv

```bash
git clone https://github.com/mindderivative/tesserae.git && cd tesserae
git checkout 0.5.0            # the release line being built; main is the last release
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pip install mkdocs mkdocs-material   # the docs build; also pillow-based tools need no extra
```

`pip install -e ".[dev]"` pulls `tesserae-engine>=0.5.6,<0.6`. **Until tre publishes 0.5.6 to PyPI that requirement cannot be met**; PyPI has 0.5.5. Until then
build the wheel from tre's `0.5.6` branch and install it into the venv (it must be this branch: the late windows, timers, layout animation, extra
accessibility states, text-input props and masks 0.5.0 uses are all in it):

```bash
git clone https://github.com/mindderivative/tre.git && cd tre && git checkout 0.5.6   # if the branch is not on GitHub yet, ask tre's maintainer for the wheel
pip install maturin
maturin build --release -m crates/engine-py/Cargo.toml     # a wheel in target/wheels/
cd ../tesserae && .venv/bin/pip install --force-reinstall --no-deps ../tre/target/wheels/tesserae_engine-0.5.6-*.whl
```

Never put a scratch tre build into `.venv` by accident; to try another tre version make a throwaway venv (`python3 -m venv /tmp/v055`, install the wheel and
`pip install -e . --no-deps` plus the dependencies).

## 3. Checking your work

```bash
tools/fullcheck.sh                                  # the whole suite, then `mkdocs build --strict` (about 3 minutes)
.venv/bin/python -m pytest tests/test_toolbar.py -q   # one file
```

A commit needs `fullcheck.sh` to pass. Tests run against a headless window: **it draws no shaders and no backdrop blur**, so those are tested by their
values only and need a look in a real window (`.venv/bin/python -m tesserae ...` or an example in `examples/`). A real display is also needed for
`tools/window_perf.py` and anything that opens a second OS window while running.

Some tests read tre's source: `TRE_SOURCE_DIR=<path to the tre checkout>` lets the one real-font test run.

### Generated files (the tests compare them)

After changing a view, a widget declaration, a component page entry or the expression language, regenerate and commit the results:

```bash
for g in generate_component_docs generate_yaml_docs generate_api_docs generate_yaml_schema generate_widget_schema; do
  .venv/bin/python tools/$g.py
done
```

`tools/component_docs.yaml` is the source of `docs/components/*.md`; do not edit those pages by hand.

### Mutation checks

How a new test is shown to test something: break the code it covers (change a value, drop a branch) in a scripted edit that **asserts the text occurs exactly
once**, run the test file with an isolated bytecode cache (`PYTHONPYCACHEPREFIX=$(mktemp -d)`), see it fail, restore the file.

## 4. How the project is laid out

- `src/tesserae/views/` — the shipped views: `<Name>_View.yaml` (structure, params) and `<Name>_Stylesheet.yaml` (looks, by widget/variant/size/part/state).
- `src/tesserae/spec/` — the view language: `nodes.py` (parser), `compose.py` (composition, route records), `lower.py` (to the builder's spec), `build.py`, `effects.py`, `transition.py`.
- `src/tesserae/composed.py` — the live view: wires handlers, overlays, timers, focus groups, frames, measures. `app.py` — the app; `appwindows.py` — more windows.
- `design/yaml-language.md` — the language, and a log of why each component needed what it did. `design/component-order.md` — the build order of the 0.5.0 components.
- `docs/` — the MkDocs site; `docs/changelog.md` and `CHANGELOG.md`; `LOG.md` and `PLAN.md` — the project log and plan.
- Spec-generated node keys (`spin`, `dial`, `graph`, `tooltip`) must be added in three places: `build._NODE_KEYS`, `view._props_equal` and the exclusion set in `tools/generate_yaml_schema.py`.

## 5. Working rules (from `CLAUDE.md`)

- **Commit locally** as soon as a milestone, step or feature is finished and `fullcheck.sh` passes. Message style: `0.5.0 #<issues>: <what>`. **Never push, merge to `main`, tag or release without being told to.**
- Update the docs (the changelog, `design/yaml-language.md`, the component page, a `mkdocs build --strict`) with each finished piece.
- The board is the GitHub project "Tesserae UI Framework" (owner `mindderivative`, number 2): Backlog → Ready → In progress → In review → **Done only when the maintainer says so**. Move items with `python3 tools/board.py 124=review 125=done`; comment on the issue with what was built, how it was tested, and what was not built or not checked.
- Report outcomes as they are: say what was not run or not seen.

## 6. A release (each step waits for the maintainer's word)

1. Release commit "Tesserae X" (version in `pyproject.toml`, the changelog heading), push the branch, fast-forward `main`, push it, wait for CI on that commit (Linux, Windows, macOS; two runs plus Deploy Docs).
2. `gh release create vX --target <sha> --prerelease --title "Tesserae X" --notes-file <changelog section>`.
3. The Release workflow stops at the `pypi` environment: the maintainer approves it.
4. Check PyPI (`https://pypi.org/pypi/tesserae-ui/json`; the index lags a few minutes), install `tesserae-ui==X` in a scratch venv with a smoke test, add a `LOG.md` entry.
5. Push the log, promote the release (`gh release edit vX --prerelease=false --latest`), move the issues to Done.

CI gotchas: a leading-slash path is not absolute on Windows; the macOS runner asks for reduced motion, so a test must not assume the OS state.

## 7. Display notes (KDE Plasma, Wayland)

Real windows can be opened from a shell; the person at the machine drives them. Wayland lets an app neither place nor centre a window and ignores `always_on_top`, so
window position code is a no-op there. Resizing a window on tre 0.5.4 stalls frames; 0.5.5 and later do not.
