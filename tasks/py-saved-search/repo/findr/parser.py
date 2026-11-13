"""Parse search text into nodes (see nodes.py)."""

from __future__ import annotations

import re

from .lexer import ParseError, Token, tokenize
from .nodes import And, Compare, Node, Not, Or, Term

__all__ = ["parse", "ParseError"]

FIELD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
NUMBER_RE = re.compile(r"\d+(\.\d+)?\Z")


def parse(text: str) -> Node:
    """Parse a search. An empty search is an error."""
    parser = _Parser(tokenize(text), len(text))
    node = parser.parse_or()
    if parser.peek() is not None:
        tok = parser.peek()
        raise ParseError(f"unexpected {tok.text!r}", tok.pos)
    return node


class _Parser:
    def __init__(self, tokens: list[Token], length: int) -> None:
        self.tokens = tokens
        self.index = 0
        self.length = length

    def peek(self, ahead: int = 0) -> Token | None:
        i = self.index + ahead
        return self.tokens[i] if i < len(self.tokens) else None

    def advance(self) -> Token:
        tok = self.peek()
        if tok is None:
            raise ParseError("unexpected end of search", self.length)
        self.index += 1
        return tok

    def at_keyword(self, word: str) -> bool:
        tok = self.peek()
        return tok is not None and tok.kind == "KEYWORD" and tok.text == word

    def parse_or(self) -> Node:
        items = [self.parse_and()]
        while self.at_keyword("OR"):
            self.advance()
            items.append(self.parse_and())
        return items[0] if len(items) == 1 else Or(tuple(items))

    def parse_and(self) -> Node:
        items = [self.parse_not()]
        while True:
            if self.at_keyword("AND"):
                self.advance()
                items.append(self.parse_not())
            elif self._starts_term():
                items.append(self.parse_not())
            else:
                break
        return items[0] if len(items) == 1 else And(tuple(items))

    def _starts_term(self) -> bool:
        tok = self.peek()
        if tok is None:
            return False
        if tok.kind in ("WORD", "STRING", "LPAREN", "MINUS"):
            return True
        return tok.kind == "KEYWORD" and tok.text == "NOT"

    def parse_not(self) -> Node:
        tok = self.peek()
        if tok is not None and (tok.kind == "MINUS" or (tok.kind == "KEYWORD" and tok.text == "NOT")):
            self.advance()
            return Not(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Node:
        tok = self.advance()
        if tok.kind == "LPAREN":
            node = self.parse_or()
            close = self.advance()
            if close.kind != "RPAREN":
                raise ParseError("expected ')'", close.pos)
            return node
        if tok.kind == "STRING":
            return Term(None, tok.text)
        if tok.kind != "WORD":
            raise ParseError(f"unexpected {tok.text!r}", tok.pos)

        nxt = self.peek()
        if nxt is not None and nxt.kind == "COLON":
            self._check_field(tok)
            self.advance()
            value = self.advance()
            if value.kind not in ("WORD", "STRING", "KEYWORD"):
                raise ParseError("expected a value", value.pos)
            return Term(tok.text, value.text)
        if nxt is not None and nxt.kind == "OP":
            self._check_field(tok)
            op = self.advance()
            number = self.advance()
            if number.kind != "WORD" or not NUMBER_RE.match(number.text):
                raise ParseError("expected a number", number.pos)
            return Compare(tok.text, op.text, number.text)
        return Term(None, tok.text)

    @staticmethod
    def _check_field(tok: Token) -> None:
        if not FIELD_RE.match(tok.text):
            raise ParseError(f"bad field name {tok.text!r}", tok.pos)
