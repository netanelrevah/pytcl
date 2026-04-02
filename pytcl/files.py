from __future__ import annotations

from typing import TYPE_CHECKING

from pytcl.words import TCLScript

if TYPE_CHECKING:
    from pathlib import Path


def read_tcl_file(source_file_path: Path) -> TCLScript:
    with open(source_file_path) as source_file:
        return TCLScript.read_text_io(source_file)
