"""Runtime values used by the mini-Scheme interpreter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


class Symbol(str):
    """A Scheme symbol, kept distinct from Scheme strings."""


class String(str):
    """A Scheme string, kept distinct from Scheme symbols."""


class Nil:
    """The singleton value representing the empty list."""

    def __repr__(self) -> str:
        return "()"


NIL = Nil()


@dataclass
class Pair:
    car: Any
    cdr: Any


@dataclass
class DottedList:
    """Parser-only representation for a dotted list expression."""

    items: list[Any]
    tail: Any


class Procedure:
    """Base class for callable Scheme procedures."""


@dataclass
class BuiltinProcedure(Procedure):
    function: Callable[..., Any]
    name: str


@dataclass
class LambdaProcedure(Procedure):
    parameters: list[Symbol]
    body: list[Any]
    environment: Any


def is_number(value: Any) -> bool:
    return type(value) in (int, float)


def is_false(value: Any) -> bool:
    return value is False


def pair_from_items(items: Iterable[Any], tail: Any = NIL) -> Any:
    result = tail
    for item in reversed(list(items)):
        result = Pair(item, result)
    return result


def quote_to_value(expression: Any) -> Any:
    """Turn parser data into the runtime values produced by quote."""

    if isinstance(expression, DottedList):
        return pair_from_items(
            (quote_to_value(item) for item in expression.items),
            quote_to_value(expression.tail),
        )
    if isinstance(expression, list):
        return pair_from_items(quote_to_value(item) for item in expression)
    return expression


def scheme_str(value: Any) -> str:
    """Format a runtime value using the representation in the language spec."""

    if value is NIL:
        return "()"
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if isinstance(value, String):
        return _quote_string(value)
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, Pair):
        return _pair_str(value)
    if isinstance(value, Procedure):
        return "#<procedure>"
    if value is None:
        return ""
    return str(value)


def display_str(value: Any) -> str:
    if isinstance(value, String):
        return str(value)
    return scheme_str(value)


def _quote_string(value: str) -> str:
    escaped = (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def _pair_str(pair: Pair) -> str:
    parts: list[str] = []
    current: Any = pair
    while isinstance(current, Pair):
        parts.append(scheme_str(current.car))
        current = current.cdr
    if current is NIL:
        return "(" + " ".join(parts) + ")"
    return "(" + " ".join(parts) + " . " + scheme_str(current) + ")"


def is_proper_list(value: Any) -> bool:
    while isinstance(value, Pair):
        value = value.cdr
    return value is NIL


def list_items(value: Any) -> list[Any]:
    if not is_proper_list(value):
        raise TypeError("expected a proper list")
    items: list[Any] = []
    while isinstance(value, Pair):
        items.append(value.car)
        value = value.cdr
    return items


def equal_values(left: Any, right: Any) -> bool:
    """Structural equality with Scheme's type distinctions."""

    if left is NIL or right is NIL:
        return left is right
    if isinstance(left, Pair) or isinstance(right, Pair):
        return (
            isinstance(left, Pair)
            and isinstance(right, Pair)
            and equal_values(left.car, right.car)
            and equal_values(left.cdr, right.cdr)
        )
    if is_number(left) and is_number(right):
        return left == right
    if type(left) is not type(right):
        return False
    if type(left) in (int, float, bool, Symbol, String):
        return left == right
    return left is right
