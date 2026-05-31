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


@dataclass(frozen=True)
class PdfPagePlan:
    source: Path
    page_index: int
    page_number: int
    result_order: int
    action: str
    rotation: int = 0
    output: Path | None = None


PdfPageRef = PdfPagePlan


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


def pdf_page_refs(source: Path) -> list[PdfPageRef]:
    source = Path(source)
    reader = PdfReader(str(source))
    return [
        PdfPagePlan(
            source=source,
            page_index=index,
            page_number=index + 1,
            result_order=index + 1,
            action="include",
        )
        for index in range(len(reader.pages))
    ]


def default_merge_plan(sources: list[Path]) -> list[PdfPagePlan]:
    plan: list[PdfPagePlan] = []
    order = 1
    for source in sources[:2]:
        for page in pdf_page_refs(source):
            plan.append(
                PdfPagePlan(
                    source=page.source,
                    page_index=page.page_index,
                    page_number=page.page_number,
                    result_order=order,
                    action="include",
                    rotation=page.rotation,
                    output=page.output,
                )
            )
            order += 1
    return plan


def write_page_plan(plan: list[PdfPagePlan], output: Path) -> PdfOperationResult:
    try:
        output = _unique_output_path(Path(output))
        writer = PdfWriter()
        reader_cache: dict[Path, PdfReader] = {}
        for row in plan:
            if row.action in {"exclude", "delete"}:
                continue
            reader = reader_cache.setdefault(row.source, PdfReader(str(row.source)))
            page = reader.pages[row.page_index]
            if row.rotation:
                page = page.rotate(row.rotation)
            writer.add_page(page)
        _write_pdf(writer, output)
    except Exception as exc:
        return PdfOperationResult(status="failed", output=None, message=str(exc))
    return PdfOperationResult(status="completed", output=output)


def build_single_pdf_plan(
    source: Path,
    operation: str,
    selection: str,
    output: Path,
    *,
    rotation: int = 0,
) -> list[PdfPagePlan]:
    source = Path(source)
    output = Path(output)
    reader = PdfReader(str(source))
    total_pages = len(reader.pages)

    if operation == "reorder":
        selected = parse_page_selection(selection, total_pages=total_pages)
        return [
            PdfPagePlan(
                source=source,
                page_index=page_index,
                page_number=page_index + 1,
                result_order=index,
                action="include",
                output=output,
            )
            for index, page_index in enumerate(selected, start=1)
        ]

    selected = set(parse_page_selection(selection, total_pages=total_pages)) if selection.strip() else set()
    plan: list[PdfPagePlan] = []
    for page_index in range(total_pages):
        action = "include"
        row_rotation = 0
        row_output = output
        if operation == "extract":
            action = "include" if page_index in selected else "exclude"
        elif operation == "delete":
            action = "delete" if page_index in selected else "keep"
        elif operation == "split":
            action = "split"
            row_output = output / f"{source.stem}_page_{page_index + 1:03d}.pdf"
        elif operation == "rotate":
            action = "rotate" if page_index in selected else "keep"
            row_rotation = rotation if page_index in selected else 0

        plan.append(
            PdfPagePlan(
                source=source,
                page_index=page_index,
                page_number=page_index + 1,
                result_order=len(plan) + 1,
                action=action,
                rotation=row_rotation,
                output=row_output,
            )
        )
    return plan


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
