from collections.abc import Callable
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


Transform = Callable[[str, bytes], bytes]


def _temporary_output_path(output: Path) -> Path:
    candidate = output.with_name(f"{output.name}.tmp")
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = output.with_name(f"{output.name}.{counter}.tmp")
        if not candidate.exists():
            return candidate
        counter += 1


def rewrite_zip_package(source: Path, output: Path, transform: Transform) -> None:
    temporary = _temporary_output_path(output)
    try:
        with ZipFile(source, "r") as input_archive, ZipFile(
            temporary, "w", ZIP_DEFLATED, compresslevel=9
        ) as output_archive:
            for info in input_archive.infolist():
                data = input_archive.read(info.filename)
                transformed = transform(info.filename, data)
                new_info = ZipInfo(filename=info.filename, date_time=info.date_time)
                new_info.external_attr = info.external_attr
                new_info.comment = info.comment
                new_info.extra = info.extra
                output_archive.writestr(new_info, transformed, compress_type=ZIP_DEFLATED)
        temporary.replace(output)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
