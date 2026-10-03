"""Tokenizer and parser for mini-Scheme source text."""

from __future__ import annotations

import re
from typing import Any

from runtime import DottedList, String, Symbol


_INTEGER = re.compile(r"^[+-]?\d+$")
_FLOAT = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*)|(?:\.\d+))(?:[eE][+-]?\d+)?$"
)


def tokenize(source: str) -> list[tuple[str, Any]]:
    tokens: list[tuple[str, Any]] = []
    index = 0
    length = len(source)
    while index < length:
        character = source[index]
        if character.isspace():
            index += 1
            continue
        if character == ";":
            newline = source.find("\n", index)
            index = length if newline == -1 else newline + 1
            continue
        if character == "(":
            tokens.append(("LPAREN", character))
            index += 1
            continue
        if character == ")":
            tokens.append(("RPAREN", character))
            index += 1
            continue
        if character == "'":
            tokens.append(("QUOTE", character))
            index += 1
            continue
        if character == '"':
            value, index = _read_string(source, index + 1)
            tokens.append(("STRING", value))
            continue

        start = index
        while index < length and not source[index].isspace() and source[index] not in "();'":
            index += 1
        if start == index:
            raise SyntaxError(f"unexpected character {source[index]!r}")
        atom = source[start:index]
        tokens.append(("DOT" if atom == "." else "ATOM", atom))
    return tokens


def _read_string(source: str, index: int) -> tuple[String, int]:
    characters: list[str] = []
    while index < len(source):
        character = source[index]
        if character == '"':
            return String("".join(characters)), index + 1
        if character == "\\":
            index += 1
            if index >= len(source):
                raise SyntaxError("unterminated string escape")
            escape = source[index]
            characters.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escape, escape))
        else:
            characters.append(character)
        index += 1
    raise SyntaxError("unterminated string")


def parse_program(source: str) -> list[Any]:
    tokens = tokenize(source)
    expressions: list[Any] = []
    position = 0
    while position < len(tokens):
        expression, position = _parse_expression(tokens, position)
        expressions.append(expression)
    return expressions


def _parse_expression(tokens: list[tuple[str, Any]], position: int) -> tuple[Any, int]:
    if position >= len(tokens):
        raise SyntaxError("unexpected end of input")
    kind, value = tokens[position]
    if kind == "LPAREN":
        return _parse_list(tokens, position + 1)
    if kind == "RPAREN":
        raise SyntaxError("unexpected )")
    if kind == "DOT":
        raise SyntaxError("unexpected .")
    if kind == "QUOTE":
        expression, next_position = _parse_expression(tokens, position + 1)
        return [Symbol("quote"), expression], next_position
    if kind == "STRING":
        return value, position + 1
    return _parse_atom(value), position + 1


def _parse_list(tokens: list[tuple[str, Any]], position: int) -> tuple[Any, int]:
    items: list[Any] = []
    while position < len(tokens):
        kind, value = tokens[position]
        if kind == "RPAREN":
            return items, position + 1
        if kind == "DOT":
            if not items:
                raise SyntaxError("dotted list needs a head")
            tail, position = _parse_expression(tokens, position + 1)
            if position >= len(tokens) or tokens[position][0] != "RPAREN":
                raise SyntaxError("dotted list must end after its tail")
            return DottedList(items, tail), position + 1
        item, position = _parse_expression(tokens, position)
        items.append(item)
    raise SyntaxError("unterminated list")


def _parse_atom(atom: str) -> Any:
    if atom == "#t":
        return True
    if atom == "#f":
        return False
    if _INTEGER.match(atom):
        return int(atom)
    if _FLOAT.match(atom):
        return float(atom)
    return Symbol(atom)
