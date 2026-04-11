# Contributing

## Architecture

pytcl is a pure Python TCL interpreter. Parsing and evaluation are interleaved — there is no separate AST phase. Everything flows through a `namespace: dict[str, Any]` that acts as the variable/command scope.

### Parsing layer (`pytcl/words.py`)

All word types inherit from `TCLWordBase` and implement two methods:
- `_read(chars: CharsIterator) -> Self` — consumes characters and builds the word
- `substitute_iterator(namespace) -> Iterator[str]` — lazily evaluates/substitutes

Word types and when they're produced:
- `TCLWord` — bare word (no delimiters)
- `TCLDoubleQuotedWord` — `"..."`, supports `$var` and `\escape` substitution inside
- `TCLBracesWord` — `{...}`, no substitution (literal)
- `TCLBracketWord` — `[...]`, evaluates enclosed script and substitutes result
- `TCLVariableSubstitutionWord` — `$varname`, looks up variable in namespace
- `TCLCommandWord` — a single command: name + list of the above argument types
- `TCLScript` — a sequence of `TCLCommandWord`s

The `@tcl_word` decorator wraps a class with `@dataclass` and injects an `origin: str` field that stores the raw source text.

`CharsIterator` (`pytcl/iterators.py`) wraps any character iterator with push/pop accumulators (used to capture `origin`) and `push_back`/`drop_last` for one-character lookahead.

### Evaluation layer (`pytcl/commands.py`)

Commands are represented as `TCLCommandBase` subclasses with `interpertize(arguments, namespace)` (parses args) and `execute(namespace)` (runs).

`TCLExpression` implements a shunting-yard algorithm to parse infix expressions into postfix, then evaluates them. Operators are defined in `EXPRESSION_OPERATOR` as `ExpressionOperator` instances with precedence and associativity.

`TCLList` (`pytcl/types.py`) handles TCL list parsing, reusing the same word-type dispatch as the main parser.

### Entry point

`pytcl/files.py` exposes `read_tcl_file(path) -> TCLScript` for reading `.tcl` files. `TCLScript.read_text_io` / `TCLScript.read` are the main parse entry points.

### Testing

Tests use `pytest-parametrization` (`@Parametrization.case`). The namespace `{"abc": 22}` is the conventional test namespace.

## Workflow

**Always run pre-commit before committing and fix all failures before proceeding:**

```bash
uv run pre-commit run --all-files
```

Only commit once all hooks pass.

## Code Style

See [CODE_STYLE.md](CODE_STYLE.md).
