"""CSS Color 4's wide-gamut functions, `color()`, `lab()`, `lch()`,
`oklab()`, `oklch()` and `hwb()`, as `tre` 0.3.4 parsed them (M63).

`tre` 0.3.4 read a colour string with the `color` crate (0.3.3):
`parse_color(raw).to_alpha_color::<Srgb>()`, stored as 8-bit RGBA by
`to_rgba8`, which clips each channel into range. This is that path in
Python: the same grammar (comments, `none`, angle units, percentages),
the same constants, and `f32` arithmetic, each step rounded to `f32` as
the crate's is, so the bytes match. `tokens.parse_color` calls
`parse(text)` for these six functions; everything else it parses itself.
"""

from __future__ import annotations

import math
import struct
from typing import Callable, Optional

RGBA = tuple[int, int, int, int]
_Vec = tuple[float, float, float]

NAMES = ("color", "lab", "lch", "oklab", "oklch", "hwb")


def _f(x: float) -> float:
    """`x` rounded to the nearest `f32`, as Rust's `as f32` does."""
    try:
        return struct.unpack("f", struct.pack("f", x))[0]
    except OverflowError:
        return math.copysign(math.inf, x)


def _pow(x: float, y: float) -> float:
    return _f(math.pow(x, y))


def _m(rows: list[list[float]]) -> tuple[_Vec, ...]:
    return tuple((_f(a), _f(b), _f(c)) for a, b, c in rows)


def _matvec(m: tuple[_Vec, ...], x: _Vec) -> _Vec:
    """The crate's `matvecmul`, left to right in `f32`."""
    a, b, c = (_f(_f(_f(r[0] * x[0]) + _f(r[1] * x[1])) + _f(r[2] * x[2])) for r in m)
    return (a, b, c)


# -- sRGB's transfer -----------------------------------------------------------------

_INV_12_92, _INV_1_055, _INV_2_4 = _f(1 / _f(12.92)), _f(1 / _f(1.055)), _f(1 / _f(2.4))


def _srgb_to_lin(x: float) -> float:
    if abs(x) <= _f(0.04045):
        return _f(x * _INV_12_92)
    return math.copysign(_pow(_f(_f(abs(x) + _f(0.055)) * _INV_1_055), _f(2.4)), x)


def _lin_to_srgb(x: float) -> float:
    if abs(x) <= _f(0.0031308):
        return _f(x * _f(12.92))
    return math.copysign(_f(_f(_f(1.055) * _pow(abs(x), _INV_2_4)) - _f(0.055)), x)


# -- each space to linear sRGB -------------------------------------------------------

_P3 = _m([[1.224_940_2, -0.224_940_18, 0.0], [-0.042_056_955, 1.042_056_9, 0.0],
          [-0.019_637_555, -0.078_636_04, 1.098_273_6]])
_A98 = _m([[66_942_405 / 47_872_228, -19_070_177 / 47_872_228, 0.0], [0.0, 1.0, 0.0],
           [0.0, -11_512_411 / 268_173_353, 279_685_764 / 268_173_353]])
_PROPHOTO = _m([[2.034_367_6, -0.727_634_5, -0.306_733_07], [-0.228_826_79, 1.231_753_3, -0.002_926_598],
                [-0.008_558_424, -0.153_268_2, 1.161_826_6]])
_REC2020 = _m([[2_785_571_537 / 1_677_558_947, -985_802_650 / 1_677_558_947, -122_209_940 / 1_677_558_947],
               [-4_638_020_506 / 37_238_079_773, 42_187_016_744 / 37_238_079_773, -310_916_465 / 37_238_079_773],
               [-97_469_024 / 5_369_968_309, -3_780_738_464 / 37_589_778_163, 42_052_799_795 / 37_589_778_163]])
_XYZ_D50 = _m([[3.134_136, -1.617_386, -0.490_662_22], [-0.978_795_47, 1.916_254_4, 0.033_442_874],
               [0.071_955_39, -0.228_976_76, 1.405_386_1]])
_XYZ_D65 = _m([[12_831 / 3_959, -329 / 214, -1_974 / 3_959],
               [-851_781 / 878_810, 1_648_619 / 878_810, 36_519 / 878_810],
               [705 / 12_673, -2_585 / 12_673, 705 / 667]])
_OKLAB_TO_LMS = _m([[1.0, 0.396_337_78, 0.215_803_76], [1.0, -0.105_561_346, -0.063_854_17],
                    [1.0, -0.089_484_18, -1.291_485_5]])
_LMS_TO_SRGB = _m([[4.076_741_7, -3.307_711_6, 0.230_969_94], [-1.268_438, 2.609_757_4, -0.341_319_38],
                   [-0.004_196_086_3, -0.703_418_6, 1.707_614_7]])
_LAB_XYZ_TO_SRGB = _m([[3.022_233_7, -1.617_386, -0.404_847_65], [-0.943_848_25, 1.916_254_4, 0.027_593_868],
                       [0.069_386_27, -0.228_976_76, 1.159_590_5]])

_A98_GAMMA = _f(563 / 256)
_REC_A, _REC_B = _f(1.099_296_8), _f(0.018_053_97)
_REC_A1, _REC_B45, _INV_4_5, _INV_0_45 = _f(_REC_A - 1), _f(_REC_B * 4.5), _f(1 / 4.5), _f(1 / _f(0.45))
_KAPPA = _f(24389 / 27)
_K116, _K16 = _f(116 / _KAPPA), _f(16 / _KAPPA)
_INV_116, _SIXTEEN_116, _INV_500, _INV_200 = _f(1 / 116), _f(16 / 116), _f(1 / 500), _f(1 / 200)
_EPSILON_CBRT = _f(0.206_896_56)
_RADS_PER_DEG = _f(_f(math.pi) / 180)
_INV_30, _INV_12 = _f(1 / 30), _f(1 / 12)


def _signed_pow(x: float, y: float) -> float:
    return math.copysign(_pow(abs(x), y), x)


def _prophoto_to_lin(x: float) -> float:
    return _f(x / 16) if abs(x) <= _f(16 / 512) else _signed_pow(x, _f(1.8))


def _rec2020_to_lin(x: float) -> float:
    if abs(x) < _REC_B45:
        return _f(x * _INV_4_5)
    return math.copysign(_pow(_f(_f(abs(x) + _REC_A1) / _REC_A), _INV_0_45), x)


def _lab_to_lin(l: float, a: float, b: float) -> _Vec:
    f1 = _f(_f(l * _INV_116) + _SIXTEEN_116)
    f0 = _f(_f(a * _INV_500) + f1)
    f2 = _f(f1 - _f(b * _INV_200))

    def cube(v: float) -> float:
        return _f(_f(v * v) * v) if v > _EPSILON_CBRT else _f(_f(_K116 * v) - _K16)

    return _matvec(_LAB_XYZ_TO_SRGB, (cube(f0), cube(f1), cube(f2)))


def _oklab_to_lin(l: float, a: float, b: float) -> _Vec:
    x, y, z = (_f(_f(v * v) * v) for v in _matvec(_OKLAB_TO_LMS, (l, a, b)))
    return _matvec(_LMS_TO_SRGB, (x, y, z))


def _lch_to_lab(l: float, c: float, h: float) -> _Vec:
    rad = _f(h * _RADS_PER_DEG)
    return (l, _f(c * _f(math.cos(rad))), _f(c * _f(math.sin(rad))))


def _hwb_to_srgb(h: float, w: float, b: float) -> _Vec:
    white, black = _f(w * _f(0.01)), _f(b * _f(0.01))
    if _f(white + black) >= 1:
        gray = _f(white / _f(white + black))
        return (gray, gray, gray)
    scale = _f(_f(1 - white) - black)
    out = []
    for n in (0.0, 8.0, 4.0):  # hsl_to_rgb([h, 100, 50]): lightness 0.5, and a = 0.5
        x = _f(n + _f(h * _INV_30))
        k = _f(x - _f(12 * math.floor(_f(x * _INV_12))))
        hue = _f(0.5 - _f(0.5 * max(-1.0, min(1.0, min(_f(k - 3), _f(9 - k))))))
        out.append(_f(white + _f(hue * scale)))
    return (out[0], out[1], out[2])


def _each(fn: Callable[[float], float]) -> Callable[[_Vec], _Vec]:
    return lambda v: (fn(v[0]), fn(v[1]), fn(v[2]))


#: `color()`'s spaces, each to linear sRGB (the crate's `ColorSpace` impls); sRGB is as given.
_RGB_SPACES: dict[str, Optional[Callable[[_Vec], _Vec]]] = {
    "srgb": None,
    "srgb-linear": lambda v: v,
    "display-p3": lambda v: _matvec(_P3, _each(_srgb_to_lin)(v)),
    "a98-rgb": lambda v: _matvec(_A98, _each(lambda x: _signed_pow(x, _A98_GAMMA))(v)),
    "prophoto-rgb": lambda v: _matvec(_PROPHOTO, _each(_prophoto_to_lin)(v)),
    "rec2020": lambda v: _matvec(_REC2020, _each(_rec2020_to_lin)(v)),
    "xyz-d50": lambda v: _matvec(_XYZ_D50, v),
    "xyz-d65": lambda v: _matvec(_XYZ_D65, v),
    "xyz": lambda v: _matvec(_XYZ_D65, v),
}


# -- the parser (the crate's `Parser`, for these six functions) ---------------------------

def _digit(c: str) -> bool:
    return c.isascii() and c.isdigit()


class _Parser:
    def __init__(self, s: str):
        self.s, self.ix = s, 0

    def _at(self, i: int) -> str:
        j = self.ix + i
        return self.s[j] if j < len(self.s) else ""

    def _comments(self) -> None:
        while self.s.startswith("/*", self.ix):
            end = self.s.find("*/", self.ix + 2)
            if end < 0:
                raise ValueError("unclosed comment")
            self.ix = end + 2

    def number(self) -> Optional[float]:
        self._comments()
        i, valid = (1 if self._at(0) in ("+", "-") and self._at(0) else 0), False
        while _digit(self._at(i)):
            valid, i = True, i + 1
        if self._at(i) == "." and _digit(self._at(i + 1)):
            valid, i = True, i + 2
            while _digit(self._at(i)):
                i += 1
        if self._at(i) in ("e", "E") and self._at(i):
            j = i + 1 + (1 if self._at(i + 1) in ("+", "-") and self._at(i + 1) else 0)
            if _digit(self._at(j)):
                i = j + 1
                while _digit(self._at(i)):
                    i += 1
        if not valid:
            return None
        text = self.s[self.ix:self.ix + i]
        self.ix += i
        return float(text)

    def ident(self) -> Optional[str]:
        i = 0
        while self._at(i):
            c = self._at(i)
            if c.isascii() and (c.isalpha() or c in "_-" or (c.isdigit() and (i >= 2 or (i == 1 and self._at(0) != "-")))):
                i += 1
            else:
                break
        text = self.s[self.ix:self.ix + i]
        if text[:2].strip("-") == "":  # '', '-' and anything starting '--' aren't identifiers
            return None
        self.ix += i
        return text

    def ch(self, c: str) -> bool:
        self._comments()
        if self._at(0) == c:
            self.ix += 1
            return True
        return False

    def ws(self) -> None:
        while True:
            self._comments()
            start = self.ix
            while self._at(0) and self._at(0) in " \t\r\n":
                self.ix += 1
            if self.ix == start:
                return

    def value(self) -> tuple[str, float, str]:
        number = self.number()
        if number is not None:
            if self._at(0) == "%":
                self.ix += 1
                return ("percent", number, "")
            unit = self.ident()
            return ("dimension", number, unit) if unit is not None else ("number", number, "")
        name = self.ident()
        return ("symbol", 0.0, name) if name is not None else ("", 0.0, "")

    def component(self, scale: float, pct_scale: float) -> Optional[float]:
        self.ws()
        kind, number, text = self.value()
        if kind == "number":
            return number * scale
        if kind == "percent":
            return number * pct_scale
        if kind == "symbol" and text.lower() == "none":
            return None
        raise ValueError("unknown color component")

    def angle(self) -> Optional[float]:
        self.ws()
        kind, number, text = self.value()
        if kind == "number":
            return number
        if kind == "symbol" and text.lower() == "none":
            return None
        if kind == "dimension":
            scale = {"deg": 1.0, "rad": math.degrees(1.0), "grad": 0.9, "turn": 360.0}.get(text.lower())
            if scale is None:
                raise ValueError("unknown angle dimension")
            return number * scale
        raise ValueError("unknown angle")

    def alpha(self) -> Optional[float]:
        self.ws()
        if self.ch("/"):  # the crate clamps alpha into 0-1; `_u8` saturates to the same bytes
            return self.component(1.0, 0.01)
        return 1.0

    def close(self) -> None:
        self.ws()
        if not self.ch(")"):
            raise ValueError("expected closing parenthesis")


def _clamp(value: Optional[float], lo: float, hi: float = math.inf) -> Optional[float]:
    return None if value is None else min(max(value, lo), hi)


def _u8(x: float) -> int:
    """The crate's `fast_round_to_u8(x * 255)`: add a half, then a saturating `as u8`."""
    v = _f(_f(x * 255) + 0.5)
    return 0 if math.isnan(v) else int(min(max(v, 0.0), 255.0))


def parse(text: str) -> RGBA:
    """One of the six functions (`text` stripped) as 8-bit RGBA. Raises
    `ValueError` with the crate's reason."""
    p = _Parser(text)
    name = (p.ident() or "").lower()
    if name not in NAMES or not p.ch("("):
        raise ValueError("expected arguments")
    space = ""
    if name == "color":
        p.ws()
        space = (p.ident() or "").lower()
        if not space:
            raise ValueError("expected color space identifier")
        if space not in _RGB_SPACES:
            raise ValueError("unknown color space")
        values = [p.component(1.0, 0.01) for _ in range(3)]
    elif name in ("lab", "oklab"):
        lmax, c = (100.0, 1.25) if name == "lab" else (1.0, 0.004)
        values = [_clamp(p.component(1.0, 0.01 * lmax), 0.0, lmax), p.component(1.0, c), p.component(1.0, c)]
    elif name in ("lch", "oklch"):
        lmax, c = (100.0, 1.25) if name == "lch" else (1.0, 0.004)
        values = [_clamp(p.component(1.0, 0.01 * lmax), 0.0, lmax), _clamp(p.component(1.0, c), 0.0), p.angle()]
    else:  # hwb
        values = [p.angle(), p.component(1.0, 1.0), p.component(1.0, 1.0)]
    alpha = p.alpha()
    p.close()
    if p.ix != len(text):
        raise ValueError("expected end of string")
    x, y, z = (_f(v or 0.0) for v in values)  # a missing (`none`) component is 0 (CSS Color 4 § 4.4)
    if name == "color":
        to_lin = _RGB_SPACES[space]
        rgb = (x, y, z) if to_lin is None else _each(_lin_to_srgb)(to_lin((x, y, z)))
        # an RGB-like space's missing channel is missing, so 0, in sRGB too (§ 12.2)
        r, g, b = (0.0 if v is None else out for v, out in zip(values, rgb))
    elif name == "hwb":
        r, g, b = _hwb_to_srgb(x, y, z)
    else:
        lab = _lch_to_lab(x, y, z) if name in ("lch", "oklch") else (x, y, z)
        lin = _lab_to_lin(*lab) if name in ("lab", "lch") else _oklab_to_lin(*lab)
        r, g, b = _each(_lin_to_srgb)(lin)
    return (_u8(r), _u8(g), _u8(b), _u8(_f(alpha or 0.0)))
