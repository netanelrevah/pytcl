import pytest
from parametrization import Parametrization

from pytcl.errors import TCLSubstituteError
from pytcl.words import TCLBracesWord, TCLCommandWord, TCLDoubleQuotedWord, TCLScript, TCLVariableSubstitutionWord


def test_variable_substitution_word__get_empty__fail():
    instance = TCLVariableSubstitutionWord.read("abc")

    assert instance.variable_name == "abc"
    assert instance.origin == "abc"


@Parametrization.parameters("chars", "expected_value", "expected_substitute", "should_raise")
@Parametrization.default_parameters(should_raise=False)
@Parametrization.case("got dollar", "$", "$", "$")
@Parametrization.case("got two dollars", "$$", "$$", "$$")
@Parametrization.case("got dollar with space", "$ ", "$ ", "$ ")
@Parametrization.case("backslash newline", "a\\\nb", "a b", "a b")
@Parametrization.case("hex backslash", " $abc\n\\x20", " $abc\n\\x20", " 22\n ")
@Parametrization.case("complicated hex backslash", " $abc\n\\x2q", " $abc\n\\x2q", " 22\n\x02q")
@Parametrization.case("go two lines with subs", " $abc\nccc", " $abc\nccc", " 22\nccc")
@Parametrization.case("backslash cancel subs", "\\$abc", "\\$abc", "$abc")
@Parametrization.case("simple subs", "$abc", "$abc", "22")
@Parametrization.case("subs with prefix", "a$abc", "a$abc", "a22")
@Parametrization.case("subs with backslash", " $abc\n\\x20", " $abc\n\\x20", " 22\n ")
@Parametrization.case("wrapped subs", "aaa $abc bbb", "aaa $abc bbb", "aaa 22 bbb")
@Parametrization.case("simple error", "$abcd", "$abcd", 'can\'t read "abcd": no such variable', True)
@Parametrization.case("wrapped error", "aaa $abcd bbb", "aaa $abcd bbb", 'can\'t read "abcd": no such variable', True)
def test_double_quoted_word__substitute(chars, expected_value, expected_substitute, should_raise):
    instance = TCLDoubleQuotedWord.read(chars)

    assert instance.value == expected_value
    assert instance.origin == chars
    if should_raise:
        with pytest.raises(TCLSubstituteError, match=expected_substitute):
            instance.substitute(namespace={})
    else:
        assert instance.substitute(namespace={"abc": 22}) == expected_substitute


@Parametrization.parameters("cls", "code", "expected")
@Parametrization.case(
    "brace word with nested braces",
    TCLBracesWord,
    "tags {}",
    TCLBracesWord("tags {}"),
)
@Parametrization.case(
    "multiline brace word",
    TCLBracesWord,
    "proc helper {} {\nr flushall\n}\n",
    TCLBracesWord("proc helper {} {\nr flushall\n}\n"),
)
@Parametrization.case(
    "command with nested brace arg",
    TCLCommandWord,
    "start_server {tags {}}",
    TCLCommandWord("start_server", [TCLBracesWord("tags {}")]),
)
@Parametrization.case(
    "command with two brace args",
    TCLCommandWord,
    "start_server {tags {}} {\nproc helper {} {\nr flushall\n}\n}",
    TCLCommandWord("start_server", [TCLBracesWord("tags {}"), TCLBracesWord("proc helper {} {\nr flushall\n}\n")]),
)
@Parametrization.case(
    "script with command",
    TCLScript,
    "start_server {tags {}} {\nproc helper {} {\nr flushall\n}\n}",
    TCLScript(
        [TCLCommandWord("start_server", [TCLBracesWord("tags {}"), TCLBracesWord("proc helper {} {\nr flushall\n}\n")])]
    ),
)
@Parametrization.case(
    "brace arg",
    TCLScript,
    "tags {1 2 3}",
    TCLScript([TCLCommandWord("tags", [TCLBracesWord("1 2 3")])]),
)
def test_read(cls, code, expected):
    instance = cls.read(code)
    assert instance == expected
    assert instance.origin == code
