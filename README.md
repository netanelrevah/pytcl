# pytcl

Pure Python TCL interpreter and parser library.

## Installation

```bash
pip install pytcl
```

## Usage

### Interpreter

```python
from pytcl.interpreter import Interpreter

i = Interpreter()
i.substitute_string("set x 42")         # "42"
i.substitute_string("expr {$x * 2}")    # "84"
i.substitute_string("set x")            # "84"
```

Evaluate a `.tcl` file:

```python
from pathlib import Path
from pytcl.interpreter import Interpreter

i = Interpreter()
i.substitute_file(Path("script.tcl"))
```

### Custom commands

Commands are plain callables stored in the namespace:

```python
from pytcl.interpreter import Interpreter

i = Interpreter()
i.namespace["double"] = lambda args, ns: str(int(args[0]) * 2)
i.substitute_string("double 21")  # "42"
```

### Parser

Parse Tcl source into a typed tree without executing it:

```python
from pytcl.words import TCLScript

script = TCLScript.read(iter("set x [expr {1 + 2}]"))
for command in script.commands:
    print(command.name, command.args)
```

## Built-in commands

`set`, `unset`, `expr`, `if` / `elseif` / `else`, `while`, `foreach`, `proc`, `return`, `break`, `continue`, `incr`, `append`, `puts`, `error`

## Development

```bash
uv sync --all-extras        # install dependencies
uv run pytest               # unit tests
uv run pytest integrations/ # integration tests (requires Docker)
uv run ruff check .         # lint
uv run pre-commit run --all-files
```
