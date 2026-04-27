from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader, PdfWriter


@dataclass(frozen=True)
class PdfOperationResult:
    status: str
    output: Path | None = None
    outputs: list[Path] = field(default_factory=list)
    message: str = ""


def parse_page_selection(selection: str, *, total_pages: int) -> list[int]:
    pages: list[int] = []
    for token in selection.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise ValueError("Page range start must be before end.")
            pages.extend(range(start - 1, end))
        else:
            pages.append(int(token) - 1)

    for index in pages:
        if index < 0 or index >= total_pages:
            raise ValueError("Page selection is outside the PDF page range.")
    return pages


def merge_pdfs(sources: list[Path], output: Path) -> PdfOperationResult:
    try:
        output = _unique_output_path(Path(output))
        writer = PdfWriter()
        for source in sources:
            reader = PdfReader(str(source))
            for page in reader.pages:
                writer.add_page(page)
        _write_pdf(writer, output)
    except Exception as exc:
        return PdfOperationResult(status="failed", output=None, message=str(exc))
    return PdfOperationResult(status="completed", output=output)


def split_pdf(source: Path, output_dir: Path) -> PdfOperationResult:
    try:
        source = Path(source)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        reader = PdfReader(str(source))
        outputs: list[Path] = []
        for index, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            output = _unique_output_path(output_dir / f"{source.stem}_page_{index:03d}.pdf")
            _write_pdf(writer, output)
            outputs.append(output)
    except Exception as exc:
        return PdfOperationResult(status="failed", outputs=[], message=str(exc))
    return PdfOperationResult(status="completed", outputs=outputs)


def extract_pages(source: Path, output: Path, selection: str) -> PdfOperationResult:
    return _write_selected_pages(source, output, parse_mode="include", selection=selection)


def delete_pages(source: Path, output: Path, selection: str) -> PdfOperationResult:
    return _write_selected_pages(source, output, parse_mode="exclude", selection=selection)


def rotate_pages(source: Path, output: Path, selection: str, angle: int) -> PdfOperationResult:
    try:
        reader = PdfReader(str(source))
        selected = set(parse_page_selection(selection, total_pages=len(reader.pages)))
        writer = PdfWriter()
        for index, page in enumerate(reader.pages):
            if index in selected:
                page = page.rotate(angle)
            writer.add_page(page)
        output = _unique_output_path(Path(output))
        _write_pdf(writer, output)
    except Exception as exc:
        return PdfOperationResult(status="failed", output=None, message=str(exc))
    return PdfOperationResult(status="completed", output=output)


def reorder_pages(source: Path, output: Path, order: str) -> PdfOperationResult:
    try:
        reader = PdfReader(str(source))
        selected = parse_page_selection(order, total_pages=len(reader.pages))
        writer = PdfWriter()
        for index in selected:
            writer.add_page(reader.pages[index])
        output = _unique_output_path(Path(output))
        _write_pdf(writer, output)
    except Exception as exc:
        return PdfOperationResult(status="failed", output=None, message=str(exc))
    return PdfOperationResult(status="completed", output=output)


def _write_selected_pages(source: Path, output: Path, *, parse_mode: str, selection: str) -> PdfOperationResult:
    try:
        reader = PdfReader(str(source))
        selected = set(parse_page_selection(selection, total_pages=len(reader.pages)))
        writer = PdfWriter()
        for index, page in enumerate(reader.pages):
            should_include = index in selected
            if parse_mode == "exclude":
                should_include = not should_include
            if should_include:
                writer.add_page(page)
        output = _unique_output_path(Path(output))
        _write_pdf(writer, output)
    except Exception as exc:
        return PdfOperationResult(status="failed", output=None, message=str(exc))
    return PdfOperationResult(status="completed", output=output)


def _write_pdf(writer: PdfWriter, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)


def _unique_output_path(path: Path) -> Path:
    candidate = path
    counter = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        counter += 1
    return candidate
