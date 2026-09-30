"""M76: Tesserae's own file reads and writes say UTF-8. Windows defaults to
its code page, so a `read_text()` with no encoding garbles or fails on any
non-ASCII YAML there (the suite runs with PYTHONUTF8=1 on CI, which would
hide it, so this checks the source itself)."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src" / "tesserae"
TEXT_CALLS = {"read_text", "write_text"}


def _offenders():
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            named = {k.arg for k in node.keywords}
            if isinstance(func, ast.Attribute) and func.attr in TEXT_CALLS and "encoding" not in named:
                yield f"{path.relative_to(SRC)}:{node.lineno}: .{func.attr}() without encoding="
            if isinstance(func, ast.Name) and func.id == "open" and "encoding" not in named:
                mode = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else "r"
                if "b" not in str(mode):
                    yield f"{path.relative_to(SRC)}:{node.lineno}: open() in text mode without encoding="


def test_every_text_read_and_write_names_its_encoding():
    assert list(_offenders()) == []
