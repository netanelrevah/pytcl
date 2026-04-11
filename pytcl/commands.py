from __future__ import annotations

import operator
from dataclasses import dataclass
from functools import reduce
from itertools import chain
from typing import TYPE_CHECKING, Any, Literal, Self

from pytcl.errors import TCLBreakSignal, TCLContinueSignal, TCLInterpretationError, TCLReturnSignal, TCLSubstituteError
from pytcl.iterators import CharsIterator
from pytcl.types import TCLList
from pytcl.words import (
    TCLBracesWord,
    TCLBracketWord,
    TCLCommandArguments,
    TCLDoubleQuotedWord,
    TCLScript,
    TCLVariableSubstitutionWord,
    TCLWord,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence


@dataclass
class TCLCommandForEach:
    variables_names_and_values_lists: list[tuple[tuple[str, ...], TCLList]]
    body: TCLScript

    def substitute(self, namespace: dict[str, Any]) -> str:
        result = ""
        iterators = [
            zip(*[iter(tcl_list.words)] * len(names)) for names, tcl_list in self.variables_names_and_values_lists
        ]
        try:
            for value_groups in zip(*iterators):
                namespace.update(
                    {
                        name: value
                        for (names, _), values in zip(self.variables_names_and_values_lists, value_groups)
                        for name, value in zip(names, values)
                    }
                )
                try:
                    result = self.body.substitute(namespace)
                except TCLContinueSignal:
                    pass
        except TCLBreakSignal:
            pass
        return result

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        args_iterator = iter(arguments)

        variables_names_and_lists = []
        body: TCLScript | None = None
        while argument := next(args_iterator, None):
            values_list = next(args_iterator, None)

            if values_list is None:
                body = TCLScript.read(iter(argument.substitute(namespace)))
                break

            names_list = tuple(TCLList.build(argument, namespace).words)

            variables_names_and_lists.append((names_list, TCLList.build(values_list, namespace)))

        if not variables_names_and_lists or not body:
            raise ValueError()

        return cls(variables_names_and_lists, body)


@dataclass
class TCLCommandIf:
    if_part: tuple[TCLExpression, TCLScript]
    elseif_parts: list[tuple[TCLExpression, TCLScript]]
    else_part: TCLScript | None

    def substitute(self, namespace: dict[str, Any]) -> str:
        condition, body = self.if_part
        if condition.substitute(namespace) != "0":
            return body.substitute(namespace)
        for condition, body in self.elseif_parts:
            if condition.substitute(namespace) != "0":
                return body.substitute(namespace)
        if self.else_part is not None:
            return self.else_part.substitute(namespace)
        return ""

    @classmethod
    def _read_if(
        cls, args_iterator: Iterator[TCLCommandArguments], namespace: dict[str, Any]
    ) -> tuple[TCLExpression, TCLScript]:
        expression_word = next(args_iterator)
        expression = TCLExpression.build([expression_word], namespace)
        body = next(args_iterator)
        if body.substitute(namespace) == "then":
            body = next(args_iterator)
        return expression, TCLScript.read(body.substitute_iterator(namespace))

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        args_iterator: Iterator[TCLCommandArguments] = chain([TCLWord("if")], arguments)

        if_part: tuple[TCLExpression, TCLScript] | None = None
        elseif_parts: list[tuple[TCLExpression, TCLScript]] = []
        else_part: TCLScript | None = None

        while argument := next(args_iterator, None):
            match argument.substitute(namespace):
                case "if":
                    if_part = cls._read_if(args_iterator, namespace)
                case "elseif":
                    elseif_parts.append(cls._read_if(args_iterator, namespace))
                case "else":
                    else_part = TCLScript.read(next(args_iterator).substitute_iterator(namespace))
                case _:
                    raise ValueError()

        if if_part is None:
            raise ValueError()

        return cls(if_part, elseif_parts, else_part)


@dataclass
class TCLCommandSet:
    name: str
    value: TCLCommandArguments | None

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        if not arguments:
            raise ValueError("set requires at least one argument")
        name = arguments[0].substitute(namespace)
        value = arguments[1] if len(arguments) > 1 else None
        return cls(name, value)

    def substitute(self, namespace: dict[str, Any]) -> str:
        if self.value is None:
            if self.name not in namespace:
                raise TCLSubstituteError(f'can\'t read "{self.name}": no such variable')
            return str(namespace[self.name])
        val = self.value.substitute(namespace)
        namespace[self.name] = val
        return val


@dataclass
class TCLCommandCatch:
    body: TCLScript
    var_name: str | None

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        if not arguments:
            raise ValueError()
        body = TCLScript.read(arguments[0].substitute_iterator(namespace))
        var_name = arguments[1].substitute(namespace) if len(arguments) > 1 else None
        return cls(body, var_name)

    def substitute(self, namespace: dict[str, Any]) -> str:
        try:
            result = self.body.substitute(namespace)
            if self.var_name is not None:
                namespace[self.var_name] = result
            return "0"
        except Exception as e:
            if self.var_name is not None:
                namespace[self.var_name] = str(e)
            return "1"


@dataclass
class TCLCommandFor:
    ARGUMENT_COUNT = 4

    init: TCLScript
    condition: TCLExpression
    step: TCLScript
    body: TCLScript

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        if len(arguments) < cls.ARGUMENT_COUNT:
            raise ValueError()
        init = TCLScript.read(arguments[0].substitute_iterator(namespace))
        condition = TCLExpression.build([arguments[1]], namespace)
        step = TCLScript.read(arguments[2].substitute_iterator(namespace))
        body = TCLScript.read(arguments[3].substitute_iterator(namespace))
        return cls(init, condition, step, body)

    def substitute(self, namespace: dict[str, Any]) -> str:
        self.init.substitute(namespace)
        try:
            while self.condition.substitute(namespace) != "0":
                try:
                    self.body.substitute(namespace)
                except TCLContinueSignal:
                    pass
                self.step.substitute(namespace)
        except TCLBreakSignal:
            pass
        return ""


@dataclass
class TCLCommandReturn:
    value: TCLCommandArguments | None

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        return cls(arguments[0] if arguments else None)

    def substitute(self, namespace: dict[str, Any]) -> str:
        raise TCLReturnSignal(self.value.substitute(namespace) if self.value else "")


TCLMathOperandType = str | TCLCommandArguments


@dataclass
class ExpressionOperator:
    operator_func: Callable[..., int | float | bool | tuple]
    representation: str
    precedence: int
    number_of_operands: int | None = None
    associativity: Literal["R", "L"] = "L"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ExpressionOperator):
            raise ValueError()
        return self.precedence < other.precedence

    @classmethod
    def _parse_operand(cls, operand: TCLMathOperandType, namespace: dict[str, Any]) -> int | float | str:
        if isinstance(operand, TCLCommandArguments):
            operand = operand.substitute(namespace)
        try:
            return int(operand)
        except ValueError:
            try:
                return float(operand)
            except ValueError:
                return operand

    def apply(self, *operands: TCLMathOperandType, namespace: dict[str, Any]) -> str:
        result = reduce(self.operator_func, map(lambda x: self._parse_operand(x, namespace), operands))
        if isinstance(result, bool):
            return "1" if result else "0"
        return str(result)


EXPRESSION_OPERATOR = {
    expression_operator.representation: expression_operator
    for expression_operator in [
        ExpressionOperator(operator.not_, "!", 6, 1, "R"),
        ExpressionOperator(operator.inv, "~", 6, 1, "R"),
        ExpressionOperator(operator.sub, "-", 1),
        ExpressionOperator(operator.add, "+", 1),
        ExpressionOperator(operator.pow, "**", 3, associativity="R"),
        ExpressionOperator(operator.lshift, "<<", 5, number_of_operands=2),
        ExpressionOperator(operator.rshift, ">>", 5, number_of_operands=2),
        ExpressionOperator(operator.or_, "|", 4),
        ExpressionOperator(operator.and_, "&", 4),
        ExpressionOperator(operator.xor, "^", 4),
        ExpressionOperator(operator.eq, "==", 0),
        ExpressionOperator(operator.ne, "!=", 0),
        ExpressionOperator(operator.eq, "eq", 0),
        ExpressionOperator(operator.ne, "ne", 0),
        ExpressionOperator(operator.lt, "<", 0),
        ExpressionOperator(operator.gt, ">", 0),
        ExpressionOperator(operator.le, "<=", 0),
        ExpressionOperator(operator.ge, ">=", 0),
        ExpressionOperator(operator.mul, "*", 2),
        ExpressionOperator(operator.truediv, "/", 2),
        ExpressionOperator(operator.mod, "%", 2),
        ExpressionOperator(lambda *operands: any(operands), "||", -1),
        ExpressionOperator(lambda *operands: all(operands), "&&", -2),
        ExpressionOperator(lambda x, y: (x, y), ":", -3),
        ExpressionOperator(lambda x, y: y[0] if x else y[1], "?", -4),
    ]
}


@dataclass
class TCLExpression:
    postfix: list[str | TCLCommandArguments]

    @classmethod
    def _iterate_expression(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Iterator[str]:
        for argument in arguments[:-1]:
            yield from argument.substitute_iterator(namespace)
            yield from " "
        yield from arguments[-1].substitute_iterator(namespace)

    @classmethod
    def _read_operator(cls, chars: CharsIterator) -> str:
        chars.push()

        value = ""
        while char := next(chars, None):
            if value + char not in EXPRESSION_OPERATOR:
                chars.push_back()
                break
            value += char

        chars.pop()
        return value

    @classmethod
    def _read_value(cls, chars: CharsIterator) -> str:
        chars.push()

        value = ""
        while char := next(chars, None):
            match char:
                case " " | "\t" | "\n":
                    chars.drop_last()
                    break
                case "*" | "<":
                    chars.push_back()
                    break
                case _:
                    value += char

        chars.pop()
        return value

    @classmethod
    def _iterate_tokens(cls, chars: Iterator[str]) -> Iterator[str | TCLCommandArguments]:
        iterator = CharsIterator.of(chars)
        iterator.push()

        while char := next(iterator, None):
            match char:
                case " " | "\t" | "\n":
                    continue
                case '"':
                    yield TCLDoubleQuotedWord.read(iterator)
                case "$":
                    yield TCLVariableSubstitutionWord.read(iterator)
                case "{":
                    yield TCLBracesWord.read(iterator)
                case "[":
                    yield TCLBracketWord.read(iterator)
                case "*" | "<":
                    iterator.unget(char)
                    yield cls._read_operator(iterator)
                case _:
                    iterator.unget(char)
                    yield cls._read_value(iterator)

    @classmethod
    def build(cls, arguments: Sequence[TCLCommandArguments], namespace: dict[str, Any]) -> Self:
        expression_iterator = cls._iterate_expression(arguments, namespace)
        tokens_iterator = cls._iterate_tokens(expression_iterator)

        operators_stack: list[str] = []
        postfix: list[str | TCLCommandArguments] = []
        while token := next(tokens_iterator, None):
            if isinstance(token, str) and (expression_operator := EXPRESSION_OPERATOR.get(token)):
                while operators_stack:
                    if not (top_operator := EXPRESSION_OPERATOR.get(operators_stack[-1])):
                        break
                    if (
                        expression_operator.associativity == "L"
                        and expression_operator.precedence > top_operator.precedence
                    ):
                        break
                    if (
                        expression_operator.associativity == "R"
                        and expression_operator.precedence >= top_operator.precedence
                    ):
                        break
                    postfix.append(operators_stack.pop())
                operators_stack.append(token)
            elif isinstance(token, str) and token == "(":
                operators_stack.append(token)
            elif isinstance(token, str) and token == ")":
                while operators_stack:
                    operator_string = operators_stack.pop()
                    if operator_string == "(":
                        break
                    postfix.append(operator_string)
            else:
                postfix.append(token)

        while operators_stack:
            postfix.append(operators_stack.pop())

        return cls(postfix)

    def substitute(self, namespace: dict[str, Any]) -> str:
        postfix = list(self.postfix)
        commands_stack: list[TCLMathOperandType] = []
        while postfix:
            token = postfix.pop(0)

            if isinstance(token, str) and (expression_operator := EXPRESSION_OPERATOR.get(token, None)) is not None:
                operands = [commands_stack.pop() for _ in range(expression_operator.number_of_operands or 2)]
                commands_stack.append(expression_operator.apply(*reversed(operands), namespace=namespace))
                continue

            commands_stack.append(token)

        if len(commands_stack) != 1:
            raise TCLInterpretationError()

        result = commands_stack[0]
        if isinstance(result, str):
            return result
        return result.substitute(namespace)
