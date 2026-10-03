"""Evaluator and special forms for mini-Scheme."""

from __future__ import annotations

from typing import Any

from environment import Environment
from runtime import (
    BuiltinProcedure,
    DottedList,
    LambdaProcedure,
    Procedure,
    String,
    Symbol,
    is_false,
    quote_to_value,
)


def evaluate(expression: Any, environment: Environment) -> Any:
    if isinstance(expression, Symbol):
        return environment.lookup(str(expression))
    if isinstance(expression, (int, float, bool, String)):
        return expression
    if isinstance(expression, DottedList):
        raise SyntaxError("dotted list cannot be evaluated directly")
    if not isinstance(expression, list):
        return expression
    if not expression:
        raise SyntaxError("cannot evaluate an empty expression")

    operator = expression[0]
    if isinstance(operator, Symbol):
        special_form = str(operator)
        handler = SPECIAL_FORMS.get(special_form)
        if handler is not None:
            return handler(expression[1:], environment)

    procedure = evaluate(operator, environment)
    arguments = [evaluate(argument, environment) for argument in expression[1:]]
    return apply_procedure(procedure, arguments)


def apply_procedure(procedure: Any, arguments: list[Any]) -> Any:
    if isinstance(procedure, BuiltinProcedure):
        return procedure.function(*arguments)
    if isinstance(procedure, LambdaProcedure):
        if len(arguments) != len(procedure.parameters):
            raise TypeError(
                f"expected {len(procedure.parameters)} arguments, got {len(arguments)}"
            )
        child = Environment(procedure.environment)
        for parameter, argument in zip(procedure.parameters, arguments):
            child.define(str(parameter), argument)
        return evaluate_sequence(procedure.body, child)
    raise TypeError(f"{procedure!r} is not a procedure")


def evaluate_sequence(expressions: list[Any], environment: Environment) -> Any:
    result = None
    for expression in expressions:
        result = evaluate(expression, environment)
    return result


def _quote(arguments: list[Any], environment: Environment) -> Any:
    _require_count("quote", arguments, 1)
    return quote_to_value(arguments[0])


def _if(arguments: list[Any], environment: Environment) -> Any:
    if len(arguments) not in (2, 3):
        raise SyntaxError("if expects two or three arguments")
    test = evaluate(arguments[0], environment)
    if not is_false(test):
        return evaluate(arguments[1], environment)
    if len(arguments) == 3:
        return evaluate(arguments[2], environment)
    return None


def _cond(arguments: list[Any], environment: Environment) -> Any:
    for clause in arguments:
        if not isinstance(clause, list) or not clause:
            raise SyntaxError("cond clauses must be non-empty lists")
        test_expression = clause[0]
        if isinstance(test_expression, Symbol) and str(test_expression) == "else":
            matched = True
            test_value = True
        else:
            test_value = evaluate(test_expression, environment)
            matched = not is_false(test_value)
        if matched:
            return test_value if len(clause) == 1 else evaluate_sequence(clause[1:], environment)
    return None


def _and(arguments: list[Any], environment: Environment) -> Any:
    result: Any = True
    for argument in arguments:
        result = evaluate(argument, environment)
        if is_false(result):
            return False
    return result


def _or(arguments: list[Any], environment: Environment) -> Any:
    for argument in arguments:
        result = evaluate(argument, environment)
        if not is_false(result):
            return result
    return False


def _define(arguments: list[Any], environment: Environment) -> Symbol:
    if len(arguments) < 2:
        raise SyntaxError("define expects a name and expression")
    target = arguments[0]
    if isinstance(target, Symbol):
        if len(arguments) != 2:
            raise SyntaxError("variable define expects one expression")
        value = evaluate(arguments[1], environment)
        environment.define(str(target), value)
        return target
    if isinstance(target, list) and target and isinstance(target[0], Symbol):
        name = target[0]
        parameters = target[1:]
        _validate_parameters(parameters)
        procedure = LambdaProcedure(parameters, arguments[1:], environment)
        environment.define(str(name), procedure)
        return name
    raise SyntaxError("invalid define target")


def _lambda(arguments: list[Any], environment: Environment) -> LambdaProcedure:
    if len(arguments) < 2 or not isinstance(arguments[0], list):
        raise SyntaxError("lambda expects parameters and a body")
    parameters = arguments[0]
    _validate_parameters(parameters)
    return LambdaProcedure(parameters, arguments[1:], environment)


def _let(arguments: list[Any], environment: Environment) -> Any:
    if len(arguments) < 2 or not isinstance(arguments[0], list):
        raise SyntaxError("let expects bindings and a body")
    bindings: list[tuple[Symbol, Any]] = []
    for binding in arguments[0]:
        if not isinstance(binding, list) or len(binding) != 2 or not isinstance(binding[0], Symbol):
            raise SyntaxError("invalid let binding")
        bindings.append((binding[0], evaluate(binding[1], environment)))
    child = Environment(environment)
    for name, value in bindings:
        child.define(str(name), value)
    return evaluate_sequence(arguments[1:], child)


def _begin(arguments: list[Any], environment: Environment) -> Any:
    return evaluate_sequence(arguments, environment)


def _require_count(name: str, arguments: list[Any], count: int) -> None:
    if len(arguments) != count:
        raise SyntaxError(f"{name} expects {count} argument(s)")


def _validate_parameters(parameters: list[Any]) -> None:
    if not all(isinstance(parameter, Symbol) for parameter in parameters):
        raise SyntaxError("parameters must be symbols")
    if len({str(parameter) for parameter in parameters}) != len(parameters):
        raise SyntaxError("duplicate parameter")


SPECIAL_FORMS = {
    "quote": _quote,
    "if": _if,
    "cond": _cond,
    "and": _and,
    "or": _or,
    "define": _define,
    "lambda": _lambda,
    "let": _let,
    "begin": _begin,
}
