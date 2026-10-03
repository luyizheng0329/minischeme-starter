"""Command-line entry point for the mini-Scheme interpreter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from scheme_builtins import install_builtins
from environment import Environment
from evaluator import evaluate
from parser import parse_program
from runtime import scheme_str


def run_sources(sources: Iterable[str]) -> None:
    environment = Environment()
    install_builtins(environment)
    for source in sources:
        for expression in parse_program(source):
            result = evaluate(expression, environment)
            if result is not None:
                print(scheme_str(result))


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments:
        sources = (Path(path).read_text(encoding="utf-8") for path in arguments)
    else:
        sources = (sys.stdin.read(),)
    run_sources(sources)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
