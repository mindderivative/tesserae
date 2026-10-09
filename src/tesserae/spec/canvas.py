"""`Canvas`: drawing as data (#215).

```yaml
widget: Canvas
style: {width: 120, height: 24}
draw:
  - {rect: [0, 10, 120, 4], color: surface_variant}
  - {circle: [60, 12, 6], color: primary}
  - {path: [[0, 12], [30, 4], [60, 12, 90, 20], [120, 12]], color: primary, width: 2}
```

`draw:` is a list of commands, painted in order. A command has one shape key and its colour:

- `rect: [x, y, width, height]` filled with `color`;
- `circle: [cx, cy, radius]` filled with `color`;
- `path: [point, ...]` stroked with `color` at `width` (default 1): the first point is `[x, y]` and each later one a line `[x, y]`, a quadratic
  `[cx, cy, x, y]` or a cubic `[c1x, c1y, c2x, c2y, x, y]`.

Numbers are logical pixels from the canvas's top-left; `color` is a theme role, a CSS colour or `role@N%`. `draw:` may be an expression, so a
canvas follows the Signals it reads; `plan(...)` checks the list and returns the commands with their colours resolved, and `painter(...)` makes
the callback tre's canvas runs.
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = ["painter", "plan"]

RGBA = tuple[int, int, int, int]
_SHAPES = ("rect", "circle", "path")
_ARITY = {"rect": 4, "circle": 3}
_SEGMENT = (2, 4, 6)


def _numbers(where: str, value: Any, count: int | tuple[int, ...]) -> tuple[float, ...]:
    counts = (count,) if isinstance(count, int) else count
    if not isinstance(value, (list, tuple)) or len(value) not in counts or any(
            isinstance(n, bool) or not isinstance(n, (int, float)) for n in value):
        want = " or ".join(str(c) for c in counts)
        raise ValueError(f"{where} is {want} numbers, not {value!r}")
    return tuple(float(n) for n in value)


def plan(draw: Any, colour: Callable[[Any], RGBA]) -> list[tuple[Any, ...]]:
    """`draw:` checked and flattened to `("rect", x, y, w, h, rgba)`, `("circle", cx, cy, r, rgba)` and `("path", points, rgba, width)`.
    `colour` resolves a colour value. Raises `ValueError` naming the command (the builder adds the widget)."""
    if draw is None:
        return []
    if not isinstance(draw, (list, tuple)):
        raise ValueError(f'draw is a list of commands, not {draw!r}')
    out: list[tuple[Any, ...]] = []
    for i, command in enumerate(draw):
        where = f"draw[{i}]"
        if not isinstance(command, dict):
            raise ValueError(f"{where} is a mapping like {{rect: [...], color: primary}}, not {command!r}")
        shapes = [k for k in command if k in _SHAPES]
        if len(shapes) != 1:
            raise ValueError(f"{where} needs exactly one of {', '.join(_SHAPES)}, has {shapes or 'none'}")
        shape = shapes[0]
        allowed = {shape, "color"} | ({"width"} if shape == "path" else set())
        unknown = set(command) - allowed
        if unknown:
            raise ValueError(f"{where}: {shape} takes {', '.join(sorted(allowed))}, not {sorted(unknown)}")
        if "color" not in command:
            raise ValueError(f"{where}: {shape} needs a color")
        rgba = colour(command["color"])
        if shape in _ARITY:
            out.append((shape, *_numbers(f"{where}.{shape}", command[shape], _ARITY[shape]), rgba))
            continue
        points = command["path"]
        if not isinstance(points, (list, tuple)) or len(points) < 2:
            raise ValueError(f"{where}.path is two or more points, not {points!r}")
        flat = [list(_numbers(f"{where}.path[{j}]", p, 2 if j == 0 else _SEGMENT)) for j, p in enumerate(points)]
        width = command.get("width", 1)
        if isinstance(width, bool) or not isinstance(width, (int, float)) or width <= 0:
            raise ValueError(f"{where}.width is a number above 0, not {width!r}")
        out.append(("path", flat, rgba, float(width)))
    return out


def painter(commands: list[tuple[Any, ...]]) -> Callable[[Any], None]:
    """The callback tre's canvas runs with its `Painter`, drawing `commands` (from `plan`)."""
    def draw(p: Any) -> None:
        for command in commands:
            if command[0] == "rect":
                p.fill_rect(*command[1:5], command[5])
            elif command[0] == "circle":
                p.fill_circle(*command[1:4], command[4])
            else:
                p.stroke_path(command[1], command[2], command[3])
    return draw
