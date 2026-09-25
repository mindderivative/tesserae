"""Tesserae's logging, through `loguru`.

Tesserae logs with loguru's shared `logger` and adds no output of its
own, so its messages go wherever the app's loguru setup sends them. With
no setup, that's loguru's default stderr output. Messages carry the
Tesserae module they came from (`tesserae.spec.watch`, `tesserae.app`,
...), so an app can filter or silence them:

```python
from loguru import logger

logger.disable("tesserae")  # no Tesserae messages at all
```

`configure_logging()` is a one-call setup for an app that wants
Tesserae's format and level on the console.
"""

from __future__ import annotations

import sys
import warnings
from typing import Any

from loguru import logger

__all__ = ["DEFAULT_FORMAT", "configure_logging"]

#: The console format `configure_logging` uses.
DEFAULT_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan> - <level>{message}</level>"
)


def _show_warning(message: Any, category: type, filename: str, lineno: int, file: Any = None, line: Any = None) -> None:
    logger.opt(depth=2).warning("{}: {}", category.__name__, message)


def configure_logging(
    level: str | int = "INFO",
    *,
    sink: Any = sys.stderr,
    format: str = DEFAULT_FORMAT,
    capture_warnings: bool = True,
) -> int:
    """Sends log messages at `level` and above to `sink` (stderr by
    default) in Tesserae's format, and returns the loguru handler id.

    It replaces loguru's default stderr handler, and leaves any handler
    the app added itself. With `capture_warnings` (the default), Python
    warnings, such as `tesserae.fonts.FontFallbackWarning`, are shown
    through loguru too. They're still real warnings, so
    `warnings.filterwarnings("error", ...)` still turns one into an
    exception.

    Call it once, early in `app.py`:

    ```python
    from tesserae import configure_logging

    configure_logging("DEBUG")
    ```
    """
    try:
        logger.remove(0)  # loguru's default stderr handler
    except ValueError:
        pass  # already removed, by an earlier call or by the app
    handler_id = logger.add(sink, level=level, format=format)
    if capture_warnings:
        warnings.showwarning = _show_warning
    return handler_id

