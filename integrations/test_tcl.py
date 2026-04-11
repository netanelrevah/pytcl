from parametrization import Parametrization

from pytcl.interpreter import Interpreter


def run(code: str) -> str:
    return Interpreter().substitute_string(code)


@Parametrization.parameters("code")
@Parametrization.case("set and get", "set x 42; set x")
@Parametrization.case("set returns value", "set x hello")
@Parametrization.case("expr addition", "expr {3 + 4}")
@Parametrization.case("expr with var", "set x 3; expr {$x * 2}")
@Parametrization.case("bracket substitution", "set x [expr {2 + 3}]")
@Parametrization.case("if true", "if {1} {set x yes}")
@Parametrization.case("if false else", "if {0} {set x yes} else {set x no}")
@Parametrization.case("if elseif", "set x 2; if {$x == 1} {set r a} elseif {$x == 2} {set r b} else {set r c}")
@Parametrization.case("while loop", "set i 0; while {$i < 3} {incr i}; set i")
@Parametrization.case("foreach single", "set s 0; foreach x {1 2 3} {incr s $x}; set s")
@Parametrization.case("foreach multi-var", "set s 0; foreach {a b} {1 2 3 4} {set s [expr {$s + $a + $b}]}; set s")
@Parametrization.case("proc call", "proc double {x} {expr {$x * 2}}; double 5")
@Parametrization.case("proc return", 'proc greet {name} {return "hi $name"}; greet world')
@Parametrization.case(
    "proc recursive",
    "proc fact {n} {if {$n <= 1} {return 1} else {return [expr {$n * [fact [expr {$n - 1}]]}]}}; fact 5",
)
@Parametrization.case("break in while", "set i 0; while {1} {incr i; if {$i == 3} {break}}; set i")
@Parametrization.case(
    "continue in while", "set s 0; set i 0; while {$i < 5} {incr i; if {$i == 3} {continue}; incr s}; set s"
)
@Parametrization.case("incr default", "set x 0; incr x; set x")
@Parametrization.case("incr by amount", "set x 10; incr x -3; set x")
@Parametrization.case("append", "set s hello; append s { } world; set s")
def test_against_tclsh(code, tclsh):
    assert run(code) == tclsh(code)
