from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from file_compressor.content_search import SearchResult, search_files
from file_compressor.dependencies import TESSERACT_DOWNLOAD_URL, detect_tesseract
from file_compressor.pdf_tools import (
    PdfOperationResult,
    delete_pages,
    extract_pages,
    merge_pdfs,
    reorder_pages,
    rotate_pages,
    split_pdf,
)
from file_compressor_app.file_tools_ui import FileToolTable


TRANSLATIONS = {
    "ko": {
        "add_files": "파일 추가",
        "add_folder": "폴더 추가",
        "select_output": "출력 선택",
        "preview": "미리보기",
        "apply": "적용",
        "search": "검색",
        "clear_list": "목록 비우기",
        "select_files": "파일 선택",
        "select_folder": "폴더 선택",
        "select_output_file": "출력 PDF 선택",
        "select_output_folder": "출력 폴더 선택",
        "all_files_filter": "모든 파일 (*.*)",
        "pdf_filter": "PDF (*.pdf)",
        "pdf_options": "PDF 작업 옵션",
        "operation": "작업",
        "pages": "페이지",
        "rotation": "회전",
        "output_default": "출력: 자동",
        "output_selected": "출력: {path}",
        "merge": "PDF 병합",
        "split": "페이지별 분할",
        "extract": "페이지 추출",
        "delete": "페이지 삭제",
        "rotate": "페이지 회전",
        "reorder": "페이지 순서 변경",
        "pdf_headers": ["파일", "작업", "출력", "상태"],
        "search_options": "검색 옵션",
        "query": "검색어",
        "use_ocr": "OCR 사용",
        "ocr_available": "OCR: 사용 가능",
        "ocr_missing": "OCR: 설치 필요",
        "install_ocr": "OCR 설치",
        "search_headers": ["파일", "형식", "위치", "문맥", "상태"],
        "ready": "준비",
        "completed": "완료",
        "failed": "실패",
        "matched": "일치",
        "no_match": "일치 없음",
        "skipped": "건너뜀",
    },
    "en": {
        "add_files": "Add files",
        "add_folder": "Add folder",
        "select_output": "Select output",
        "preview": "Preview",
        "apply": "Apply",
        "search": "Search",
        "clear_list": "Clear list",
        "select_files": "Select files",
        "select_folder": "Select folder",
        "select_output_file": "Select output PDF",
        "select_output_folder": "Select output folder",
        "all_files_filter": "All files (*.*)",
        "pdf_filter": "PDF (*.pdf)",
        "pdf_options": "PDF options",
        "operation": "Operation",
        "pages": "Pages",
        "rotation": "Rotation",
        "output_default": "Output: automatic",
        "output_selected": "Output: {path}",
        "merge": "Merge PDFs",
        "split": "Split pages",
        "extract": "Extract pages",
        "delete": "Delete pages",
        "rotate": "Rotate pages",
        "reorder": "Reorder pages",
        "pdf_headers": ["File", "Operation", "Output", "Status"],
        "search_options": "Search options",
        "query": "Query",
        "use_ocr": "Use OCR",
        "ocr_available": "OCR: available",
        "ocr_missing": "OCR: install required",
        "install_ocr": "Install OCR",
        "search_headers": ["File", "Type", "Location", "Snippet", "Status"],
        "ready": "Ready",
        "completed": "Completed",
        "failed": "Failed",
        "matched": "Matched",
        "no_match": "No match",
        "skipped": "Skipped",
    },
}


class PdfToolsWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.output_path: Path | None = None
        self.last_result: PdfOperationResult | None = None

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.output_button = QPushButton()
        self.output_label = QLabel()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.options_group = QGroupBox()
        self.operation_label = QLabel()
        self.operation_combo = QComboBox()
        self.page_selection_label = QLabel()
        self.page_selection_edit = QLineEdit()
        self.rotation_label = QLabel()
        self.rotation_combo = QComboBox()
        self.table = FileToolTable(4, self.add_paths)

        self.page_selection_edit.setText("1")
        self._set_operation_items("extract")
        self.rotation_combo.addItem("90", 90)
        self.rotation_combo.addItem("180", 180)
        self.rotation_combo.addItem("270", 270)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.output_button.clicked.connect(self.pick_output)
        self.preview_button.clicked.connect(self.preview_operation)
        self.apply_button.clicked.connect(self.apply_operation)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.clear_list_button)
        actions.addWidget(self.output_button)
        actions.addWidget(self.output_label)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)

        options = QHBoxLayout()
        options.addWidget(self.operation_label)
        options.addWidget(self.operation_combo)
        options.addWidget(self.page_selection_label)
        options.addWidget(self.page_selection_edit)
        options.addWidget(self.rotation_label)
        options.addWidget(self.rotation_combo)
        options.addStretch()
        self.options_group.setLayout(options)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_operation = self.operation_combo.currentData() or "extract"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.output_button.setText(str(self.tr("select_output")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.options_group.setTitle(str(self.tr("pdf_options")))
        self.operation_label.setText(str(self.tr("operation")))
        self.page_selection_label.setText(str(self.tr("pages")))
        self.rotation_label.setText(str(self.tr("rotation")))
        self.table.setHorizontalHeaderLabels(self.tr("pdf_headers"))
        self._set_operation_items(selected_operation)
        self._refresh_output_label()
        self.refresh_table("ready")

    def _set_operation_items(self, selected: str):
        self.operation_combo.blockSignals(True)
        self.operation_combo.clear()
        for key in ("merge", "split", "extract", "delete", "rotate", "reorder"):
            self.operation_combo.addItem(str(self.tr(key)), key)
        self.operation_combo.blockSignals(False)
        self.operation_combo.setCurrentIndex(self.operation_combo.findData(selected))

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, str(self.tr("select_files")), "", str(self.tr("pdf_filter")))
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if folder:
            self.add_paths([Path(folder)])

    def pick_output(self):
        if self.operation_combo.currentData() == "split":
            folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_output_folder")), "")
            if folder:
                self.set_output_path(Path(folder))
            return
        file, _ = QFileDialog.getSaveFileName(self, str(self.tr("select_output_file")), "", str(self.tr("pdf_filter")))
        if file:
            self.set_output_path(Path(file))

    def set_output_path(self, path: Path):
        self.output_path = Path(path)
        self._refresh_output_label()
        self.refresh_table("ready")

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_pdf_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.refresh_table("ready")

    def clear_paths(self):
        self.paths.clear()
        self.last_result = None
        self.refresh_table("ready")

    def preview_operation(self):
        self.refresh_table("ready")

    def apply_operation(self):
        operation = self.operation_combo.currentData()
        if not self.paths:
            return
        try:
            output = self._planned_output(operation)
            if operation == "merge":
                result = merge_pdfs(self.paths, output)
            elif operation == "split":
                result = split_pdf(self.paths[0], output)
            elif operation == "extract":
                result = extract_pages(self.paths[0], output, self.page_selection_edit.text())
            elif operation == "delete":
                result = delete_pages(self.paths[0], output, self.page_selection_edit.text())
            elif operation == "rotate":
                result = rotate_pages(
                    self.paths[0],
                    output,
                    self.page_selection_edit.text(),
                    self.rotation_combo.currentData(),
                )
            elif operation == "reorder":
                result = reorder_pages(self.paths[0], output, self.page_selection_edit.text())
            else:
                result = PdfOperationResult(status="failed", message="Unknown operation.")
        except Exception as exc:
            result = PdfOperationResult(status="failed", message=str(exc))
        self.last_result = result
        self.refresh_table(result.status)

    def refresh_table(self, status: str):
        self.table.setRowCount(len(self.paths))
        operation_label = self.operation_combo.currentText()
        for row, path in enumerate(self.paths):
            output_text = self._output_text_for_row(row)
            values = [path.name, operation_label, output_text, self.status_text(status)]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _planned_output(self, operation: str) -> Path:
        if self.output_path is not None:
            return self.output_path
        source = self.paths[0]
        if operation == "split":
            return source.parent / f"{source.stem}_pages"
        return source.with_name(f"{source.stem}_{operation}.pdf")

    def _output_text_for_row(self, row: int) -> str:
        if self.last_result and self.last_result.output:
            return str(self.last_result.output)
        if self.last_result and self.last_result.outputs:
            return str(self.last_result.outputs[0].parent)
        if not self.paths:
            return ""
        return str(self._planned_output(self.operation_combo.currentData()))

    def _refresh_output_label(self):
        if self.output_path is None:
            self.output_label.setText(str(self.tr("output_default")))
        else:
            self.output_label.setText(str(self.tr("output_selected")).format(path=self.output_path))


class ContentSearchWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.results: list[SearchResult] = []
        self.tesseract_status = detect_tesseract()

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.search_button = QPushButton()
        self.options_group = QGroupBox()
        self.query_label = QLabel()
        self.query_edit = QLineEdit()
        self.use_ocr_checkbox = QCheckBox()
        self.ocr_status_label = QLabel()
        self.ocr_install_button = QPushButton()
        self.table = FileToolTable(5, self.add_paths)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.search_button.clicked.connect(self.run_search)
        self.ocr_install_button.clicked.connect(self.open_ocr_download)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.search_button)

        options = QHBoxLayout()
        options.addWidget(self.query_label)
        options.addWidget(self.query_edit)
        options.addWidget(self.use_ocr_checkbox)
        options.addWidget(self.ocr_status_label)
        options.addWidget(self.ocr_install_button)
        options.addStretch()
        self.options_group.setLayout(options)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.search_button.setText(str(self.tr("search")))
        self.options_group.setTitle(str(self.tr("search_options")))
        self.query_label.setText(str(self.tr("query")))
        self.use_ocr_checkbox.setText(str(self.tr("use_ocr")))
        self.ocr_install_button.setText(str(self.tr("install_ocr")))
        self.table.setHorizontalHeaderLabels(self.tr("search_headers"))
        self._refresh_ocr_status()
        self.refresh_table()

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            str(self.tr("select_files")),
            "",
            str(self.tr("all_files_filter")),
        )
        self.add_paths([Path(file) for file in files])

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_folder")), "")
        if folder:
            self.add_paths([Path(folder)])

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_all_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.results = []
        self.refresh_table()

    def clear_paths(self):
        self.paths.clear()
        self.results = []
        self.refresh_table()

    def run_search(self):
        query = self.query_edit.text().strip()
        if not query:
            return
        executable = self.tesseract_status.executable if self.use_ocr_checkbox.isChecked() else None
        self.results = search_files(
            self.paths,
            query,
            use_ocr=self.use_ocr_checkbox.isChecked(),
            tesseract_executable=executable,
        )
        self.refresh_table()

    def refresh_table(self):
        if self.results:
            self.table.setRowCount(len(self.results))
            for row, result in enumerate(self.results):
                values = [
                    result.source.name,
                    result.kind,
                    result.location,
                    result.snippet,
                    self.status_text(result.status),
                ]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if column == 4:
                        item.setToolTip(result.message)
                    self.table.setItem(row, column, item)
        else:
            self.table.setRowCount(len(self.paths))
            for row, path in enumerate(self.paths):
                for column, value in enumerate([path.name, path.suffix.lower(), "", "", ""]):
                    self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def open_ocr_download(self):
        QDesktopServices.openUrl(QUrl(TESSERACT_DOWNLOAD_URL))

    def _refresh_ocr_status(self):
        if self.tesseract_status.available:
            self.ocr_status_label.setText(str(self.tr("ocr_available")))
            self.ocr_install_button.setEnabled(False)
        else:
            self.ocr_status_label.setText(str(self.tr("ocr_missing")))
            self.ocr_install_button.setEnabled(True)


def _expand_pdf_files(paths: list[Path]) -> list[Path]:
    return [path for path in _expand_all_files(paths) if path.suffix.lower() == ".pdf"]


def _expand_all_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*") if child.is_file()))
        elif path.is_file():
            files.append(path)
    return files
