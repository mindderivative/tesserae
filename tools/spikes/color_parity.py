"""M34 Phase 2 Step 2 spike: materialyoucolor's MD3 schemes against tre's
DynamicTheme, every role tre's ColorScheme.role answers, 8 seeds, light
and dark. Needs materialyoucolor (not a Tesserae dependency yet):

    python tools/spikes/color_parity.py "$(roles)"

where the argument is the comma-separated role list from tre's
crates/engine-md3/src/color.rs. With spec_version="2021", 752 of 784
match; the 32 others (light on_*_container) match at tone 10, which
M38 applies. A prototype, not product code."""
import inspect, re, subprocess, sys
import tre
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors

ROLES = sys.argv[1].split(",")
SEEDS = [(0x67, 0x50, 0xA4), (0xB3, 0x26, 0x1E), (0x00, 0x6A, 0x60), (0xFF, 0xB0, 0x00),
         (0x21, 0x96, 0xF3), (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x7D, 0x52, 0x60)]
print("scheme sig:", inspect.signature(SchemeTonalSpot.__init__))

def mcu_rgba(role, scheme):
    dc = getattr(MaterialDynamicColors, role, None) or getattr(MaterialDynamicColors, re.sub(r"_(\w)", lambda m: m.group(1).upper(), role), None)
    if dc is None:
        return None
    argb = dc.get_argb(scheme)
    return ((argb >> 16) & 255, (argb >> 8) & 255, argb & 255, (argb >> 24) & 255)

total = mismatches = missing = 0
worst = []
for seed in SEEDS:
    for dark in (False, True):
        w = tre.Window(width=10, height=10)
        w.set_theme((*seed, 0xFF), dark=dark)
        argb = 0xFF000000 | (seed[0] << 16) | (seed[1] << 8) | seed[2]
        scheme = SchemeTonalSpot(Hct.from_int(argb), dark, 0.0, spec_version="2021")
        for role in ROLES:
            want = w.theme.role(role)
            got = mcu_rgba(role, scheme)
            total += 1
            if got is None:
                missing += 1
                worst.append((role, "missing in materialyoucolor"))
                continue
            diff = max(abs(a - b) for a, b in zip(want, got))
            if diff:
                mismatches += 1
                worst.append((f"{role} seed={bytes(seed).hex()} dark={dark}", f"tre={want} mcu={got} maxdiff={diff}"))
print(f"{total} role values compared; {mismatches} differ; {missing} missing")
seen = set()
for k, v in worst:
    if (k.split()[0], v.split(" maxdiff")[0][:20]) in seen:
        continue
    seen.add((k.split()[0], v.split(" maxdiff")[0][:20]))
    print(" ", k, v)
    if len(seen) > 25:
        break
