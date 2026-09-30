"""M76: the proof that one `pip install` is enough. Run with the Python of
a fresh venv that has only Tesserae's wheel installed (CI's clean-install
job does this on Linux, macOS and Windows): it makes an app with
`tesserae new`, then runs it headlessly -- builds its views, shows Home,
clicks its button, lays out a few frames -- without a GPU or a display.
Exits non-zero, saying why, if anything is missing or wrong.
"""

from __future__ import annotations

import importlib.metadata
import os
import runpy
import sys
import tempfile
from pathlib import Path


def main() -> int:
    import tesserae
    from tesserae import cli

    engine = importlib.metadata.version("tesserae-engine")
    print(f"tesserae {importlib.metadata.version('tesserae-ui')} on tre {engine}, Python {sys.version.split()[0]}, "
          f"{sys.platform}")
    home = os.getcwd()
    with tempfile.TemporaryDirectory() as parent:
        if cli.main(["new", "hello", "--dir", parent]) != 0:
            return 1
        project = Path(parent) / "hello"
        report: dict[str, object] = {}

        def run(app, max_frames=None, **kwargs):  # headless: no render loop, so no GPU or display needed
            home = app._registered["Home"].view
            app.window.simulate("click", node=home.node("button"))
            for _ in range(3):
                app.window.advance(16)
            report.update(current=app.current, greeting=home.node("greeting").get("text"),
                          count=home.node("count").get("text"))

        tesserae.App.run = run
        sys.path.insert(0, str(project))
        os.chdir(project)
        sys.argv = ["app.py"]
        try:
            runpy.run_path(str(project / "app.py"), run_name="__main__")
        finally:
            os.chdir(home)  # Windows can't remove the folder a process is in
        print("the app reported:", report)
    expected = {"current": "Home", "greeting": "Hello from Hello", "count": "Clicked 1 times"}
    if report != expected:
        print(f"the generated app didn't run as expected: {report} (wanted {expected})", file=sys.stderr)
        return 1
    print("a generated app ran:", report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
