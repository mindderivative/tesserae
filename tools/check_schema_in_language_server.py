#!/usr/bin/env python3
"""Runs Tesserae's YAML schemas through Red Hat's real YAML language server (0.3.2, #79; the current language since #275).

`tests/test_yaml_schema.py` and `tests/test_widget_schema.py` check the schemas with a generic validator. This
drives the server an editor uses, over the Language Server Protocol, the way VS Code does: it opens every view of the current language and every
stylesheet of rules in the repository (each must come back with no diagnostics: the example projects against the schema `tesserae schema --project`
writes for them), then asks for completions and checks that mistakes are flagged.
It needs node and the server, so CI doesn't run it; run it after regenerating
the schemas (`tools/generate_yaml_schema.py`) or changing a file format.

    mkdir /tmp/yls && cd /tmp/yls && npm init -y && npm install --ignore-scripts yaml-language-server
    python tools/check_schema_in_language_server.py /tmp/yls . src/tesserae/spec/default_theme.yaml

Arguments: the folder holding `node_modules/.bin/yaml-language-server`, the
repository root, and the theme files to map to the theme schema.
"""

import json
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

L = Path(sys.argv[1]); REPO = Path(sys.argv[2]).resolve(); S = REPO / "src/tesserae/schema"
THEMES = sys.argv[3:]
sys.path.insert(0, str(REPO / "src"))
from tesserae import cli  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="tesserae-schemas."))
# One schema per file: the server applies every schema whose glob matches, so the packaged one is mapped only to the views Tesserae ships and to the scratch
# files below, and each example project has its own.
SCHEMAS = {(S / "tesserae-widget-schema.json").as_uri(): [(REPO / "src/tesserae/views").as_posix() + "/*_View.yaml", "**/Scn*_View.yaml"],
           (S / "tesserae-stylesheet-schema.json").as_uri(): [(REPO / "src/tesserae/views").as_posix() + "/*_Stylesheet.yaml", "**/Scn*_Stylesheet.yaml"],
           (S / "tesserae-theme-schema.json").as_uri(): [(REPO / t).as_posix() for t in THEMES] or ["**/__none__.yaml"]}
EXAMPLES = sorted(p.parent for p in (REPO / "examples").rglob("app.py"))
for number, example in enumerate(EXAMPLES):  # each example project has its own views, so its own widget schema
    schema = TMP / f"example{number}.json"
    schema.write_text(json.dumps(cli.project_schema_data(example)), encoding="utf-8")
    SCHEMAS[schema.as_uri()] = [example.as_posix() + "/**/*_View.yaml"]
    SCHEMAS[(S / "tesserae-stylesheet-schema.json").as_uri()].append(example.as_posix() + "/**/*_Stylesheet.yaml")
YAML_SETTINGS = {"schemas": SCHEMAS, "validate": True, "completion": True, "hover": True, "schemaStore": {"enable": False}}
class Client:
    def __init__(self):
        self.p = subprocess.Popen([str(L / "node_modules/.bin/yaml-language-server"), "--stdio"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.id = 0; self.responses = {}; self.diags = {}
        threading.Thread(target=self._read, daemon=True).start()
    def _read(self):
        f = self.p.stdout
        while True:
            h = {}
            while True:
                line = f.readline()
                if not line: return
                line = line.strip()
                if not line: break
                k, v = line.decode().split(":", 1); h[k.lower()] = v.strip()
            b = json.loads(f.read(int(h["content-length"])))
            if "id" in b and "method" not in b: self.responses[b["id"]] = b
            elif b.get("method") == "textDocument/publishDiagnostics": self.diags[b["params"]["uri"]] = b["params"]["diagnostics"]
            elif "id" in b and "method" in b:
                self.send({"jsonrpc": "2.0", "id": b["id"], "result": [YAML_SETTINGS if i.get("section") == "yaml" else {} for i in b.get("params", {}).get("items", [])]})
    def send(self, m):
        d = json.dumps(m).encode(); self.p.stdin.write(b"Content-Length: %d\r\n\r\n" % len(d) + d); self.p.stdin.flush()
    def request(self, method, params, timeout=20):
        self.id += 1; i = self.id; self.send({"jsonrpc": "2.0", "id": i, "method": method, "params": params}); t = time.time()
        while i not in self.responses:
            if time.time() - t > timeout: return {"error": "timeout"}
            time.sleep(0.02)
        return self.responses[i]
    def notify(self, m, p): self.send({"jsonrpc": "2.0", "method": m, "params": p})
c = Client()
c.request("initialize", {"processId": None, "rootUri": REPO.as_uri(), "capabilities": {"textDocument": {"hover": {"contentFormat": ["markdown"]}}}})
c.notify("initialized", {}); c.notify("workspace/didChangeConfiguration", {"settings": {"yaml": YAML_SETTINGS}}); time.sleep(1)
def open_doc(path_or_name, text, root=REPO):
    uri = (root / path_or_name).as_uri(); c.diags.pop(uri, None)
    c.notify("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "yaml", "version": 1, "text": text}})
    t = time.time()
    while uri not in c.diags and time.time() - t < 15: time.sleep(0.03)
    time.sleep(0.15); return uri
def labels(uri, line, col):
    r = c.request("textDocument/completion", {"textDocument": {"uri": uri}, "position": {"line": line, "character": col}}).get("result") or []
    return [i["label"] for i in (r.get("items", []) if isinstance(r, dict) else r)]

# 1. every view of the current language and every stylesheet of rules, in the real server
import yaml  # noqa: E402

bad = []; n = 0
files = []
for p in sorted([*(REPO / "src").rglob("*.yaml"), *(REPO / "examples").rglob("*.yaml")]):
    data = yaml.safe_load(p.read_text())
    if p.name.endswith("_View.yaml") and isinstance(data, dict) and "widget" in data:
        files.append(p)
    elif p.name.endswith("_Stylesheet.yaml") and isinstance(data, dict) and any(isinstance(r, dict) and "widget" in r for r in data.get("styles") or []):
        files.append(p)
    elif p.relative_to(REPO).as_posix() in THEMES:
        files.append(p)
for p in files:
    uri = open_doc(p.relative_to(REPO), p.read_text()); n += 1
    ds = [d["message"][:90] for d in c.diags.get(uri, ["<no response>"])]
    if ds: bad.append((p.relative_to(REPO).as_posix(), ds[:2]))
print(f"every current-language YAML in the real server: {n} files, {len(bad)} with diagnostics")
for b in bad[:8]: print("   ", b)

# 2. completions and flagged mistakes, each asserted
problems = [f"{name}: {', '.join(ds)}" for name, ds in bad]


def check(name, condition, shown):
    print(("ok   " if condition else "FAIL ") + name, "->", shown)
    if not condition:
        problems.append(name)


def messages(uri):
    return [d["message"] for d in c.diags.get(uri, [])]


u = open_doc("Scn1_View.yaml", "widget: Contai\n"); got = [l for l in labels(u, 0, 14) if l.startswith("Contai")]
check("widget names are suggested", "Container" in got, got)
u = open_doc("Scn2_View.yaml", "widget: Container\nchildren:\n  - widget: Bu\n"); got = [l for l in labels(u, 2, 15) if l.startswith("Bu")]
check("the views Tesserae ships are suggested as widgets", "Button" in got, got)
u = open_doc("Scn3_View.yaml", "widget: Button\nla\n"); got = labels(u, 1, 2)
check("a shipped view's params are suggested", "label" in got and "variant" in got, [x for x in got if x in ("label", "variant")])
u = open_doc("Scn4_View.yaml", "widget: Button\nlabell: Save\n")
check("a misspelt param of a shipped view is flagged", bool(messages(u)), messages(u))
u = open_doc("Scn5_View.yaml", "widget: Button\nvariant: gigantic\n")
check("a wrong choice is flagged", bool(messages(u)), messages(u))
u = open_doc("Scn6_View.yaml", "widget: Window\ntitel: Studio\n")
check("a window's typo is flagged", bool(messages(u)), messages(u))
u = open_doc("Scn7_View.yaml", "widget: Window\nbor\n"); got = labels(u, 1, 3)
check("a window's keys are suggested", "borderless" in got, got[:6])
u = open_doc("Scn8_View.yaml", "widget: Container\nstyle:\n  fo\n"); got = labels(u, 2, 4)
check("style fields are suggested", "flex_direction" in got, [x for x in got if x.startswith("f")][:5])
u = open_doc("Scn9_View.yaml", "widget: Container\nstyle:\n  background: \n"); got = labels(u, 2, 14)
check("theme colour roles are suggested", {"primary", "surface"} <= set(got), f"{len(got)} roles")
u = open_doc("Scn10_View.yaml", "widget: Container\nstyle:\n  foregorund: red\n  flex_direction: diagonal\n")
check("a typo and a wrong value are flagged", len(messages(u)) >= 2, messages(u))
u = open_doc("Scn11_View.yaml", "widget: Container\nstyle:\n  width: \"{{ w / 2 }}\"\n  height: 50%\n")
check("an expression and a percentage are accepted", not messages(u), messages(u))
u = open_doc("Scn12_Stylesheet.yaml", "styles:\n  - widget: Button\n    state: hoverd\n    style: {width: 1}\n")
check("a rule's wrong state is flagged", bool(messages(u)), messages(u))
u = open_doc("Scn13_Stylesheet.yaml", "styles:\n  - widget: Button\n    sta\n"); got = labels(u, 2, 7)
check("a rule's keys are suggested", "state" in got and "variant" in got, got)
u = open_doc("Scn14_Stylesheet.yaml", "styles:\n  - widget: Button\n    state: hovered\n    style:\n      corner_radius: 8\n")
check("a good rule is accepted", not messages(u), messages(u))
# 3. the sizes, insets and anchor fields of 0.5.0.24-28: good values pass, each bad one is flagged, the new fields and their choices are offered
u = open_doc("Scn15_View.yaml", "widget: Container\nstyle:\n  position: absolute\n  left: 8\n  right: 10%\n  bottom: -4\n  top: auto\n  inset: 2\n"
             "  width: \"calc(100% - 16)\"\n  height: fit-content\n  min_width: 50%\n")
check("insets, sums and fit-content are accepted", not messages(u), messages(u))
for n, (what, style) in enumerate([("40px", "width: 40px"), ("a negative size", "width: -3"), ("a sum in an inset", "right: \"calc(100% - 4)\""), ("a sum in a limit", "min_width: \"calc(100% - 4)\""),
                                    ("a negative percentage inset", "inset: -5%"), ("a sum without spaces", "width: \"100%-16\"")]):
    u = open_doc(f"Scn{16 + n}_View.yaml", f"widget: Container\nstyle:\n  {style}\n")
    check(f"a size or inset tre refuses is flagged: {what}", bool(messages(u)), messages(u)[:1])
u = open_doc("Scn22_View.yaml", "widget: Rect\nstyle:\n  anchor: target\n  placement: top_end\n  offset: [4, -4]\n")
check("anchor, placement and offset are accepted", not messages(u), messages(u))
for n, (what, style) in enumerate([("an empty anchor", "anchor: ''"), ("a placement tre refuses", "placement: above_end"), ("a short offset", "offset: [1]"), ("a scalar offset", "offset: 3")]):
    u = open_doc(f"Scn{23 + n}_View.yaml", f"widget: Rect\nstyle:\n  {style}\n")
    check(f"a mistake in the anchor fields is flagged: {what}", bool(messages(u)), messages(u)[:1])
u = open_doc("Scn27_View.yaml", "widget: Rect\nstyle:\n  anc\n"); got = labels(u, 2, 5)
check("the anchor style fields are suggested", {"anchor"} <= set(got), [x for x in got if x.startswith("anc")])
u = open_doc("Scn28_View.yaml", "widget: Rect\nstyle:\n  placement: \n"); got = labels(u, 2, 13)
check("the placements are suggested", {"below", "top_end", "center"} <= set(got), got[:10])
u = open_doc("Scn29_View.yaml", "widget: Overlay\nanchor: t\nplacement: bottom_start\noffset: [0, 8]\nflip: false\n")
check("an overlay's corner placement, offset and flip are accepted", not messages(u), messages(u))
u = open_doc("Scn30_View.yaml", "widget: Overlay\nanchor: t\nplacement: diagonal\nflip: maybe\n")
check("an overlay's wrong placement and flip are flagged", len(messages(u)) >= 2, messages(u)[:2])
c.p.terminate()
if problems:
    sys.exit("FAILED: " + "; ".join(problems))
print("all checks passed")
