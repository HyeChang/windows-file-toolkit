from collections.abc import Iterable
from pathlib import Path

from file_compressor.formats import is_supported_file


def discover_supported_files(source_root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in source_root.rglob("*")
            if path.is_file() and is_supported_file(path)
        ),
        key=_path_sort_key,
    )


def expand_source_paths(paths: Iterable[Path]) -> list[Path]:
    discovered: list[Path] = []
    for path in paths:
        if path.is_dir():
            discovered.extend(discover_supported_files(path))
        elif path.is_file() and is_supported_file(path):
            discovered.append(path)
    return sorted(discovered, key=_path_sort_key)


def _path_sort_key(path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in path.parts)
