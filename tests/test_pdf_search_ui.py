from pathlib import Path
import shutil

from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter

from file_compressor.dependencies import DependencyStatus, TESSERACT_DOWNLOAD_URL
from file_compressor_app.ui import MainWindow


def app() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication([])


def case_dir(name: str) -> Path:
    path = Path(".worktrees/file-compressor-impl/.test-output") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def write_pdf(path: Path, page_count: int):
    writer = PdfWriter()
    for index in range(page_count):
        writer.add_blank_page(width=200 + index, height=300 + index)
    with path.open("wb") as output:
        writer.write(output)


def make_window(monkeypatch, *, tesseract_available=False) -> MainWindow:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr(
        "file_compressor_app.ui.detect_ghostscript",
        lambda: DependencyStatus(False),
    )
    monkeypatch.setattr("file_compressor_app.ui.default_excel_available", lambda: False)
    monkeypatch.setattr("file_compressor_app.ui.default_powerpoint_available", lambda: False)
    monkeypatch.setattr("file_compressor_app.ui.default_hancom_available", lambda: False)
    monkeypatch.setattr(
        "file_compressor_app.pdf_search_ui.detect_tesseract",
        lambda: DependencyStatus(tesseract_available, "tesseract" if tesseract_available else None),
    )
    app()
    return MainWindow()


def tab_labels(window: MainWindow) -> list[str]:
    return [window.tabs.tabText(index) for index in range(window.tabs.count())]


def test_main_window_includes_pdf_tools_and_search_tabs(monkeypatch):
    window = make_window(monkeypatch)

    assert tab_labels(window) == [
        "문서 압축",
        "파일 이름 변경",
        "파일 자동 분류",
        "파일 날짜 변경",
        "PDF 도구",
        "파일 내용 검색",
    ]

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert tab_labels(window) == ["Compression", "Rename", "Classify", "Dates", "PDF Tools", "Search"]


def test_pdf_tools_tab_extracts_selected_pages(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-pdf-tools")
    source = workdir / "source.pdf"
    output = workdir / "extract.pdf"
    write_pdf(source, 3)

    window.pdf_tools_tab.add_paths([source])
    window.pdf_tools_tab.set_output_path(output)
    window.pdf_tools_tab.operation_combo.setCurrentIndex(
        window.pdf_tools_tab.operation_combo.findData("extract")
    )
    window.pdf_tools_tab.page_selection_edit.setText("2")
    window.pdf_tools_tab.preview_operation()
    window.pdf_tools_tab.apply_operation()

    assert output.exists()
    assert len(PdfReader(str(output)).pages) == 1
    assert window.pdf_tools_tab.table.item(0, 3).text() == "완료"


def test_search_tab_finds_text_file_content(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-search")
    source = workdir / "memo.txt"
    source.write_text("needle appears here", encoding="utf-8")

    window.search_tab.add_paths([source])
    window.search_tab.query_edit.setText("needle")
    window.search_tab.run_search()

    assert window.search_tab.table.item(0, 0).text() == "memo.txt"
    assert window.search_tab.table.item(0, 2).text() == "Line 1"
    assert window.search_tab.table.item(0, 4).text() == "일치"


def test_search_tab_shows_ocr_status_and_opens_install_page(monkeypatch):
    window = make_window(monkeypatch, tesseract_available=False)
    opened = []

    def fake_open_url(url):
        opened.append(url.toString())
        return True

    monkeypatch.setattr("file_compressor_app.pdf_search_ui.QDesktopServices.openUrl", fake_open_url)

    assert window.search_tab.ocr_status_label.text() == "OCR: 설치 필요"
    window.search_tab.ocr_install_button.click()

    assert opened == [TESSERACT_DOWNLOAD_URL]
