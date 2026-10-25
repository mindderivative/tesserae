"""Runs every generator's `--check` and lists the ones whose output is out of date with the code, then checks the project skills.

    python3 tools/docs_audit.py

Exits 1 if any generated page, schema or the component order differs from what the generator now writes, or if a skill in `.agents/skills/` has
frontmatter that is not valid YAML, lacks a `name` (equal to its folder) or a `description`, or whose parsed description is shorter than the line
written (an unquoted `: ` or ` #` truncates it, and pi then drops or mis-routes the skill). Fast: run it before the strict docs build.
"""

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
PY = str(ROOT / ".venv" / "bin" / "python")
GENERATORS = ["generate_api_docs", "generate_yaml_docs", "generate_component_docs", "generate_component_order", "generate_yaml_schema"]


def check_skills():
    """Return a list of problems with the SKILL.md files; a description is read the way a YAML parser reads it."""
    import yaml

    problems = []
    for path in sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md")):
        where = path.parent.name
        parts = path.read_text(encoding="utf-8").split("---", 2)
        if len(parts) < 3 or parts[0].strip():
            problems.append(f"{where}: no frontmatter between --- lines")
            continue
        try:
            meta = yaml.safe_load(parts[1])
        except yaml.YAMLError as err:
            problems.append(f"{where}: frontmatter is not valid YAML ({str(err).splitlines()[0]})")
            continue
        if not isinstance(meta, dict) or meta.get("name") != where:
            problems.append(f"{where}: `name` is {meta.get('name') if isinstance(meta, dict) else None!r}, expected {where!r}")
        description = meta.get("description") if isinstance(meta, dict) else None
        if not isinstance(description, str) or not description.strip():
            problems.append(f"{where}: no description")
            continue
        line = next((l for l in parts[1].splitlines() if l.startswith("description:")), "")[len("description:"):].strip()
        raw = line[1:-1].replace("''", "'") if line[:1] in "'\"" and line[-1:] == line[:1] and len(line) > 1 else line
        if len(description) < len(raw):
            problems.append(f"{where}: the description is cut short when parsed ({len(description)} of {len(raw)} characters): quote it")
    return problems


def main():
    stale = []
    for name in GENERATORS:
        done = subprocess.run([PY, str(TOOLS / f"{name}.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
        status = "ok" if done.returncode == 0 else "OUT OF DATE"
        print(f"{name}: {status}")
        if done.returncode:
            stale.append(name)
            print("   " + "\n   ".join((done.stdout + done.stderr).strip().splitlines()[-5:]))
    skills = check_skills()
    print("skills: " + ("ok" if not skills else "PROBLEMS"))
    for problem in skills:
        print("   " + problem)
    return int(bool(stale or skills))


if __name__ == "__main__":
    sys.exit(main())
