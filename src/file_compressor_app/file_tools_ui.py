from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from file_compressor.file_tools import (
    ClassificationPlan,
    DateChangePlan,
    RenameOptions,
    RenamePlan,
    apply_classification_plan,
    apply_date_change_plan,
    apply_rename_plan,
    build_classification_plan,
    build_date_change_plan,
    build_rename_plan,
    get_file_timestamps,
    undo_classification_results,
    undo_date_change_results,
    undo_rename_results,
)


TRANSLATIONS = {
    "ko": {
        "add_files": "파일 추가",
        "add_folder": "폴더 추가",
        "remove_selected": "선택 삭제",
        "clear_list": "목록 비우기",
        "preview": "미리보기",
        "apply": "적용",
        "undo": "되돌리기",
        "select_files": "파일 선택",
        "select_folder": "폴더 선택",
        "all_files_filter": "모든 파일 (*.*)",
        "rename_options": "이름 변경 옵션",
        "prefix": "앞에 추가",
        "suffix": "뒤에 추가",
        "find": "찾기",
        "replace": "바꾸기",
        "clean_spaces": "공백 정리",
        "clean_special": "특수문자 제거",
        "number_files": "번호 붙이기",
        "number_start": "시작 번호",
        "date_format": "날짜 형식",
        "date_change_options": "날짜 변경 옵션",
        "date_source": "날짜 기준",
        "manual": "직접 입력",
        "filename": "파일명 날짜",
        "now": "현재 시간",
        "change_created": "생성일 변경",
        "change_modified": "수정일 변경",
        "created_input": "생성일",
        "modified_input": "수정일",
        "preserve_modified_time": "수정일 유지",
        "rename_headers": ["원본", "변경 후", "상태", "위치"],
        "classify_headers": ["파일", "분류", "이동 위치", "상태"],
        "date_headers": ["파일", "생성일", "수정일", "상태", "위치"],
        "select_output_folder_button": "출력 폴더 선택",
        "select_output_folder": "출력 폴더 선택",
        "output_folder_missing": "출력 폴더: 선택 필요",
        "output_folder_selected": "출력 폴더: {path}",
        "ready": "준비",
        "completed": "완료",
        "unchanged": "변경 없음",
        "skipped": "건너뜀",
        "failed": "실패",
        "undone": "되돌림",
        "details": "파일 상세 정보",
        "no_selection": "선택 없음",
        "file_name": "파일명",
        "full_path": "전체 경로",
        "extension": "확장자",
        "size": "크기",
        "created": "생성일",
        "modified": "수정일",
        "planned_path": "예정 위치",
        "status": "상태",
        "none": "날짜 변경 안 함",
        "prefix_dash": "YYYY-MM-DD_파일명",
        "prefix_compact": "YYYYMMDD_파일명",
        "suffix_dash": "파일명_YYYY-MM-DD",
        "suffix_compact": "파일명_YYYYMMDD",
    },
    "en": {
        "add_files": "Add files",
        "add_folder": "Add folder",
        "remove_selected": "Remove selected",
        "clear_list": "Clear list",
        "preview": "Preview",
        "apply": "Apply",
        "undo": "Undo",
        "select_files": "Select files",
        "select_folder": "Select folder",
        "all_files_filter": "All files (*.*)",
        "rename_options": "Rename options",
        "prefix": "Prefix",
        "suffix": "Suffix",
        "find": "Find",
        "replace": "Replace",
        "clean_spaces": "Clean spaces",
        "clean_special": "Remove special characters",
        "number_files": "Number files",
        "number_start": "Start number",
        "date_format": "Date format",
        "date_change_options": "Date change options",
        "date_source": "Date source",
        "manual": "Manual",
        "filename": "File name date",
        "now": "Current time",
        "change_created": "Change created",
        "change_modified": "Change modified",
        "created_input": "Created",
        "modified_input": "Modified",
        "preserve_modified_time": "Preserve modified date",
        "rename_headers": ["Original", "New name", "Status", "Location"],
        "classify_headers": ["File", "Category", "Move to", "Status"],
        "date_headers": ["File", "Created", "Modified", "Status", "Location"],
        "select_output_folder_button": "Select output folder",
        "select_output_folder": "Select output folder",
        "output_folder_missing": "Output folder: required",
        "output_folder_selected": "Output folder: {path}",
        "ready": "Ready",
        "completed": "Completed",
        "unchanged": "Unchanged",
        "skipped": "Skipped",
        "failed": "Failed",
        "undone": "Undone",
        "details": "File details",
        "no_selection": "No selection",
        "file_name": "File name",
        "full_path": "Full path",
        "extension": "Extension",
        "size": "Size",
        "created": "Created",
        "modified": "Modified",
        "planned_path": "Planned path",
        "status": "Status",
        "none": "Do not change dates",
        "prefix_dash": "YYYY-MM-DD_filename",
        "prefix_compact": "YYYYMMDD_filename",
        "suffix_dash": "filename_YYYY-MM-DD",
        "suffix_compact": "filename_YYYYMMDD",
    },
}


class FileToolTable(QTableWidget):
    def __init__(self, columns: int, on_files=None):
        super().__init__(0, columns)
        self.on_files = on_files
        self.setAcceptDrops(on_files is not None)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def dragEnterEvent(self, event):
        if self._has_local_urls(event):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if self._has_local_urls(event):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.on_files is None or not self._has_local_urls(event):
            return

        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        self.on_files(paths)
        event.acceptProposedAction()

    def _has_local_urls(self, event) -> bool:
        mime_data = event.mimeData()
        return mime_data.hasUrls() and any(url.isLocalFile() for url in mime_data.urls())


class FileDetailPanel(QGroupBox):
    FIELD_KEYS = (
        "file_name",
        "full_path",
        "extension",
        "size",
        "created",
        "modified",
        "planned_path",
        "status",
    )

    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.field_labels: dict[str, QLabel] = {}
        self.value_labels: dict[str, QLabel] = {}
        layout = QFormLayout()
        for key in self.FIELD_KEYS:
            field_label = QLabel()
            value_label = QLabel()
            value_label.setWordWrap(True)
            self.field_labels[key] = field_label
            self.value_labels[key] = value_label
            layout.addRow(field_label, value_label)
        self.setLayout(layout)
        self.set_language(language)
        self.clear()

    def tr(self, key: str) -> str:
        return str(TRANSLATIONS[self.language][key])

    def set_language(self, language: str):
        self.language = language
        self.setTitle(self.tr("details"))
        for key, label in self.field_labels.items():
            label.setText(self.tr(key))

    def clear(self):
        for key in self.FIELD_KEYS:
            self.value_labels[key].setText("-")
        self.value_labels["status"].setText(self.tr("no_selection"))

    def set_file(self, path: Path, *, planned_path: Path | None = None, status: str = ""):
        path = Path(path)
        stat_path = path if path.exists() else planned_path
        self.value_labels["file_name"].setText(path.name)
        self.value_labels["full_path"].setText(str(path))
        self.value_labels["extension"].setText(path.suffix or "-")
        self.value_labels["planned_path"].setText(str(planned_path) if planned_path else "-")
        self.value_labels["status"].setText(status or "-")

        if stat_path and Path(stat_path).exists():
            stat_path = Path(stat_path)
            timestamps = get_file_timestamps(stat_path)
            self.value_labels["size"].setText(_format_size(stat_path.stat().st_size))
            self.value_labels["created"].setText(_format_timestamp(timestamps.created))
            self.value_labels["modified"].setText(_format_timestamp(timestamps.modified))
        else:
            self.value_labels["size"].setText("-")
            self.value_labels["created"].setText("-")
            self.value_labels["modified"].setText("-")

    def value_text(self, key: str) -> str:
        return self.value_labels[key].text()


class RenameToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.plans: list[RenamePlan] = []
        self.last_results: list[RenamePlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.options_group = QGroupBox()
        self.prefix_label = QLabel()
        self.prefix_edit = QLineEdit()
        self.suffix_label = QLabel()
        self.suffix_edit = QLineEdit()
        self.find_label = QLabel()
        self.find_edit = QLineEdit()
        self.replace_label = QLabel()
        self.replace_edit = QLineEdit()
        self.clean_spaces_checkbox = QCheckBox()
        self.clean_special_checkbox = QCheckBox()
        self.number_files_checkbox = QCheckBox()
        self.number_start_label = QLabel()
        self.number_start_spin = QSpinBox()
        self.date_format_label = QLabel()
        self.date_format_combo = QComboBox()
        self.preserve_modified_time_checkbox = QCheckBox()
        self.table = FileToolTable(4, self.add_paths)
        self.detail_panel = FileDetailPanel(language)

        self.number_start_spin.setRange(1, 999999)
        self.number_start_spin.setValue(1)
        self.preserve_modified_time_checkbox.setChecked(True)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_changes)
        self.apply_button.clicked.connect(self.apply_changes)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.undo_button)

        options_layout = QGridLayout()
        options_layout.addWidget(self.prefix_label, 0, 0)
        options_layout.addWidget(self.prefix_edit, 0, 1)
        options_layout.addWidget(self.suffix_label, 0, 2)
        options_layout.addWidget(self.suffix_edit, 0, 3)
        options_layout.addWidget(self.find_label, 1, 0)
        options_layout.addWidget(self.find_edit, 1, 1)
        options_layout.addWidget(self.replace_label, 1, 2)
        options_layout.addWidget(self.replace_edit, 1, 3)
        options_layout.addWidget(self.clean_spaces_checkbox, 2, 0)
        options_layout.addWidget(self.clean_special_checkbox, 2, 1)
        options_layout.addWidget(self.number_files_checkbox, 2, 2)
        options_layout.addWidget(self.number_start_label, 2, 3)
        options_layout.addWidget(self.number_start_spin, 2, 4)
        options_layout.addWidget(self.date_format_label, 3, 0)
        options_layout.addWidget(self.date_format_combo, 3, 1)
        options_layout.addWidget(self.preserve_modified_time_checkbox, 3, 2)
        self.options_group.setLayout(options_layout)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        content_layout.addWidget(self.detail_panel, 1)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_date_format = self.date_format_combo.currentData() or "none"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.options_group.setTitle(str(self.tr("rename_options")))
        self.prefix_label.setText(str(self.tr("prefix")))
        self.suffix_label.setText(str(self.tr("suffix")))
        self.find_label.setText(str(self.tr("find")))
        self.replace_label.setText(str(self.tr("replace")))
        self.clean_spaces_checkbox.setText(str(self.tr("clean_spaces")))
        self.clean_special_checkbox.setText(str(self.tr("clean_special")))
        self.number_files_checkbox.setText(str(self.tr("number_files")))
        self.number_start_label.setText(str(self.tr("number_start")))
        self.date_format_label.setText(str(self.tr("date_format")))
        self.preserve_modified_time_checkbox.setText(str(self.tr("preserve_modified_time")))
        self.table.setHorizontalHeaderLabels(self.tr("rename_headers"))
        self.detail_panel.set_language(language)
        self._set_date_format_items(selected_date_format)
        self.refresh_table()
        self.refresh_detail_panel()

    def _set_date_format_items(self, selected: str):
        self.date_format_combo.blockSignals(True)
        self.date_format_combo.clear()
        for key in ("none", "prefix_dash", "prefix_compact", "suffix_dash", "suffix_compact"):
            self.date_format_combo.addItem(str(self.tr(key)), key)
        self.date_format_combo.blockSignals(False)
        self.date_format_combo.setCurrentIndex(self.date_format_combo.findData(selected))

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
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()
        self.refresh_detail_panel()

    def current_options(self) -> RenameOptions:
        return RenameOptions(
            prefix=self.prefix_edit.text(),
            suffix=self.suffix_edit.text(),
            find_text=self.find_edit.text(),
            replace_text=self.replace_edit.text(),
            clean_spaces=self.clean_spaces_checkbox.isChecked(),
            clean_special=self.clean_special_checkbox.isChecked(),
            number_files=self.number_files_checkbox.isChecked(),
            number_start=self.number_start_spin.value(),
            date_format=self.date_format_combo.currentData() or "none",
            preserve_modified_time=self.preserve_modified_time_checkbox.isChecked(),
        )

    def preview_changes(self):
        self.plans = build_rename_plan(self.paths, self.current_options())
        self.refresh_table()
        self.refresh_detail_panel()

    def apply_changes(self):
        if not self.plans:
            self.preview_changes()
        self.plans = apply_rename_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self.paths = [plan.target if plan.status == "completed" else plan.source for plan in self.plans]
        self.refresh_table()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_rename_results(self.last_results)
        self.paths = [plan.source if plan.status == "undone" else plan.target for plan in self.plans]
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self.refresh_detail_panel()

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                values = [
                    plan.source.name,
                    plan.target.name,
                    self.status_text(plan.status),
                    str(plan.target.parent),
                ]
                self._set_row(row, values)
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, "", "", str(path.parent)])
        self.table.resizeColumnsToContents()
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.target,
                status=self.status_text(plan.status),
            )
            return
        self.detail_panel.set_file(self.paths[row])

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if 0 <= row < row_count:
            return row
        return None


class ClassifyToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.output_folder: Path | None = None
        self.plans: list[ClassificationPlan] = []
        self.last_results: list[ClassificationPlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.output_folder_button = QPushButton()
        self.output_folder_label = QLabel()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.table = FileToolTable(4, self.add_paths)
        self.detail_panel = FileDetailPanel(language)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.output_folder_button.clicked.connect(self.pick_output_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_moves)
        self.apply_button.clicked.connect(self.apply_moves)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.output_folder_button)
        actions.addWidget(self.output_folder_label)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.undo_button)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        content_layout.addWidget(self.detail_panel, 1)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.output_folder_button.setText(str(self.tr("select_output_folder_button")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.table.setHorizontalHeaderLabels(self.tr("classify_headers"))
        self.detail_panel.set_language(language)
        self._refresh_output_folder_label()
        self.refresh_table()
        self.refresh_detail_panel()

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

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_output_folder")), "")
        if folder:
            self.set_output_folder(Path(folder))

    def set_output_folder(self, folder: Path):
        self.output_folder = Path(folder)
        self.plans = []
        self._refresh_output_folder_label()
        self.refresh_table()
        self.refresh_detail_panel()

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()
        self.refresh_detail_panel()

    def preview_moves(self):
        if self.output_folder is None:
            self.plans = []
            self.refresh_table()
            self.refresh_detail_panel()
            return
        self.plans = build_classification_plan(self.paths, self.output_folder)
        self.refresh_table()
        self.refresh_detail_panel()

    def apply_moves(self):
        if not self.plans:
            self.preview_moves()
        self.plans = apply_classification_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self.paths = [plan.target if plan.status == "completed" else plan.source for plan in self.plans]
        self.refresh_table()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_classification_results(self.last_results)
        self.paths = [plan.source if plan.status == "undone" else plan.target for plan in self.plans]
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self.refresh_detail_panel()

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                self._set_row(
                    row,
                    [
                        plan.source.name,
                        plan.category,
                        str(plan.target),
                        self.status_text(plan.status),
                    ],
                )
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, "", "", ""])
        self.table.resizeColumnsToContents()
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _refresh_output_folder_label(self):
        if self.output_folder is None:
            self.output_folder_label.setText(str(self.tr("output_folder_missing")))
            return
        self.output_folder_label.setText(str(self.tr("output_folder_selected")).format(path=self.output_folder))

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.target,
                status=self.status_text(plan.status),
            )
            return
        self.detail_panel.set_file(self.paths[row])

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if 0 <= row < row_count:
            return row
        return None


class DateChangeToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.plans: list[DateChangePlan] = []
        self.last_results: list[DateChangePlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.undo_button = QPushButton()
        self.options_group = QGroupBox()
        self.source_mode_label = QLabel()
        self.source_mode_combo = QComboBox()
        self.change_created_checkbox = QCheckBox()
        self.change_modified_checkbox = QCheckBox()
        self.created_input_label = QLabel()
        self.modified_input_label = QLabel()
        self.created_datetime_edit = QDateTimeEdit()
        self.modified_datetime_edit = QDateTimeEdit()
        self.table = FileToolTable(5, self.add_paths)
        self.detail_panel = FileDetailPanel(language)

        for editor in (self.created_datetime_edit, self.modified_datetime_edit):
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            editor.setCalendarPopup(True)
            editor.setDateTime(QDateTime.currentDateTime())
        self.change_created_checkbox.setChecked(True)
        self.change_modified_checkbox.setChecked(True)
        self.undo_button.setEnabled(False)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_changes)
        self.apply_button.clicked.connect(self.apply_changes)
        self.undo_button.clicked.connect(self.undo_last_action)
        self.table.itemSelectionChanged.connect(self.refresh_detail_panel)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.undo_button)

        options_layout = QGridLayout()
        options_layout.addWidget(self.source_mode_label, 0, 0)
        options_layout.addWidget(self.source_mode_combo, 0, 1)
        options_layout.addWidget(self.change_created_checkbox, 0, 2)
        options_layout.addWidget(self.change_modified_checkbox, 0, 3)
        options_layout.addWidget(self.created_input_label, 1, 0)
        options_layout.addWidget(self.created_datetime_edit, 1, 1)
        options_layout.addWidget(self.modified_input_label, 1, 2)
        options_layout.addWidget(self.modified_datetime_edit, 1, 3)
        self.options_group.setLayout(options_layout)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.table, 3)
        content_layout.addWidget(self.detail_panel, 1)

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.options_group)
        layout.addLayout(content_layout)
        self.setLayout(layout)
        self.set_language(language)

    def tr(self, key: str) -> str | list[str]:
        return TRANSLATIONS[self.language][key]

    def set_language(self, language: str):
        self.language = language
        selected_mode = self.source_mode_combo.currentData() or "manual"
        self.add_files_button.setText(str(self.tr("add_files")))
        self.add_folder_button.setText(str(self.tr("add_folder")))
        self.remove_selected_button.setText(str(self.tr("remove_selected")))
        self.clear_list_button.setText(str(self.tr("clear_list")))
        self.preview_button.setText(str(self.tr("preview")))
        self.apply_button.setText(str(self.tr("apply")))
        self.undo_button.setText(str(self.tr("undo")))
        self.options_group.setTitle(str(self.tr("date_change_options")))
        self.source_mode_label.setText(str(self.tr("date_source")))
        self.change_created_checkbox.setText(str(self.tr("change_created")))
        self.change_modified_checkbox.setText(str(self.tr("change_modified")))
        self.created_input_label.setText(str(self.tr("created_input")))
        self.modified_input_label.setText(str(self.tr("modified_input")))
        self.table.setHorizontalHeaderLabels(self.tr("date_headers"))
        self.detail_panel.set_language(language)
        self._set_source_mode_items(selected_mode)
        self.refresh_table()
        self.refresh_detail_panel()

    def _set_source_mode_items(self, selected: str):
        self.source_mode_combo.blockSignals(True)
        self.source_mode_combo.clear()
        for key in ("manual", "filename", "now"):
            self.source_mode_combo.addItem(str(self.tr(key)), key)
        self.source_mode_combo.blockSignals(False)
        self.source_mode_combo.setCurrentIndex(self.source_mode_combo.findData(selected))

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
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def remove_selected_paths(self):
        selected_rows = sorted(
            {index.row() for index in self.table.selectionModel().selectedRows()},
            reverse=True,
        )
        for row in selected_rows:
            if 0 <= row < len(self.paths):
                del self.paths[row]
        self.plans = []
        self.refresh_table()
        self.refresh_detail_panel()

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()
        self.refresh_detail_panel()

    def set_manual_timestamps(self, created: float, modified: float):
        self.source_mode_combo.setCurrentIndex(self.source_mode_combo.findData("manual"))
        self.created_datetime_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(created)))
        self.modified_datetime_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(modified)))

    def preview_changes(self):
        mode = self.source_mode_combo.currentData() or "manual"
        self.plans = build_date_change_plan(
            self.paths,
            created_timestamp=self.created_datetime_edit.dateTime().toSecsSinceEpoch(),
            modified_timestamp=self.modified_datetime_edit.dateTime().toSecsSinceEpoch(),
            from_filename=mode == "filename",
            use_now=mode == "now",
            change_created=self.change_created_checkbox.isChecked(),
            change_modified=self.change_modified_checkbox.isChecked(),
        )
        self.refresh_table()
        self.refresh_detail_panel()

    def apply_changes(self):
        if not self.plans:
            self.preview_changes()
        self.plans = apply_date_change_plan(self.plans)
        self.last_results = self.plans
        self.undo_button.setEnabled(any(plan.status == "completed" for plan in self.last_results))
        self.refresh_table()
        self.refresh_detail_panel()

    def undo_last_action(self):
        self.plans = undo_date_change_results(self.last_results)
        self.undo_button.setEnabled(False)
        self.refresh_table()
        self.refresh_detail_panel()

    def refresh_table(self):
        row_count = len(self.plans) if self.plans else len(self.paths)
        self.table.setRowCount(row_count)
        if self.plans:
            for row, plan in enumerate(self.plans):
                self._set_row(
                    row,
                    [
                        plan.source.name,
                        _format_timestamp(plan.target_timestamps.created),
                        _format_timestamp(plan.target_timestamps.modified),
                        self.status_text(plan.status),
                        str(plan.source.parent),
                    ],
                )
        else:
            for row, path in enumerate(self.paths):
                self._set_row(row, [path.name, "", "", "", str(path.parent)])
        self.table.resizeColumnsToContents()
        self.refresh_detail_panel()

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))

    def refresh_detail_panel(self):
        row = self._selected_row()
        if row is None:
            self.detail_panel.clear()
            return
        if self.plans:
            plan = self.plans[row]
            self.detail_panel.set_file(
                plan.source,
                planned_path=plan.source,
                status=self.status_text(plan.status),
            )
            return
        self.detail_panel.set_file(self.paths[row])

    def _selected_row(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        row_count = len(self.plans) if self.plans else len(self.paths)
        if 0 <= row < row_count:
            return row
        return None


def _expand_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*") if child.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
