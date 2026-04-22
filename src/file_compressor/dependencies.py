from dataclasses import dataclass
from shutil import which as default_which
from typing import Callable


@dataclass(frozen=True)
class DependencyStatus:
    available: bool
    executable: str | None = None


def detect_ghostscript(which: Callable[[str], str | None] = default_which) -> DependencyStatus:
    executable = which("gswin64c") or which("gswin32c") or which("gs")
    return DependencyStatus(available=executable is not None, executable=executable)
