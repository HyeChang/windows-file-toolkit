from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
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
    RenameOptions,
    RenamePlan,
    apply_classification_plan,
    apply_rename_plan,
    build_classification_plan,
    build_rename_plan,
)


TRANSLATIONS = {
    "ko": {
        "add_files": "파일 추가",
        "add_folder": "폴더 추가",
        "remove_selected": "선택 삭제",
        "clear_list": "목록 비우기",
        "preview": "미리보기",
        "apply": "적용",
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
        "preserve_modified_time": "수정일 유지",
        "rename_headers": ["원본", "변경 후", "상태", "위치"],
        "classify_headers": ["파일", "분류", "이동 위치", "상태"],
        "select_output_folder_button": "출력 폴더 선택",
        "select_output_folder": "출력 폴더 선택",
        "output_folder_missing": "출력 폴더: 선택 필요",
        "output_folder_selected": "출력 폴더: {path}",
        "ready": "준비",
        "completed": "완료",
        "unchanged": "변경 없음",
        "skipped": "건너뜀",
        "failed": "실패",
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
        "preserve_modified_time": "Preserve modified date",
        "rename_headers": ["Original", "New name", "Status", "Location"],
        "classify_headers": ["File", "Category", "Move to", "Status"],
        "select_output_folder_button": "Select output folder",
        "select_output_folder": "Select output folder",
        "output_folder_missing": "Output folder: required",
        "output_folder_selected": "Output folder: {path}",
        "ready": "Ready",
        "completed": "Completed",
        "unchanged": "Unchanged",
        "skipped": "Skipped",
        "failed": "Failed",
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


class RenameToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.plans: list[RenamePlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
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

        self.number_start_spin.setRange(1, 999999)
        self.number_start_spin.setValue(1)
        self.preserve_modified_time_checkbox.setChecked(True)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_changes)
        self.apply_button.clicked.connect(self.apply_changes)

        actions = QHBoxLayout()
        actions.addWidget(self.add_files_button)
        actions.addWidget(self.add_folder_button)
        actions.addWidget(self.remove_selected_button)
        actions.addWidget(self.clear_list_button)
        actions.addStretch()
        actions.addWidget(self.preview_button)
        actions.addWidget(self.apply_button)

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
        layout.addWidget(self.table)
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
        self._set_date_format_items(selected_date_format)
        self.refresh_table()

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

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()

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

    def apply_changes(self):
        if not self.plans:
            self.preview_changes()
        self.plans = apply_rename_plan(self.plans)
        self.paths = [plan.target if plan.status == "completed" else plan.source for plan in self.plans]
        self.refresh_table()

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

    def status_text(self, status: str) -> str:
        return str(TRANSLATIONS[self.language].get(status, status))

    def _set_row(self, row: int, values: list[str]):
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))


class ClassifyToolWidget(QWidget):
    def __init__(self, language: str = "ko"):
        super().__init__()
        self.language = language
        self.paths: list[Path] = []
        self.output_folder: Path | None = None
        self.plans: list[ClassificationPlan] = []

        self.add_files_button = QPushButton()
        self.add_folder_button = QPushButton()
        self.output_folder_button = QPushButton()
        self.output_folder_label = QLabel()
        self.remove_selected_button = QPushButton()
        self.clear_list_button = QPushButton()
        self.preview_button = QPushButton()
        self.apply_button = QPushButton()
        self.table = FileToolTable(4, self.add_paths)

        self.add_files_button.clicked.connect(self.pick_files)
        self.add_folder_button.clicked.connect(self.pick_folder)
        self.output_folder_button.clicked.connect(self.pick_output_folder)
        self.remove_selected_button.clicked.connect(self.remove_selected_paths)
        self.clear_list_button.clicked.connect(self.clear_paths)
        self.preview_button.clicked.connect(self.preview_moves)
        self.apply_button.clicked.connect(self.apply_moves)

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

        layout = QVBoxLayout()
        layout.addLayout(actions)
        layout.addWidget(self.table)
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
        self.table.setHorizontalHeaderLabels(self.tr("classify_headers"))
        self._refresh_output_folder_label()
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

    def pick_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, str(self.tr("select_output_folder")), "")
        if folder:
            self.set_output_folder(Path(folder))

    def set_output_folder(self, folder: Path):
        self.output_folder = Path(folder)
        self.plans = []
        self._refresh_output_folder_label()
        self.refresh_table()

    def add_paths(self, paths: list[Path]):
        known = set(self.paths)
        for path in _expand_files(paths):
            if path not in known:
                self.paths.append(path)
                known.add(path)
        self.plans = []
        self.refresh_table()

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

    def clear_paths(self):
        self.paths.clear()
        self.plans.clear()
        self.refresh_table()

    def preview_moves(self):
        if self.output_folder is None:
            self.plans = []
            self.refresh_table()
            return
        self.plans = build_classification_plan(self.paths, self.output_folder)
        self.refresh_table()

    def apply_moves(self):
        if not self.plans:
            self.preview_moves()
        self.plans = apply_classification_plan(self.plans)
        self.paths = [plan.target if plan.status == "completed" else plan.source for plan in self.plans]
        self.refresh_table()

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


def _expand_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.extend(sorted(child for child in path.rglob("*") if child.is_file()))
        elif path.is_file():
            files.append(path)
    return files
