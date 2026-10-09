"""`open_url(url)`: hand a link to the OS (#224).

The default browser or mail program opens it. Only `http`, `https`, `mailto` and `tel` links are opened: a view's text can come from anywhere, and
`file:`, `javascript:` or an application's own scheme would run something rather than show a page.
"""

from __future__ import annotations

import webbrowser
from typing import Callable, Optional
from urllib.parse import urlsplit

__all__ = ["SCHEMES", "check_url", "open_url"]

SCHEMES = ("http", "https", "mailto", "tel")


def check_url(url: object) -> str:
    """`url` if it is a link `open_url` will open; otherwise a `ValueError` saying why."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError(f"open_url() takes a link such as 'https://example.com', not {url!r}")
    if any(ord(c) < 32 or ord(c) == 127 or c.isspace() for c in url):
        raise ValueError(f"open_url() will not open a link with spaces or control characters in it: {url!r}")
    parts = urlsplit(url)
    scheme = parts.scheme  # urlsplit lower-cases it
    if scheme not in SCHEMES:
        raise ValueError(f"open_url() opens {', '.join(SCHEMES)} links, not {scheme + ':' if scheme else 'a link with no scheme'} ({url!r})")
    if scheme in ("http", "https") and not parts.netloc:
        raise ValueError(f"open_url(): the link {url!r} has no host")
    return url


def open_url(url: str, opener: Optional[Callable[[str], bool]] = None) -> bool:
    """Opens `url` with the OS's opener (`webbrowser.open`, unless `opener` is given); whether it could be opened. Raises `ValueError` for a link that
    is not allowed."""
    return bool((opener or webbrowser.open)(check_url(url)))
