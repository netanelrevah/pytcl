from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, Self

from pytcl.words import TCLBracesWord, TCLBracketWord, TCLDoubleQuotedWord, TCLVariableSubstitutionWord, TCLWord

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class TCLList:
    words: list[str]

    def __str__(self) -> str:
        return "{" + ",".join([str(w) for w in self.words]) + "}"

    @classmethod
    def words_iterator(
        cls,
        chars: Iterator[str],
        namespace: dict[str, Any],
    ) -> Iterator[str]:
        while char := next(chars, None):
            match char:
                case '"':
                    yield TCLDoubleQuotedWord.read(chars).substitute(namespace)
                case "{":
                    yield TCLBracesWord.read(chars).substitute(namespace)
                case "[":
                    yield TCLBracketWord.read(chars).substitute(namespace)
                case "}" | "]":
                    raise ValueError()
                case " " | "\t" | "\n":
                    continue
                case _:
                    yield TCLWord.read(chain([char], chars)).substitute(namespace)

    @classmethod
    def interpertize(
        cls,
        list_word: TCLWord | TCLDoubleQuotedWord | TCLBracesWord | TCLBracketWord | TCLVariableSubstitutionWord,
        namespace: dict[str, Any],
    ) -> Self:
        if isinstance(list_word, TCLWord | TCLBracesWord):
            return cls(list(cls.words_iterator(iter(list_word.value), namespace)))
        if isinstance(list_word, TCLBracketWord | TCLDoubleQuotedWord | TCLVariableSubstitutionWord):
            return cls(list(cls.words_iterator(list_word.substitute_iterator(namespace), namespace)))
        raise TypeError()
