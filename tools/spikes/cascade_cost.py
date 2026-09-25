"""M34 Phase 2 Step 1 spike: the cost of Tesserae's own cascade, role
resolution and bindings in Python, on tre 0.3.4's create/set, against
tre's View doing the same work. A prototype, not product code."""
import ast, time, statistics
import tre

N = 2000          # boxes, each with a text child
BOUND = 500       # texts bound to one shared Signal
SEED_A, SEED_B = (0x67, 0x50, 0xA4, 0xFF), (0xB3, 0x26, 0x1E, 0xFF)

SHEET = {"styles": [
    {"style": {"corner_radius": 4}},                                  # baseline
    {"kind": "Rect", "style": {"background": "primary"}},             # kind
    {"classes": ["row"], "style": {"corner_radius": 6}},              # classes
    {"id": "b7", "style": {"background": "tertiary"}},                # id
]}

def spec(label_binding=True):
    kids = []
    for i in range(N):
        t = {"id": f"t{i}", "kind": "Text", "text": {"content": f"row {i}", "font_family": "Roboto", "font_size": 14},
             "style": {"foreground": "on_primary"}}
        if label_binding and i < BOUND:
            t["bindings"] = {"text": "{{ label.get() }}"}
        kids.append({"id": f"b{i}", "kind": "Rect", "classes": ["row"],
                     "style": {"width": 40, "height": 20}, "children": [t]})
    return {"id": "root", "kind": "Container", "children": kids}

# -- tre's reference roles, so both sides paint the same colours ----------
def roles_for(seed):
    w = tre.Window(width=10, height=10); w.set_theme(seed)
    return {r: w.theme.role(r) for r in ("primary", "on_primary", "tertiary")}

# -- the Tesserae prototype --------------------------------------------------
_stack = []
class Signal:
    def __init__(self, v): self._v, self._subs = v, []
    def get(self):
        if _stack: _stack[-1].add(self)
        return self._v
    def set(self, v):
        if v == self._v: return
        self._v = v
        for cb in list(self._subs): cb()

_ALLOWED = (ast.Expression, ast.Attribute, ast.Call, ast.Name, ast.Load, ast.Constant, ast.Subscript,
            ast.BinOp, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.And, ast.Or, ast.Not)
_compiled = {}
def compile_binding(src):
    expr = src.strip()[2:-2].strip()
    if expr not in _compiled:
        tree = ast.parse(expr, mode="eval")
        for n in ast.walk(tree):
            if not isinstance(n, _ALLOWED): raise ValueError(f"not allowed: {type(n).__name__}")
            if isinstance(n, ast.Call) and n.args: raise ValueError("only zero-argument calls")
        _compiled[expr] = compile(tree, "<binding>", "eval")
    return _compiled[expr]

def cascade(node, sheet):
    tiers = [[], [], [], []]
    for rule in sheet["styles"]:
        k, c, i = rule.get("kind"), rule.get("classes") or [], rule.get("id")
        if k and k != node["kind"]: continue
        if c and not set(c) <= set(node.get("classes", [])): continue
        if i and i != node["id"]: continue
        tier = 3 if i else 2 if c else 1 if k else 0
        tiers[tier].append((len(c), rule["style"]))
    out = {}
    for tier in tiers:
        for _, style in sorted(tier, key=lambda x: x[0]):
            out.update(style)
    out.update(node.get("style") or {})
    return out

def color(v, roles):
    if isinstance(v, str) and v.startswith("#"):
        h = v[1:]; return tuple(int(h[j:j+2], 16) for j in (0, 2, 4)) + ((int(h[6:8], 16),) if len(h) == 8 else (255,))
    return roles[v]

def props(node, style, roles):
    p = {}
    for k, v in style.items():
        if k in ("background", "foreground"): p["fill"] = color(v, roles)
        elif k in ("width", "height", "corner_radius"): p[k] = v
    if node["kind"] == "Text":
        p["text"] = node["text"]["content"]; p["font_size"] = node["text"]["font_size"]; p["font_family"] = node["text"]["font_family"]
    return p

KIND = {"Rect": "box", "Container": "box", "Text": "text"}

class Built:
    def __init__(self, window, spec, sheet, roles, vm):
        self.nodes, self.styles = {}, {}
        self.window, self.sheet, self.vm = window, sheet, vm
        self.root = self._build(spec, roles)
    def _build(self, node, roles):
        style = cascade(node, self.sheet); self.styles[node["id"]] = (node, style)
        n = self.window.create(KIND[node["kind"]], **props(node, style, roles))
        self.nodes[node["id"]] = n
        for prop, src in (node.get("bindings") or {}).items():
            self._bind(n, prop, compile_binding(src))
        for c in node.get("children") or []:
            n.add_child(self._build(c, roles))
        return n
    def _bind(self, n, prop, code):
        env = {k: getattr(self.vm, k) for k in ("label",)}
        last = [object()]
        def run():
            _stack.append(set())
            try: value = eval(code, {"__builtins__": {}}, env)
            finally: deps = _stack.pop()
            for d in deps:
                if run not in d._subs: d._subs.append(run)
            if value != last[0]:
                last[0] = value; n.set(**{prop: value})
        run()
    def retheme(self, roles):
        for nid, (node, style) in self.styles.items():
            p = {k: v for k, v in props(node, style, roles).items() if k == "fill"}
            if p: self.nodes[nid].set(**p)

def timeit(fn, reps=5):
    out = []
    for _ in range(reps):
        t = time.perf_counter(); r = fn(); out.append(time.perf_counter() - t)
    return statistics.median(out) * 1000, r

A, B = roles_for(SEED_A), roles_for(SEED_B)
s = spec()

class VM: pass
def build_tesserae():
    vm = VM(); vm.label = Signal("bound")
    w = tre.Window(width=800, height=600)
    b = Built(w, s, SHEET, A, vm); w.root.add_child(b.root)
    return b, vm

def build_tre():
    v = tre.View(spec=s, stylesheet_spec=SHEET, theme_seed=SEED_A)
    class TVM(tre.ViewModel):
        def __init__(self, view):
            self.label = tre.Signal("bound"); super().__init__(view)
    return v, TVM(v)

t_build, (b, vm) = timeit(build_tesserae)
r_build, (v, tvm) = timeit(build_tre)
t_theme, _ = timeit(lambda: b.retheme(B))
r_theme, _ = timeit(lambda: v.set_theme(theme_seed=SEED_B))
vals = iter(range(10**6))
t_bound, _ = timeit(lambda: vm.label.set(f"v{next(vals)}"))
r_bound, _ = timeit(lambda: tvm.label.set(f"v{next(vals)}"))

# correctness checks: same result on both sides
assert b.nodes["t3"].get("text") == vm.label.get() and v.node("t3").get_text() == tvm.label.get()
assert b.nodes["b7"].get("fill") == B["tertiary"] and b.nodes["b8"].get("fill") == B["primary"]
assert b.nodes["b8"].get("corner_radius") == v.node("b8").get("corner_radius") == 6.0

print(f"{N} boxes + {N} texts, 4-rule stylesheet, {BOUND} texts bound to one Signal (median of 5)")
print(f"{'':28}{'Tesserae prototype':>20}{'tre View':>12}")
print(f"{'build (incl. cascade, bind)':28}{t_build:>17.1f} ms{r_build:>9.1f} ms")
print(f"{'theme switch':28}{t_theme:>17.1f} ms{r_theme:>9.1f} ms")
print(f"{'one Signal.set -> 500 nodes':28}{t_bound:>17.1f} ms{r_bound:>9.1f} ms")
