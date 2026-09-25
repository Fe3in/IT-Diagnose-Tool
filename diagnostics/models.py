"""Shared data model for diagnostic check results."""
from enum import Enum


class Status(Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    INFO = "INFO"


SYMBOLS = {
    Status.PASS: "\u2714",     # ✔
    Status.WARNING: "\u26A0",  # ⚠
    Status.FAIL: "\u2718",     # ✘
    Status.INFO: "\u2139",     # ℹ
}


class DiagnosticResult:
    """A single check's outcome. A module returns a list of these."""

    def __init__(self, check_name: str, status: Status, message: str, details: str = ""):
        self.check_name = check_name
        self.status = status
        self.message = message
        self.details = details or ""

    @property
    def symbol(self) -> str:
        return SYMBOLS.get(self.status, "?")
