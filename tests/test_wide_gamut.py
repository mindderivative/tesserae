"""M63 (#16): CSS Color 4's wide-gamut functions parse as `tre` 0.3.4
parsed them (the `color` crate, 0.3.3), byte for byte. A seeded corpus
reaches every branch: each `color()` space's transfer, near zero (the
linear segments) and far out of gamut (clipped), `lab`'s linear toe,
`hwb`'s grey when whiteness and blackness pass 100%, `none`, angle
units, percentages and alpha. `tre`'s answers are recorded once
(`tests/reference.py`), as the other parity data is.
"""

import random

import pytest
import tre

from tesserae import tokens

import reference

SPACES = ["srgb", "srgb-linear", "display-p3", "a98-rgb", "prophoto-rgb", "rec2020", "xyz", "xyz-d50", "xyz-d65"]


def _corpus(seed: int = 63) -> list[str]:
    """Deterministic: the recorded answers are keyed by these strings. Forty
    per `color()` space, mostly in gamut (where a small error shows), some
    near zero (each transfer's linear segment) and some out of range."""
    rnd = random.Random(seed)

    def num(lo, hi, near=0.15, none=0.06):
        pick = rnd.random()
        if pick < none:
            return "none"
        value = rnd.uniform(-0.1, 0.1) if pick < none + near else rnd.uniform(lo, hi)
        return f"{value:.5g}"

    def channel():
        pick = rnd.random()
        return num(-0.4, 1.4, near=0, none=0) if pick < 0.1 else num(0, 1, near=0.2, none=0.05)

    def pct(lo, hi):
        text = num(lo, hi)
        return text + "%" if text != "none" and rnd.random() < 0.25 else text

    def angle():
        text = num(-720, 720, near=0)
        return text + rnd.choice(["deg", "rad", "grad", "turn"]) if text != "none" and rnd.random() < 0.3 else text

    def alpha():
        text = rnd.choice(["", "", f" / {num(-0.2, 1.2)}", f" / {num(-10, 110)}%", " / none"])
        return text.replace("none%", "none")

    corpus = [f"color({space} {channel()} {channel()} {channel()}{alpha()})" for space in SPACES for _ in range(40)]
    for kind in ("lab", "oklab", "lch", "oklch", "hwb"):
        for _ in range(60):
            if kind in ("lab", "oklab"):
                top, c = (100, 160) if kind == "lab" else (1, 0.5)
                body = " ".join([pct(-0.1 * top, 1.1 * top), pct(-c, c), pct(-c, c)])
            elif kind in ("lch", "oklch"):
                top, c = (100, 230) if kind == "lch" else (1, 0.5)
                body = " ".join([pct(-0.1 * top, 1.1 * top), pct(-0.1 * c, c), angle()])
            else:
                body = " ".join([angle(), pct(-10, 120), pct(-10, 120)])
            corpus.append(f"{kind}({body}{alpha()})")
    return corpus


CORPUS = _corpus()


def _tre_fill(raw):
    def ask():
        spec = {"id": "r", "kind": "Rect", "style": {"width": 1, "height": 1, "background": raw}}
        view = tre.View(spec=spec)
        tre.Window.from_view(view, width=10, height=10, title="t")
        return view.node("r").get("fill")
    return reference.tre(ask)


@pytest.mark.parametrize("raw", CORPUS)
def test_the_corpus_parses_as_tre_parses_it(raw):
    assert tokens.parse_color(raw) == _tre_fill(raw)


def test_the_corpus_reaches_every_space_and_both_ends_of_the_range():
    assert {raw.split("(")[1].split()[0] for raw in CORPUS if raw.startswith("color(")} == set(SPACES)
    parsed = [tokens.parse_color(raw) for raw in CORPUS]
    channels = [c for rgba in parsed for c in rgba[:3]]
    assert channels.count(0) > 50 and channels.count(255) > 50  # clipped at both ends, often
    assert sum(1 for c in channels if 0 < c < 255) > len(channels) // 2  # mostly in range, where precision shows
    assert sum(1 for rgba in parsed if rgba[3] == 0) > 5  # `none` and negative alphas
    assert sum(1 for raw in CORPUS if "none" in raw) > 40
