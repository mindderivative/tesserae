"""`mask:` on a `TextInput`: the text is put in a pattern as the user types or pastes (#222).

```yaml
widget: TextInput
mask: "(###) ###-####"
```

In a pattern `#` is a digit, `A` a letter and `*` a letter or digit; `\\` makes the next character a literal; any other character is a literal.
The user's text is read left to right: each slot takes the next character it accepts and a character it does not accept is dropped, so a paste
of `1234567890`, of `123-456-7890` or of `(123) 456-7890` all become `(123) 456-7890`. Literals come by themselves, but only when more input
follows them: `123` is `(123` and the `) ` appears with the fourth digit, so backspace is never stuck on one. A literal the user typed is kept.
What does not fit after the last slot is dropped.

`Mask(pattern).apply(text)` is the whole of it. tre's input has no caret control yet (#234), so an edit in the middle of the text leaves the caret at
the end.
"""

from __future__ import annotations

from typing import Optional

__all__ = ["Mask"]


def _digit(c: str) -> bool:
    return c in "0123456789"


_SLOTS = {"#": _digit, "A": str.isalpha, "*": str.isalnum}


class Mask:
    """A compiled pattern. Raises `ValueError` for one that is empty, ends in `\\` or has no slot."""

    def __init__(self, pattern: str) -> None:
        if not isinstance(pattern, str) or not pattern:
            raise ValueError(f"a mask is a pattern such as '(###) ###-####', not {pattern!r}")
        self.pattern = pattern
        #: (slot character or None, literal): a slot has no literal and a literal no slot character
        self.tokens: list[tuple[Optional[str], str]] = []
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c == "\\":
                if i + 1 == len(pattern):
                    raise ValueError(f"the mask {pattern!r} ends in a backslash, which makes the next character a literal")
                self.tokens.append((None, pattern[i + 1]))
                i += 2
                continue
            self.tokens.append((c, "") if c in _SLOTS else (None, c))
            i += 1
        if not any(slot for slot, _ in self.tokens):
            raise ValueError(f"the mask {pattern!r} has no slot: # is a digit, A a letter, * a letter or digit")

    def _next(self, slot: str, text: str, start: int) -> int:
        """Where in `text`, from `start`, the next character `slot` takes is; `len(text)` if none."""
        j = start
        while j < len(text) and not _SLOTS[slot](text[j]):
            j += 1
        return j

    def apply(self, text: str) -> str:
        """`text` in the pattern."""
        out: list[str] = []
        at = 0
        for index, (slot, literal) in enumerate(self.tokens):
            if slot is not None:
                found = self._next(slot, text, at)
                if found == len(text):
                    break
                out.append(text[found])
                at = found + 1
            elif text[at:at + 1] == literal:  # typed by the user
                out.append(literal)
                at += 1
            elif self._more_input(index, text, at):  # put in, because more is coming
                out.append(literal)
        return "".join(out)

    def _more_input(self, index: int, text: str, at: int) -> bool:
        """Whether a slot after token `index` has a character to take from `text[at:]`."""
        cursor = at
        for slot, _ in self.tokens[index + 1:]:
            if slot is not None:
                return self._next(slot, text, cursor) < len(text)
        return False
