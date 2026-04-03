import pytest
from parametrization import Parametrization

from pytcl.errors import TCLSubstituteError
from pytcl.interpreter import Interpreter


def run(code: str) -> str:
    return Interpreter().substitute_string(code)


@Parametrization.parameters("code", "expected")
@Parametrization.case("set and get", "set x 42; set x", "42")
@Parametrization.case("set returns value", "set x hello", "hello")
@Parametrization.case("expr addition", "expr {3 + 4}", "7")
@Parametrization.case("expr with var", "set x 3; expr {$x * 2}", "6")
@Parametrization.case("bracket substitution", "set x [expr {2 + 3}]", "5")
@Parametrization.case("if true", "if {1} {set x yes}", "yes")
@Parametrization.case("if false else", "if {0} {set x yes} else {set x no}", "no")
@Parametrization.case("if elseif", "set x 2; if {$x == 1} {set r a} elseif {$x == 2} {set r b} else {set r c}", "b")
@Parametrization.case("while loop", "set i 0; while {$i < 3} {incr i}; set i", "3")
@Parametrization.case("foreach single", "set s 0; foreach x {1 2 3} {incr s $x}; set s", "6")
@Parametrization.case(
    "foreach multi-var", "set s 0; foreach {a b} {1 2 3 4} {set s [expr {$s + $a + $b}]}; set s", "10"
)
@Parametrization.case("proc call", "proc double {x} {expr {$x * 2}}; double 5", "10")
@Parametrization.case("proc return", 'proc greet {name} {return "hi $name"}; greet world', "hi world")
@Parametrization.case(
    "proc recursive",
    "proc fact {n} {if {$n <= 1} {return 1} else {return [expr {$n * [fact [expr {$n - 1}]]}]}}; fact 5",
    "120",
)
@Parametrization.case("break in while", "set i 0; while {1} {incr i; if {$i == 3} {break}}; set i", "3")
@Parametrization.case(
    "continue in while", "set s 0; set i 0; while {$i < 5} {incr i; if {$i == 3} {continue}; incr s}; set s", "4"
)
@Parametrization.case("incr default", "set x 0; incr x; set x", "1")
@Parametrization.case("incr by amount", "set x 10; incr x -3; set x", "7")
@Parametrization.case("append", "set s hello; append s { } world; set s", "hello world")
def test_interpreter(code, expected):
    assert run(code) == expected


def test_unset_variable():
    i = Interpreter()
    i.substitute_string("set x 1")
    i.substitute_string("unset x")
    with pytest.raises(TCLSubstituteError):
        i.substitute_string("set x")


def test_error_command():
    with pytest.raises(TCLSubstituteError, match="something went wrong"):
        run("error {something went wrong}")
