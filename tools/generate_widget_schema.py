"""Writes `src/tesserae/schema/tesserae-widget-schema.json`: the JSON schema of a 0.5.0 view node, one branch per registered widget.

Run it after changing a widget declaration (`src/tesserae/spec/builtin_widgets.py`); `tests/test_widgets.py` fails while the file is stale.
"""

import json
from pathlib import Path

from tesserae.spec.widgets import json_schema

PATH = Path(__file__).resolve().parent.parent / "src" / "tesserae" / "schema" / "tesserae-widget-schema.json"


def render() -> str:
    return json.dumps(json_schema(), indent=2, sort_keys=False) + "\n"


if __name__ == "__main__":
    PATH.write_text(render(), encoding="utf-8")
    print(f"wrote {PATH}")
