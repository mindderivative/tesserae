"""M34 Phase 2 Step 3 spike: an MD3 checkbox built only from tre 0.3.4's
building blocks, driven headlessly with simulate/advance. A prototype."""
import tre

SEED = (0x67, 0x50, 0xA4, 0xFF)
ref = tre.Window(width=10, height=10); ref.set_theme(SEED)
ROLE = {r: ref.theme.role(r) for r in ("primary", "on_primary", "on_surface", "on_surface_variant")}
EMPHASIZED = (0.2, 0.0, 0.0, 1.0)          # MD3 standard easing
HOVER, FOCUS, PRESS = 0.08, 0.10, 0.10     # MD3 state-layer opacities

def alpha(color, a):
    return color[:3] + (round(255 * a),)

class Checkbox:
    def __init__(self, window, label, checked=False):
        self.window, self.checked = window, checked
        self._hover = self._focus = False
        # the 40x40 touch target: what assistive tech and focus see
        self.node = window.create("box", width=40, height=40, align_items="center", justify_content="center",
                                  focusable=True, role="checkbox", label=label, checked=checked, cursor="pointer")
        # state layer: a circle behind the box, invisible until hovered/focused/pressed
        self.layer = window.create("box", position="absolute", x=0, y=0, width=40, height=40, corner_radius=20,
                                   fill=alpha(ROLE["on_surface"], 0), clip_children=True,
                                   a11y_hidden=True, hit_testable=False, z_index=0)
        # the ripple: a circle grown from the press point, clipped by the layer
        self.ripple = window.create("box", position="absolute", width=80, height=80, corner_radius=40,
                                    fill=alpha(ROLE["on_surface"], PRESS), scale=0.0, opacity=0.0,
                                    a11y_hidden=True, hit_testable=False)
        self.layer.add_child(self.ripple)
        # the 18x18 box and its check mark
        self.box = window.create("box", width=18, height=18, corner_radius=2, stroke_width=2, z_index=1,
                                 hit_testable=False, align_items="center", justify_content="center")
        self.check = window.create("path", data="M3.5,9.5 L7,13 L14.5,5.5", view_box=(0, 0, 18, 18),
                                   width=18, height=18, stroke_color=ROLE["on_primary"], stroke_width=2,
                                   fill=(0, 0, 0, 0), hit_testable=False)
        self.box.add_child(self.check)
        for child in (self.layer, self.box):
            self.node.add_child(child)
        self.node.on("click", lambda e: self.toggle())
        self.node.on("pointer_enter", lambda e: self._state(hover=True))
        self.node.on("pointer_leave", lambda e: self._state(hover=False))
        self.node.on("focus", lambda e: self._state(focus=bool(e.focus_visible)))
        self.node.on("unfocus", lambda e: self._state(focus=False))
        self.node.on("pointer_down", self._press)
        self._paint(animate=False)

    def toggle(self):
        self.checked = not self.checked
        self.node.set(checked=self.checked)
        self._paint(animate=True)

    def _paint(self, animate):
        ms = 150 if animate else 0
        if self.checked:
            self.box.set(fill=ROLE["primary"], stroke_color=ROLE["primary"])
            self.check.animate("trim_end", 1.0, ms, easing=EMPHASIZED)
        else:
            self.box.set(fill=(0, 0, 0, 0), stroke_color=ROLE["on_surface_variant"])
            self.check.animate("trim_end", 0.0, ms // 2, easing=EMPHASIZED)

    def _state(self, hover=None, focus=None):
        if hover is not None: self._hover = hover
        if focus is not None: self._focus = focus
        a = FOCUS if self._focus else HOVER if self._hover else 0.0
        self.layer.animate("fill", alpha(ROLE["on_surface"], a), 90)

    def _press(self, e):
        self.ripple.set(x=e.x - 40, y=e.y - 40, scale=0.0, opacity=1.0)
        self.ripple.animate("scale", 1.0, 225, easing=EMPHASIZED)
        self.ripple.animate("opacity", 0.0, 375, on_complete=lambda: None)

w = tre.Window(width=200, height=100)
before = w.create("box", width=40, height=40, focusable=True, role="button", label="Back")
cb = Checkbox(w, "Accept terms")
w.root.set(flex_direction="horizontal")
w.root.add_child(before)
w.root.add_child(cb.node)
w.advance(16)
results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

check("a11y: role and label", cb.node.get("role") == "checkbox" and cb.node.get("label") == "Accept terms")
check("starts unchecked, check mark hidden", cb.node.get("checked") is False and cb.check.get("trim_end") == 0.0)
w.simulate("pointer_enter", node=cb.node); w.advance(200)
check("hover: state layer at 8%", cb.layer.get("fill")[3] == round(255 * HOVER), cb.layer.get("fill"))
w.simulate("pointer_down", node=cb.node, x=10, y=12); w.advance(100)
mid_scale = cb.ripple.get("scale")
check("press: ripple grows from the press point", 0.0 < mid_scale < 1.0 and cb.ripple.get("x") == -30, (mid_scale, cb.ripple.get("x")))
w.simulate("pointer_up", node=cb.node, x=10, y=12)  # press + release on the node = a click
w.advance(75)
mid = cb.check.get("trim_end")
check("click: checked, a11y state follows", cb.checked and cb.node.get("checked") is True)
check("check mark draws in (mid-animation)", 0.0 < mid < 1.0, mid)
w.advance(400)
check("check mark fully drawn", cb.check.get("trim_end") == 1.0)
check("box filled with primary", cb.box.get("fill") == ROLE["primary"], cb.box.get("fill"))
check("ripple faded out", cb.ripple.get("opacity") == 0.0)
w.simulate("pointer_leave", node=cb.node); w.advance(200)
check("leave: state layer cleared (pointer focus shows no ring)", cb.layer.get("fill")[3] == 0, cb.layer.get("fill"))
before.focus(); w.advance(200)
w.simulate("key_down", key="tab"); w.advance(200)
check("Tab focuses it, focus ring (state layer) at 10%", cb.node.get("focused") is True and cb.layer.get("fill")[3] == round(255 * FOCUS), cb.layer.get("fill"))
w.simulate("key_down", key="space"); w.simulate("key_up", key="space"); w.advance(400)
check("Space toggles it off (keyboard activation)", cb.checked is False and cb.check.get("trim_end") == 0.0 and cb.node.get("checked") is False)
for name, ok, detail in results:
    print(("PASS " if ok else "FAIL ") + name + (f"   [{detail}]" if not ok and detail != "" else ""))
print(f"{sum(ok for _, ok, _ in results)}/{len(results)} checks passed")
