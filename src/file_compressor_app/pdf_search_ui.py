from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QItemSelectionModel, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
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
    build_single_pdf_plan,
    default_merge_plan,
    pdf_page_refs,
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
        "page_plan": "페이지 작업 미리보기",
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
        "page_plan_headers": ["순서", "파일", "원본 페이지", "작업", "회전", "출력"],
        "select_all_pages": "전체 선택",
        "clear_page_selection": "선택 해제",
        "page_actions": {
            "include": "포함",
            "exclude": "제외",
            "delete": "삭제",
            "keep": "유지",
            "split": "분할",
            "rotate": "회전",
        },
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
        "page_plan": "Page Preview",
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
        "page_plan_headers": ["Order", "File", "Source page", "Action", "Rotation", "Output"],
        "select_all_pages": "Select all",
        "clear_page_selection": "Clear",
        "page_actions": {
            "include": "Include",
            "exclude": "Exclude",
            "delete": "Delete",
            "keep": "Keep",
            "split": "Split",
            "rotate": "Rotate",
        },
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
        self.page_plan: list[PdfPagePlan] = []
        self.selected_page_numbers: list[int] = [1]
        self._refreshing_page_plan = False

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
        self.page_plan_group = QGroupBox()
        self.page_plan_table = FileToolTable(6)
        self.page_select_all_button = QPushButton()
        self.page_clear_selection_button = QPushButton()
        self.page_move_up_button = QPushButton()
        self.page_move_down_button = QPushButton()
        self.pdf1_group = QGroupBox()
        self.pdf2_group = QGroupBox()
        self.merge_result_group = QGroupBox()
        self.pdf1_table = FileToolTable(2)
        self.pdf2_table = FileToolTable(2)
        self.merge_result_table = FileToolTable(5)
        self.move_up_button = QPushButton()
        self.move_down_button = QPushButton()
        self.remove_result_button = QPushButton()

        self.options_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.options_group.setMaximumHeight(96)
        self.page_plan_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.merge_result_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

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
        self.page_plan_table.itemSelectionChanged.connect(self.on_page_plan_selection_changed)
        self.page_select_all_button.clicked.connect(self.select_all_page_rows)
        self.page_clear_selection_button.clicked.connect(self.clear_page_row_selection)
        self.page_move_up_button.clicked.connect(self.move_page_plan_up)
        self.page_move_down_button.clicked.connect(self.move_page_plan_down)

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
        self._setup_page_plan_panel()
        self._setup_merge_panels()
        layout.addWidget(self.table)
        layout.addWidget(self.page_plan_group)
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
        self.page_plan_group.setTitle(str(self.tr("page_plan")))
        self.page_select_all_button.setText(str(self.tr("select_all_pages")))
        self.page_clear_selection_button.setText(str(self.tr("clear_page_selection")))
        self.page_move_up_button.setText(str(self.tr("move_up")))
        self.page_move_down_button.setText(str(self.tr("move_down")))
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
        self.page_plan_table.setHorizontalHeaderLabels(self.tr("page_plan_headers"))
        self.pdf1_table.setHorizontalHeaderLabels(self.tr("input_page_headers"))
        self.pdf2_table.setHorizontalHeaderLabels(self.tr("input_page_headers"))
        self.merge_result_table.setHorizontalHeaderLabels(self.tr("merge_result_headers"))
        self._set_operation_items(selected_operation)
        self._configure_table_columns()
        self._refresh_output_label()
        self._refresh_mode_visibility()
        self.refresh_table("ready")

    def _setup_page_plan_panel(self):
        layout = QVBoxLayout()
        actions = QHBoxLayout()
        actions.addWidget(self.page_select_all_button)
        actions.addWidget(self.page_clear_selection_button)
        actions.addWidget(self.page_move_up_button)
        actions.addWidget(self.page_move_down_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(self.page_plan_table)
        self.page_plan_group.setLayout(layout)

    def _setup_merge_panels(self):
        self.merge_splitter = QSplitter(Qt.Orientation.Vertical)
        self.merge_input_splitter = QSplitter(Qt.Orientation.Horizontal)
        for group, table in (
            (self.pdf1_group, self.pdf1_table),
            (self.pdf2_group, self.pdf2_table),
        ):
            group_layout = QVBoxLayout()
            group_layout.addWidget(table)
            group.setLayout(group_layout)
            self.merge_input_splitter.addWidget(group)

        result_layout = QVBoxLayout()
        result_actions = QHBoxLayout()
        result_actions.addWidget(self.move_up_button)
        result_actions.addWidget(self.move_down_button)
        result_actions.addWidget(self.remove_result_button)
        result_actions.addStretch()
        result_layout.addLayout(result_actions)
        result_layout.addWidget(self.merge_result_table)
        self.merge_result_group.setLayout(result_layout)
        self.merge_splitter.addWidget(self.merge_input_splitter)
        self.merge_splitter.addWidget(self.merge_result_group)
        self.merge_splitter.setSizes([240, 260])

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
        had_paths = bool(self.paths)
        known = set(self.paths)
        for path in _expand_pdf_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        if self.operation_combo.currentData() == "merge":
            self.paths = self.paths[:2]
            self.merge_plan = default_merge_plan(self.paths)
        elif not had_paths and self.paths:
            self._reset_single_pdf_state()
        self.refresh_table("ready")

    def clear_paths(self):
        self.paths.clear()
        self.last_result = None
        self.merge_plan = []
        self._reset_single_pdf_state()
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
                self._refresh_page_plan_table()
                result = write_page_plan(self.page_plan, output)
            elif operation == "delete":
                self._refresh_page_plan_table()
                result = write_page_plan(self.page_plan, output)
            elif operation == "rotate":
                self._refresh_page_plan_table()
                result = write_page_plan(self.page_plan, output)
            elif operation == "reorder":
                self._ensure_reorder_plan()
                result = write_page_plan(self.page_plan, output)
            else:
                result = PdfOperationResult(status="failed", message="Unknown operation.")
        except Exception as exc:
            result = PdfOperationResult(status="failed", message=str(exc))
        self.last_result = result
        self.refresh_table(result.status)

    def on_operation_changed(self):
        operation = self.operation_combo.currentData()
        if operation == "merge":
            self.paths = self.paths[:2]
            self.merge_plan = default_merge_plan(self.paths)
        elif operation == "reorder":
            self.page_plan = []
        else:
            self._reset_single_pdf_state()
        self._refresh_mode_visibility()
        self.refresh_table("ready")

    def on_page_plan_selection_changed(self):
        if self._refreshing_page_plan:
            return
        operation = self.operation_combo.currentData()
        if operation not in {"extract", "delete", "rotate"}:
            return

        selected_rows = sorted({index.row() for index in self.page_plan_table.selectionModel().selectedRows()})
        selected_pages: list[int] = []
        for row in selected_rows:
            item = self.page_plan_table.item(row, 2)
            if item is not None:
                selected_pages.append(int(item.text()))
        self.selected_page_numbers = selected_pages
        self.page_selection_edit.setText(self._selected_pages_text())
        self._refresh_page_plan_table()

    def select_all_page_rows(self):
        if self.operation_combo.currentData() not in {"extract", "delete", "rotate"}:
            return
        self.selected_page_numbers = [page.page_number for page in pdf_page_refs(self.paths[0])] if self.paths else []
        self.page_selection_edit.setText(self._selected_pages_text())
        self._refresh_page_plan_table()

    def clear_page_row_selection(self):
        if self.operation_combo.currentData() not in {"extract", "delete", "rotate"}:
            return
        self.selected_page_numbers = []
        self.page_selection_edit.setText("")
        self._refresh_page_plan_table()

    def move_page_plan_up(self):
        row = self._selected_page_plan_row()
        if row is None or row == 0:
            return
        self._ensure_reorder_plan()
        self.page_plan[row - 1], self.page_plan[row] = self.page_plan[row], self.page_plan[row - 1]
        self._renumber_page_plan()
        self._refresh_page_plan_table()
        self.page_plan_table.selectRow(row - 1)

    def move_page_plan_down(self):
        row = self._selected_page_plan_row()
        if row is None:
            return
        self._ensure_reorder_plan()
        if row >= len(self.page_plan) - 1:
            return
        self.page_plan[row + 1], self.page_plan[row] = self.page_plan[row], self.page_plan[row + 1]
        self._renumber_page_plan()
        self._refresh_page_plan_table()
        self.page_plan_table.selectRow(row + 1)

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
        self._refresh_page_plan_table()

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
        operation = self.operation_combo.currentData()
        is_merge = operation == "merge"
        uses_page_row_selection = operation in {"extract", "delete", "rotate"}
        uses_page_reorder = operation == "reorder"
        self.table.setVisible(not is_merge)
        self.page_plan_group.setVisible(not is_merge)
        self.merge_splitter.setVisible(is_merge)
        self.page_selection_label.setVisible(False)
        self.page_selection_edit.setVisible(False)
        self.rotation_label.setVisible(operation == "rotate")
        self.rotation_combo.setVisible(operation == "rotate")
        self.page_select_all_button.setVisible(uses_page_row_selection)
        self.page_clear_selection_button.setVisible(uses_page_row_selection)
        self.page_move_up_button.setVisible(uses_page_reorder)
        self.page_move_down_button.setVisible(uses_page_reorder)

    def _refresh_page_plan_table(self):
        if not self.paths:
            self.page_plan_table.setRowCount(0)
            self.page_plan = []
            return

        operation = self.operation_combo.currentData()
        if operation == "merge":
            self.page_plan_table.setRowCount(0)
            self.page_plan = []
            return

        try:
            if operation == "reorder":
                self._ensure_reorder_plan()
                plan = self.page_plan
            else:
                self._clamp_selected_pages()
                plan = build_single_pdf_plan(
                    self.paths[0],
                    operation,
                    self._selected_pages_text(),
                    self._planned_output(operation),
                    rotation=self.rotation_combo.currentData() or 0,
                )
        except Exception:
            self.page_plan_table.setRowCount(0)
            self.page_plan = []
            return

        self.page_plan = plan
        self._refreshing_page_plan = True
        self.page_plan_table.blockSignals(True)
        self.page_plan_table.setRowCount(len(plan))
        for row, page in enumerate(plan):
            values = [
                str(page.result_order),
                page.source.name,
                str(page.page_number),
                self.action_text(page.action),
                str(page.rotation) if page.rotation else "",
                str(page.output or self._planned_output(operation)),
            ]
            for column, value in enumerate(values):
                self.page_plan_table.setItem(row, column, QTableWidgetItem(value))

        self.page_plan_table.clearSelection()
        if operation in {"extract", "delete", "rotate"}:
            selection_model = self.page_plan_table.selectionModel()
            selected = set(self.selected_page_numbers)
            for row, page in enumerate(plan):
                if page.page_number in selected:
                    selection_model.select(
                        self.page_plan_table.model().index(row, 0),
                        QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
                    )

        self.page_plan_table.blockSignals(False)
        self._refreshing_page_plan = False
        self._configure_table_columns()

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

        self._configure_table_columns()

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

    def _reset_single_pdf_state(self):
        self.page_plan = []
        self.selected_page_numbers = [1]
        self.page_selection_edit.setText("1")

    def _selected_pages_text(self) -> str:
        return ",".join(str(page_number) for page_number in self.selected_page_numbers)

    def _clamp_selected_pages(self):
        if not self.paths:
            self.selected_page_numbers = []
            self.page_selection_edit.setText("")
            return
        total_pages = len(pdf_page_refs(self.paths[0]))
        self.selected_page_numbers = [
            page_number
            for page_number in self.selected_page_numbers
            if 1 <= page_number <= total_pages
        ]
        self.page_selection_edit.setText(self._selected_pages_text())

    def _ensure_reorder_plan(self):
        if not self.paths:
            self.page_plan = []
            return
        source = self.paths[0]
        output = self._planned_output("reorder")
        if not self.page_plan or any(page.source != source for page in self.page_plan):
            self.page_plan = [
                replace(page, action="include", output=output)
                for page in pdf_page_refs(source)
            ]
        else:
            self.page_plan = [
                replace(page, output=output, result_order=index)
                for index, page in enumerate(self.page_plan, start=1)
            ]

    def _selected_page_plan_row(self) -> int | None:
        row = self.page_plan_table.currentRow()
        if row < 0:
            return None
        if self.operation_combo.currentData() != "reorder":
            return None
        if row >= len(self.page_plan):
            return None
        return row

    def _renumber_page_plan(self):
        self.page_plan = [
            replace(page, result_order=index)
            for index, page in enumerate(self.page_plan, start=1)
        ]

    def _configure_table_columns(self):
        self._set_resize_modes(self.pdf1_table, stretch={0})
        self._set_resize_modes(self.pdf2_table, stretch={0})
        self._set_resize_modes(self.merge_result_table, stretch={1})
        self._set_resize_modes(self.page_plan_table, stretch={1, 5})

    def _set_resize_modes(self, table: FileToolTable, *, stretch: set[int]):
        table.setWordWrap(False)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(table.columnCount()):
            mode = QHeaderView.ResizeMode.Stretch if column in stretch else QHeaderView.ResizeMode.ResizeToContents
            header.setSectionResizeMode(column, mode)

    def action_text(self, action: str) -> str:
        actions = TRANSLATIONS[self.language]["page_actions"]
        return str(actions.get(action, action))


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
