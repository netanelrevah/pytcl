# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync --all-extras       # Install all dependencies
uv run pytest              # Run all tests
uv run pytest tests/test_commands.py::test_tcl_expression__substitute  # Run a single test
uv run ruff check .        # Lint
uv run mypy pytcl/         # Type check
```

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

## Code Style

- No comments or docstrings — ever. Don't restate what code does; extract instead.
- No nested `if` — use fast returns.
- DRY: extract to variables/functions/constants when it aids readability; don't extract the obvious.
- Imports at top of file only.
- Use `is`/direct evaluation instead of `== True`/`== False`.

## General

- Do not create example test files, do not create `.md` files to explain solutions.
- When changing something globally, work gradually — small steps without loading full context.
- Read `CLAUDE.local.md` if it exists for machine-specific context.

## Workflow

When the user corrects a workflow mistake (e.g., wrong command, missing `.gitignore` entries), save the correction here — CLAUDE.md is loaded every session and is the authoritative source for project rules.

## Unordered Notes
- when you want to run code to check if things work, don't do this, create a test cases instead and run pytest. This way you have a permanent record of the behavior and can easily rerun it in the future.
- when running command from root directory, NEVER run "cd && <command>" to change dir, just run the command.  
- when running command that need to change dir, first try to use command flags to specify the path.