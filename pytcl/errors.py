from __future__ import annotations


class TCLInterpretationError(Exception):
    pass


class TCLSubstituteError(Exception):
    pass


class TCLReadError(Exception):
    pass


class TCLReturnSignal(Exception):  # noqa: N818
    def __init__(self, value: str = "") -> None:
        self.value = value


class TCLBreakSignal(Exception):  # noqa: N818
    pass


class TCLContinueSignal(Exception):  # noqa: N818
    pass
