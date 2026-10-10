"""Moves issues on the "Tesserae UI Framework" GitHub project (owner mindderivative, project 2).

    python3 tools/board.py 124=review 125=review 204=done

States: backlog, ready, progress, review, done. Needs the `gh` CLI, logged in with the `project` scope. Item ids are cached in
the system temp directory; a number not in the cache refreshes it from the project.
"""

import json
import os
import subprocess
import sys
import tempfile

OPTIONS = {"backlog": "f75ad846", "ready": "e18bf179", "progress": "47fc9ee4", "review": "aba860b9", "done": "98236657"}
PROJECT_ID = "PVT_kwHOAH-9nM4BlPO7"
STATUS_FIELD = "PVTSSF_lAHOAH-9nM4BlPO7zhj83AU"
CACHE = os.path.join(tempfile.gettempdir(), "tesserae_board_items.json")


def item_ids(wanted):
    ids = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    if any(str(n) not in ids for n in wanted):
        items = json.loads(subprocess.check_output(["gh", "project", "item-list", "2", "--owner", "mindderivative", "--limit", "400",
                                                    "--format", "json"]))["items"]
        ids = {str(i["content"]["number"]): i["id"] for i in items if i.get("content", {}).get("number")}
        json.dump(ids, open(CACHE, "w", encoding="utf-8"))
    return ids


def main(args):
    moves = [a.split("=") for a in args]
    ids = item_ids([int(n) for n, _ in moves])
    for number, state in moves:
        subprocess.run(["gh", "project", "item-edit", "--id", ids[number], "--project-id", PROJECT_ID, "--field-id", STATUS_FIELD,
                        "--single-select-option-id", OPTIONS[state]], check=True, capture_output=True)
        print(number, state)


if __name__ == "__main__":
    main(sys.argv[1:])
