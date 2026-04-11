# Code Style

## General
- No comments or docstrings — ever. Don't restate what code does; extract instead.
- No nested `if` — use fast returns.
- DRY: extract to variables/functions/constants when it aids readability.
- Use `is`/direct evaluation instead of `== True`/`== False`.
- Line length: 120 characters.
- Target Python 3.11+.

## Imports
- Always start with `from __future__ import annotations`.
- Move imports only needed for type annotations into a `TYPE_CHECKING` block:
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from collections.abc import Callable
  ```

## Type Annotations
- Annotate every function parameter and return type.
- Use `|` union syntax, not `Union[...]`.
- Use lowercase generics: `dict[str, T]`, `list[T]`, `set[str]` — never `Dict`, `List`, `Set`.

## Indentation and Structure
- Maximum indentation depth: 3–4 levels. Deeply nested pyramids must be extracted.
- Use early `continue` in loops to avoid nesting, same as early `return` in functions.
- A method should read as a pipeline: each step is a call, not an inline block.

## Return Patterns
- Return `None` to signal failure; callers check `if x is None`.
- Use early `return None` to keep the happy path at the bottom — never `elif` after a `return`.

## Naming
- Classes: `PascalCase`. Functions/variables: `snake_case`. Module-private: `_underscore_prefix`.
- `match` statements preferred over chained `if/elif` for dispatch on string/type keys.