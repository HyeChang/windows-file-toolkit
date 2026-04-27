from __future__ import annotations

from dataclasses import replace
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
    QSplitter,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from file_compressor.content_search import SearchResult, search_files
from file_compressor.dependencies import TESSERACT_DOWNLOAD_URL, detect_tesseract
from file_compressor.pdf_tools import (
    PdfPagePlan,
    PdfOperationResult,
    default_merge_plan,
    delete_pages,
    extract_pages,
    pdf_page_refs,
    reorder_pages,
    rotate_pages,
    split_pdf,
    write_page_plan,
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
        "pdf_1": "PDF 1",
        "pdf_2": "PDF 2",
        "merge_result": "병합 결과",
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
        "input_page_headers": ["파일", "페이지"],
        "merge_result_headers": ["순서", "파일", "페이지", "회전", "상태"],
        "move_up": "위로",
        "move_down": "아래로",
        "remove_result": "결과 삭제",
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
        "pdf_1": "PDF 1",
        "pdf_2": "PDF 2",
        "merge_result": "Merge Result",
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
        "input_page_headers": ["File", "Page"],
        "merge_result_headers": ["Order", "File", "Page", "Rotation", "Status"],
        "move_up": "Move up",
        "move_down": "Move down",
        "remove_result": "Remove",
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
        self.merge_plan: list[PdfPagePlan] = []

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
        self.pdf1_group = QGroupBox()
        self.pdf2_group = QGroupBox()
        self.merge_result_group = QGroupBox()
        self.pdf1_table = FileToolTable(2)
        self.pdf2_table = FileToolTable(2)
        self.merge_result_table = FileToolTable(5)
        self.move_up_button = QPushButton()
        self.move_down_button = QPushButton()
        self.remove_result_button = QPushButton()

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
        self.operation_combo.currentIndexChanged.connect(self.on_operation_changed)
        self.move_up_button.clicked.connect(self.move_merge_result_up)
        self.move_down_button.clicked.connect(self.move_merge_result_down)
        self.remove_result_button.clicked.connect(self.remove_selected_merge_result)

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
        self._setup_merge_panels()
        layout.addWidget(self.table)
        layout.addWidget(self.merge_splitter)
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
        self.pdf1_group.setTitle(str(self.tr("pdf_1")))
        self.pdf2_group.setTitle(str(self.tr("pdf_2")))
        self.merge_result_group.setTitle(str(self.tr("merge_result")))
        self.move_up_button.setText(str(self.tr("move_up")))
        self.move_down_button.setText(str(self.tr("move_down")))
        self.remove_result_button.setText(str(self.tr("remove_result")))
        self.operation_label.setText(str(self.tr("operation")))
        self.page_selection_label.setText(str(self.tr("pages")))
        self.rotation_label.setText(str(self.tr("rotation")))
        self.table.setHorizontalHeaderLabels(self.tr("pdf_headers"))
        self.pdf1_table.setHorizontalHeaderLabels(self.tr("input_page_headers"))
        self.pdf2_table.setHorizontalHeaderLabels(self.tr("input_page_headers"))
        self.merge_result_table.setHorizontalHeaderLabels(self.tr("merge_result_headers"))
        self._set_operation_items(selected_operation)
        self._refresh_output_label()
        self._refresh_mode_visibility()
        self.refresh_table("ready")

    def _setup_merge_panels(self):
        self.merge_splitter = QSplitter()
        for group, table in (
            (self.pdf1_group, self.pdf1_table),
            (self.pdf2_group, self.pdf2_table),
        ):
            group_layout = QVBoxLayout()
            group_layout.addWidget(table)
            group.setLayout(group_layout)
            self.merge_splitter.addWidget(group)

        result_layout = QVBoxLayout()
        result_actions = QHBoxLayout()
        result_actions.addWidget(self.move_up_button)
        result_actions.addWidget(self.move_down_button)
        result_actions.addWidget(self.remove_result_button)
        result_actions.addStretch()
        result_layout.addLayout(result_actions)
        result_layout.addWidget(self.merge_result_table)
        self.merge_result_group.setLayout(result_layout)
        self.merge_splitter.addWidget(self.merge_result_group)

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
        if self.operation_combo.currentData() == "merge":
            self.paths = self.paths[:2]
            self.merge_plan = default_merge_plan(self.paths)
        self.refresh_table("ready")

    def clear_paths(self):
        self.paths.clear()
        self.last_result = None
        self.merge_plan = []
        self.refresh_table("ready")

    def preview_operation(self):
        if self.operation_combo.currentData() == "merge":
            self.paths = self.paths[:2]
            self.merge_plan = default_merge_plan(self.paths)
        self.refresh_table("ready")

    def apply_operation(self):
        operation = self.operation_combo.currentData()
        if not self.paths:
            return
        try:
            output = self._planned_output(operation)
            if operation == "merge":
                if not self.merge_plan:
                    self.merge_plan = default_merge_plan(self.paths)
                result = write_page_plan(self.merge_plan, output)
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

    def on_operation_changed(self):
        if self.operation_combo.currentData() == "merge":
            self.paths = self.paths[:2]
            self.merge_plan = default_merge_plan(self.paths)
        self._refresh_mode_visibility()
        self.refresh_table("ready")

    def move_merge_result_up(self):
        row = self._selected_merge_result_row()
        if row is None or row == 0:
            return
        self.merge_plan[row - 1], self.merge_plan[row] = self.merge_plan[row], self.merge_plan[row - 1]
        self._renumber_merge_plan()
        self.refresh_table("ready")
        self.merge_result_table.selectRow(row - 1)

    def move_merge_result_down(self):
        row = self._selected_merge_result_row()
        if row is None or row >= len(self.merge_plan) - 1:
            return
        self.merge_plan[row + 1], self.merge_plan[row] = self.merge_plan[row], self.merge_plan[row + 1]
        self._renumber_merge_plan()
        self.refresh_table("ready")
        self.merge_result_table.selectRow(row + 1)

    def remove_selected_merge_result(self):
        row = self._selected_merge_result_row()
        if row is None:
            return
        del self.merge_plan[row]
        self._renumber_merge_plan()
        self.refresh_table("ready")

    def refresh_table(self, status: str):
        if self.operation_combo.currentData() == "merge":
            if not self.merge_plan and self.paths:
                self.merge_plan = default_merge_plan(self.paths)
            self._refresh_merge_tables(status)
            return

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

    def _refresh_mode_visibility(self):
        is_merge = self.operation_combo.currentData() == "merge"
        self.table.setVisible(not is_merge)
        self.merge_splitter.setVisible(is_merge)
        self.page_selection_label.setVisible(not is_merge)
        self.page_selection_edit.setVisible(not is_merge)
        self.rotation_label.setVisible(not is_merge)
        self.rotation_combo.setVisible(self.operation_combo.currentData() == "rotate")

    def _refresh_merge_tables(self, status: str):
        self._refresh_input_page_table(self.pdf1_table, self.paths[0] if len(self.paths) > 0 else None)
        self._refresh_input_page_table(self.pdf2_table, self.paths[1] if len(self.paths) > 1 else None)

        self.merge_result_table.setRowCount(len(self.merge_plan))
        for row, page in enumerate(self.merge_plan):
            values = [
                str(page.result_order),
                page.source.name,
                str(page.page_number),
                str(page.rotation) if page.rotation else "",
                self.status_text(status),
            ]
            for column, value in enumerate(values):
                self.merge_result_table.setItem(row, column, QTableWidgetItem(value))

        self.pdf1_table.resizeColumnsToContents()
        self.pdf2_table.resizeColumnsToContents()
        self.merge_result_table.resizeColumnsToContents()

    def _refresh_input_page_table(self, table: FileToolTable, source: Path | None):
        if source is None:
            table.setRowCount(0)
            return

        try:
            pages = pdf_page_refs(source)
        except Exception:
            table.setRowCount(0)
            return

        table.setRowCount(len(pages))
        for row, page in enumerate(pages):
            table.setItem(row, 0, QTableWidgetItem(page.source.name))
            table.setItem(row, 1, QTableWidgetItem(str(page.page_number)))

    def _selected_merge_result_row(self) -> int | None:
        row = self.merge_result_table.currentRow()
        if row < 0 or row >= len(self.merge_plan):
            return None
        return row

    def _renumber_merge_plan(self):
        self.merge_plan = [
            replace(page, result_order=index)
            for index, page in enumerate(self.merge_plan, start=1)
        ]


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
