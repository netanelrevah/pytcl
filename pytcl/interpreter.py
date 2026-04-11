from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytcl.builtins import register_builtins
from pytcl.words import TCLScript

if TYPE_CHECKING:
    from pathlib import Path


class Interpreter:
    def __init__(self) -> None:
        self.namespace: dict[str, Any] = {}
        register_builtins(self.namespace)

    def substitute(self, script: TCLScript) -> str:
        return script.substitute(self.namespace)

    def substitute_string(self, code: str) -> str:
        return self.substitute(TCLScript.read(iter(code)))

    def substitute_file(self, path: Path) -> str:
        with open(path) as f:
            return self.substitute(TCLScript.read_text_io(f))
