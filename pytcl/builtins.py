from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from pytcl.commands import TCLCommandForEach, TCLCommandIf, TCLExpression
from pytcl.errors import TCLBreakSignal, TCLContinueSignal, TCLReturnSignal, TCLSubstituteError
from pytcl.words import TCLScript, TCLWord


def _cmd_set(args: list[str], namespace: dict[str, Any]) -> str:
    if len(args) == 1:
        name = args[0]
        if name not in namespace:
            raise TCLSubstituteError(f'can\'t read "{name}": no such variable')
        return str(namespace[name])
    namespace[args[0]] = args[1]
    return args[1]


def _cmd_puts(args: list[str], namespace: dict[str, Any]) -> str:
    newline = True
    text = args[-1]
    if args[0] == "-nonewline":
        newline = False
    print(text, end="\n" if newline else "")
    return ""


def _cmd_expr(args: list[str], namespace: dict[str, Any]) -> str:
    return TCLExpression.build([TCLWord(" ".join(args))], namespace).substitute(namespace)


def _cmd_if(args: list[str], namespace: dict[str, Any]) -> str:
    raw_args = [TCLWord(a) for a in args]
    return TCLCommandIf.build(raw_args, namespace).substitute(namespace)


def _cmd_while(args: list[str], namespace: dict[str, Any]) -> str:
    cond_str, body_str = args[0], args[1]
    result = ""
    while True:
        if TCLExpression.build([TCLWord(cond_str)], namespace).substitute(namespace) == "0":
            break
        try:
            result = TCLScript.read(iter(body_str)).substitute(namespace)
        except TCLBreakSignal:
            break
        except TCLContinueSignal:
            pass
    return result


def _cmd_foreach(args: list[str], namespace: dict[str, Any]) -> str:
    raw_args = [TCLWord(a) for a in args]
    return TCLCommandForEach.build(raw_args, namespace).substitute(namespace)


def _cmd_proc(args: list[str], namespace: dict[str, Any]) -> str:
    name, params_str, body_str = args[0], args[1], args[2]
    params = params_str.split() if params_str.strip() else []
    namespace[name] = TCLProcedure(params, body_str)
    return ""


def _cmd_return(args: list[str], namespace: dict[str, Any]) -> str:
    raise TCLReturnSignal(args[0] if args else "")


def _cmd_break(args: list[str], namespace: dict[str, Any]) -> str:
    raise TCLBreakSignal()


def _cmd_continue(args: list[str], namespace: dict[str, Any]) -> str:
    raise TCLContinueSignal()


def _cmd_incr(args: list[str], namespace: dict[str, Any]) -> str:
    name = args[0]
    increment = int(args[1]) if len(args) > 1 else 1
    value = int(namespace.get(name, 0)) + increment
    namespace[name] = str(value)
    return str(value)


def _cmd_append(args: list[str], namespace: dict[str, Any]) -> str:
    name = args[0]
    value = str(namespace.get(name, "")) + "".join(args[1:])
    namespace[name] = value
    return value


def _cmd_error(args: list[str], namespace: dict[str, Any]) -> str:
    raise TCLSubstituteError(args[0] if args else "")


def _cmd_unset(args: list[str], namespace: dict[str, Any]) -> str:
    for name in args:
        namespace.pop(name, None)
    return ""


@dataclass
class TCLProcedure:
    params: list[str]
    body: str

    def __call__(self, args: list[str], namespace: dict[str, Any]) -> str:
        local_ns: dict[str, Any] = {k: v for k, v in namespace.items() if callable(v)}
        for i, param in enumerate(self.params):
            if param == "args":
                local_ns["args"] = " ".join(args[i:])
                break
            if i < len(args):
                local_ns[param] = args[i]
        try:
            return TCLScript.read(iter(self.body)).substitute(local_ns)
        except TCLReturnSignal as e:
            return e.value


def register_builtins(namespace: dict[str, Any]) -> None:
    namespace.update(
        {
            "set": _cmd_set,
            "puts": _cmd_puts,
            "expr": _cmd_expr,
            "if": _cmd_if,
            "while": _cmd_while,
            "foreach": _cmd_foreach,
            "proc": _cmd_proc,
            "return": _cmd_return,
            "break": _cmd_break,
            "continue": _cmd_continue,
            "incr": _cmd_incr,
            "append": _cmd_append,
            "error": _cmd_error,
            "unset": _cmd_unset,
        }
    )


_ = sys  # suppress unused import (reserved for future channel support in puts)
