"""Split search text into tokens. See docs/syntax.md for the language."""

from __future__ import annotations

from dataclasses import dataclass

KEYWORDS = frozenset({"AND", "OR", "NOT"})

# Characters that end a bare word. A bare word may contain '-' and '\' anywhere
# except that a leading '-' is read as NOT.
SPECIAL = frozenset('():"<>')


class ParseError(ValueError):
    """The search text is not valid. ``pos`` is the offset of the problem."""

    def __init__(self, message: str, pos: int) -> None:
        super().__init__(f"{message} at offset {pos}")
        self.pos = pos


@dataclass(frozen=True)
class Token:
    kind: str  # LPAREN RPAREN COLON OP MINUS WORD STRING KEYWORD
    text: str
    pos: int


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    while pos < len(text):
        ch = text[pos]
        if ch.isspace():
            pos += 1
        elif ch == "(":
            tokens.append(Token("LPAREN", ch, pos))
            pos += 1
        elif ch == ")":
            tokens.append(Token("RPAREN", ch, pos))
            pos += 1
        elif ch == ":":
            tokens.append(Token("COLON", ch, pos))
            pos += 1
        elif ch in "<>":
            op = text[pos : pos + 2] if text[pos + 1 : pos + 2] == "=" else ch
            tokens.append(Token("OP", op, pos))
            pos += len(op)
        elif ch == '"':
            value, end = _read_string(text, pos)
            tokens.append(Token("STRING", value, pos))
            pos = end
        elif ch == "-":
            tokens.append(Token("MINUS", ch, pos))
            pos += 1
        else:
            start = pos
            while pos < len(text) and not text[pos].isspace() and text[pos] not in SPECIAL:
                pos += 1
            word = text[start:pos]
            tokens.append(Token("KEYWORD" if word in KEYWORDS else "WORD", word, start))
    return tokens


def _read_string(text: str, start: int) -> tuple[str, int]:
    """Read a quoted value starting at the opening quote; return it and the end offset."""
    out: list[str] = []
    pos = start + 1
    while pos < len(text):
        ch = text[pos]
        if ch == "\\" and text[pos + 1 : pos + 2] == '"':
            out.append('"')
            pos += 2
            continue
        if ch == '"':
            return "".join(out), pos + 1
        out.append(ch)
        pos += 1
    raise ParseError("unterminated string", start)
