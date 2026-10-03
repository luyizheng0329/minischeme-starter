"""Built-in procedures installed in the initial environment."""

from __future__ import annotations

import sys
from functools import reduce
from typing import Any, Callable

from environment import Environment
from runtime import (
    BuiltinProcedure,
    NIL,
    Pair,
    Procedure,
    String,
    Symbol,
    display_str,
    equal_values,
    is_number,
    is_proper_list,
    list_items,
    pair_from_items,
)


def install_builtins(environment: Environment) -> None:
    procedures: dict[str, Callable[..., Any]] = {
        "+": _add,
        "-": _subtract,
        "*": _multiply,
        "/": _divide,
        "modulo": _modulo,
        "quotient": _quotient,
        "expt": _expt,
        "abs": _absolute,
        "=": _equal_compare,
        "<": _less_than,
        ">": _greater_than,
        "<=": _less_equal,
        ">=": _greater_equal,
        "not": _not,
        "cons": _cons,
        "car": _car,
        "cdr": _cdr,
        "list": _list,
        "length": _length,
        "append": _append,
        "null?": _null,
        "pair?": _pair,
        "list?": _list_predicate,
        "number?": _number,
        "boolean?": _boolean,
        "symbol?": _symbol,
        "string?": _string,
        "procedure?": _procedure,
        "zero?": _zero,
        "even?": _even,
        "odd?": _odd,
        "eq?": _eq,
        "equal?": _equal,
        "display": _display,
        "newline": _newline,
    }
    for name, function in procedures.items():
        environment.define(name, BuiltinProcedure(function, name))


def _require_arity(name: str, arguments: tuple[Any, ...], count: int) -> None:
    if len(arguments) != count:
        raise TypeError(f"{name} expects {count} argument(s)")


def _require_numbers(name: str, arguments: tuple[Any, ...]) -> None:
    if not all(is_number(argument) for argument in arguments):
        raise TypeError(f"{name} expects numbers")


def _add(*arguments: Any) -> Any:
    _require_numbers("+", arguments)
    return sum(arguments, 0)


def _subtract(*arguments: Any) -> Any:
    if not arguments:
        raise TypeError("- expects at least one argument")
    _require_numbers("-", arguments)
    if len(arguments) == 1:
        return -arguments[0]
    return reduce(lambda left, right: left - right, arguments[1:], arguments[0])


def _multiply(*arguments: Any) -> Any:
    _require_numbers("*", arguments)
    return reduce(lambda left, right: left * right, arguments, 1)


def _divide(*arguments: Any) -> Any:
    if not arguments:
        raise TypeError("/ expects at least one argument")
    _require_numbers("/", arguments)
    if len(arguments) == 1:
        return 1 / arguments[0]
    result: Any = arguments[0]
    for divisor in arguments[1:]:
        if type(result) is int and type(divisor) is int:
            result = _truncate_toward_zero(result, divisor)
        else:
            result = result / divisor
    return result


def _modulo(left: Any, right: Any) -> int:
    arguments = (left, right)
    _require_numbers("modulo", arguments)
    if type(left) is not int or type(right) is not int:
        raise TypeError("modulo expects integers")
    return left % right


def _quotient(left: Any, right: Any) -> int:
    arguments = (left, right)
    _require_numbers("quotient", arguments)
    if type(left) is not int or type(right) is not int:
        raise TypeError("quotient expects integers")
    return _truncate_toward_zero(left, right)


def _truncate_toward_zero(left: int, right: int) -> int:
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def _expt(left: Any, right: Any) -> Any:
    _require_numbers("expt", (left, right))
    return left**right


def _absolute(value: Any) -> Any:
    _require_numbers("abs", (value,))
    return abs(value)


def _compare(arguments: tuple[Any, ...], comparator: Callable[[Any, Any], bool]) -> bool:
    if len(arguments) < 2:
        return True
    for left, right in zip(arguments, arguments[1:]):
        if not comparator(left, right):
            return False
    return True


def _equal_compare(*arguments: Any) -> bool:
    return _compare(arguments, equal_values)


def _less_than(*arguments: Any) -> bool:
    return _compare(arguments, lambda left, right: left < right)


def _greater_than(*arguments: Any) -> bool:
    return _compare(arguments, lambda left, right: left > right)


def _less_equal(*arguments: Any) -> bool:
    return _compare(arguments, lambda left, right: left <= right)


def _greater_equal(*arguments: Any) -> bool:
    return _compare(arguments, lambda left, right: left >= right)


def _not(value: Any) -> bool:
    return value is False


def _cons(first: Any, rest: Any) -> Pair:
    return Pair(first, rest)


def _car(pair: Any) -> Any:
    if not isinstance(pair, Pair):
        raise TypeError("car expects a pair")
    return pair.car


def _cdr(pair: Any) -> Any:
    if not isinstance(pair, Pair):
        raise TypeError("cdr expects a pair")
    return pair.cdr


def _list(*arguments: Any) -> Any:
    return pair_from_items(arguments)


def _length(value: Any) -> int:
    return len(list_items(value))


def _append(*arguments: Any) -> Any:
    items: list[Any] = []
    for argument in arguments:
        items.extend(list_items(argument))
    return pair_from_items(items)


def _null(value: Any) -> bool:
    return value is NIL


def _pair(value: Any) -> bool:
    return isinstance(value, Pair)


def _list_predicate(value: Any) -> bool:
    return is_proper_list(value)


def _number(value: Any) -> bool:
    return is_number(value)


def _boolean(value: Any) -> bool:
    return type(value) is bool


def _symbol(value: Any) -> bool:
    return type(value) is Symbol


def _string(value: Any) -> bool:
    return type(value) is String


def _procedure(value: Any) -> bool:
    return isinstance(value, Procedure)


def _zero(value: Any) -> bool:
    _require_numbers("zero?", (value,))
    return value == 0


def _even(value: Any) -> bool:
    if type(value) is not int:
        raise TypeError("even? expects an integer")
    return value % 2 == 0


def _odd(value: Any) -> bool:
    if type(value) is not int:
        raise TypeError("odd? expects an integer")
    return value % 2 != 0


def _eq(left: Any, right: Any) -> bool:
    if left is NIL or right is NIL:
        return left is right
    if is_number(left) and is_number(right):
        return left == right
    if type(left) is type(right) and type(left) in (bool, int, float, Symbol, String):
        return left == right
    return left is right


def _equal(left: Any, right: Any) -> bool:
    return equal_values(left, right)


def _display(value: Any) -> None:
    sys.stdout.write(display_str(value))
    return None


def _newline() -> None:
    sys.stdout.write("\n")
    return None
