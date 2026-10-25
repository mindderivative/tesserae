#!/usr/bin/env python3
"""A mypy ratchet: the code has hundreds of old type errors, so mypy cannot gate a commit, but a new one can.

    python3 tools/mypy_ratchet.py            # fail (exit 1) on an error the baseline does not have
    python3 tools/mypy_ratchet.py --update   # rewrite the baseline to the current errors (after fixing some, never to hide a new one)
    python3 tools/mypy_ratchet.py --list     # print the current errors, one per line

`tools/mypy_baseline.json` counts the errors of `mypy src/tesserae` by file, error code and message, not by line number, so editing a
file does not move an old error into "new". A key whose count went up, or a key that is not in the baseline, is new and is printed with
its current lines. Fewer errors than the baseline is reported as progress: run `--update` to keep it.
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = Path(__file__).resolve().parent / "mypy_baseline.json"
LINE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+): error: (?P<message>.*?)(?:  \[(?P<code>[a-z-]+)\])?$")


def current():
    """Return ({key: count}, {key: [lines]}) from a fresh mypy run; the key is `file|code|message`."""
    exe = ROOT / ".venv" / "bin" / "mypy"
    done = subprocess.run([str(exe) if exe.exists() else "mypy", "src/tesserae", "--no-error-summary", "--no-pretty"], cwd=ROOT,
                          capture_output=True, text=True)
    counts, where = Counter(), {}
    for text in done.stdout.splitlines():
        m = LINE.match(text)
        if m:
            key = f"{m['file']}|{m['code'] or '-'}|{m['message']}"
            counts[key] += 1
            where.setdefault(key, []).append(m["line"])
        elif "error:" in text:
            print(f"mypy: could not parse: {text}", file=sys.stderr)
    if done.returncode not in (0, 1):
        sys.exit(f"mypy did not run: {done.stderr.strip() or done.stdout.strip()}"[:300])
    return counts, where


def main(argv):
    counts, where = current()
    if "--list" in argv:
        for key in sorted(counts):
            file, code, message = key.split("|", 2)
            print(f"{file}:{','.join(where[key])}: [{code}] {message}  x{counts[key]}")
        return 0
    if "--update" in argv:
        BASELINE.write_text(json.dumps(dict(sorted(counts.items())), indent=0) + "\n", encoding="utf-8")
        print(f"baseline written: {sum(counts.values())} errors in {len({k.split('|')[0] for k in counts})} files")
        return 0
    if not BASELINE.exists():
        sys.exit("no baseline: run `python3 tools/mypy_ratchet.py --update` once")
    old = Counter(json.loads(BASELINE.read_text(encoding="utf-8")))
    new = {k: counts[k] - old.get(k, 0) for k in counts if counts[k] > old.get(k, 0)}
    fixed = sum(max(0, old[k] - counts.get(k, 0)) for k in old)
    if new:
        print(f"{sum(new.values())} new mypy error(s) (baseline {sum(old.values())}, now {sum(counts.values())}):")
        for key, extra in sorted(new.items()):
            file, code, message = key.split("|", 2)
            print(f"  {file}: lines {','.join(where[key])} [{code}] {message}" + (f"  (+{extra})" if old.get(key) else ""))
        return 1
    note = f"; {fixed} fewer than the baseline: run --update to keep the progress" if fixed else ""
    print(f"ok: no new mypy errors ({sum(counts.values())} old ones remain){note}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
