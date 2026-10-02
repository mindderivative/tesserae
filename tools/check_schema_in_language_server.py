#!/usr/bin/env python3
"""Runs Tesserae's YAML schemas through Red Hat's real YAML language server (0.3.2, #79).

`tests/test_yaml_schema.py` checks the schemas with a generic validator. This
drives the server an editor uses, over the Language Server Protocol, the way
VS Code does: it opens every `*_View.yaml`, `*_Shell.yaml`, `*_Component.yaml`
and the default theme in the repository (each must come back with no
diagnostics), then asks for completions and checks that mistakes are flagged.
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
import threading
import time
from pathlib import Path
L = Path(sys.argv[1]); REPO = Path(sys.argv[2]).resolve(); S = REPO / "src/tesserae/schema"
THEMES = sys.argv[3:]
SCHEMAS = {(S / "tesserae-yaml-schema.json").as_uri(): ["**/*_View.yaml"], (S / "tesserae-shell-schema.json").as_uri(): ["**/*_Shell.yaml"],
           (S / "tesserae-component-schema.json").as_uri(): ["**/*_Component.yaml"],
           (S / "tesserae-theme-schema.json").as_uri(): [(REPO / t).as_posix() for t in THEMES] or ["**/__none__.yaml"]}
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

# 1. every repo YAML file, in the real server
bad = []; n = 0
files = [p for p in sorted([*(REPO / "src").rglob("*.yaml"), *(REPO / "examples").rglob("*.yaml")]) if p.name.endswith(("_View.yaml", "_Shell.yaml", "_Component.yaml")) or p.relative_to(REPO).as_posix() in THEMES]
for p in files:
    uri = open_doc(p.relative_to(REPO), p.read_text()); n += 1
    ds = [d["message"][:90] for d in c.diags.get(uri, ["<no response>"])]
    if ds: bad.append((p.relative_to(REPO).as_posix(), ds[:2]))
print(f"every repo YAML in the real server: {n} files, {len(bad)} with diagnostics")
for b in bad[:8]: print("   ", b)

# 2. completions and flagged mistakes, each asserted
problems = [f"{name}: {', '.join(ds)}" for name, ds in bad]


def check(name, condition, shown):
    print(("ok   " if condition else "FAIL ") + name, "->", shown)
    if not condition:
        problems.append(name)


def messages(uri):
    return [d["message"] for d in c.diags.get(uri, [])]


u = open_doc("Scn1_View.yaml", "id: x\nkind: Rect\nhandlers:\n  on_\n"); got = [l for l in labels(u, 3, 5) if l.startswith("on_")]
check("handler keys are suggested", {"on_click", "on_change"} <= set(got), got)
u = open_doc("Scn2_View.yaml", "children:\n  - id: b\n    component: But\n"); got = [l for l in labels(u, 2, 18) if l.startswith("Button")]
check("built-in components are suggested", "ButtonFilled" in got, got[:4])
u = open_doc("Scn3_View.yaml", "id: b\ncomponent: ButtonFilled\nwith:\n  la\n"); got = labels(u, 3, 4)
check("a fragment's parameters are suggested", "label" in got, got)
u = open_doc("Scn4_View.yaml", "id: b\ncomponent: ButtonFilled\nwith:\n  labell: Save\n")
check("a misspelt parameter is flagged", any("labell" in m for m in messages(u)), messages(u))
u = open_doc("Scn5_View.yaml", "id: bar\nkind: TitleBar\nbuttons: [minimize, help]\n")
check("a title bar's wrong button is flagged", any("Valid values" in m for m in messages(u)), messages(u))
u = open_doc("Scn6_Shell.yaml", "top_bar:\n  titel: Studio\nzones:\n  middle: 100\n")
check("a shell's typos are flagged", sum("not allowed" in m for m in messages(u)) == 2, messages(u))
u = open_doc("Scn7_Shell.yaml", "top_bar:\n  tit\n"); got = labels(u, 1, 5)
check("a shell's keys are suggested", "title" in got, got)
u = open_doc("Scn8_View.yaml", "id: root\nkind: \n"); got = labels(u, 1, 6)
check("every kind is suggested for `kind:`", {"Container", "Text", "Rect", "TitleBar"} <= set(got), f"{len(got)} kinds")
u = open_doc("Scn9_View.yaml", "id: root\nkind: Rect\nstyle:\n  fo\n"); got = labels(u, 3, 4)
check("style fields are suggested", "foreground" in got, [x for x in got if x.startswith("fo")])
u = open_doc("Scn10_View.yaml", "id: root\nkind: Rect\nstyle:\n  background: \n"); got = labels(u, 3, 14)
check("theme colour roles are suggested", {"primary", "surface"} <= set(got), f"{len(got)} roles")
u = open_doc("Scn11_View.yaml", "id: root\nkind: Rect\nstyle:\n  foregorund: red\n  flex_direction: diagonal\n")
check("a typo and a wrong value are flagged", len(messages(u)) == 2, messages(u))
c.p.terminate()
if problems:
    sys.exit("FAILED: " + "; ".join(problems))
print("all checks passed")
