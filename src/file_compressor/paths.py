from pathlib import Path


def compressed_output_path(source: Path) -> Path:
    base = source.with_name(f"{source.stem}_compressed{source.suffix}")
    if not base.exists():
        return base

    counter = 2
    while True:
        candidate = source.with_name(f"{source.stem}_compressed_{counter}{source.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
