"""Lexical environments for mini-Scheme."""

from __future__ import annotations

from typing import Any


class Environment:
    def __init__(self, parent: Environment | None = None):
        self.parent = parent
        self.bindings: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> Any:
        self.bindings[name] = value
        return value

    def lookup(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise NameError(f"unknown identifier: {name}")
