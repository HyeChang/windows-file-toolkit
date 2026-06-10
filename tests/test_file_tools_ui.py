from datetime import datetime
import os
from pathlib import Path
import shutil

from PySide6.QtCore import QMimeData, Qt, QUrl
from PySide6.QtWidgets import QApplication, QDialog, QGridLayout, QHeaderView
from PIL import Image

from file_compressor.dependencies import DependencyStatus
from file_compressor.file_tools import get_file_timestamps, set_file_timestamps
from file_compressor_app.file_tools_ui import FolderSelectionDialog
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


def make_window(monkeypatch) -> MainWindow:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr(
        "file_compressor_app.ui.detect_ghostscript",
        lambda: DependencyStatus(False),
    )
    monkeypatch.setattr("file_compressor_app.ui.default_excel_available", lambda: False)
    monkeypatch.setattr("file_compressor_app.ui.default_powerpoint_available", lambda: False)
    monkeypatch.setattr("file_compressor_app.ui.default_hancom_available", lambda: False)
    app()
    return MainWindow()


def tab_labels(window: MainWindow) -> list[str]:
    return [window.tabs.tabText(index) for index in range(window.tabs.count())]


class FakeDropEvent:
    def __init__(self, paths: list[Path]):
        self._mime_data = QMimeData()
        self._mime_data.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
        self.accepted = False

    def mimeData(self):
        return self._mime_data

    def acceptProposedAction(self):
        self.accepted = True


def test_main_window_separates_features_into_localized_tabs(monkeypatch):
    window = make_window(monkeypatch)

    assert tab_labels(window) == [
        "문서 압축",
        "파일 이름 변경",
        "파일 자동 분류",
        "파일 날짜 변경",
        "이미지 회전",
        "이미지 비율 분류",
        "PDF 도구",
        "파일 내용 검색",
    ]
    assert window.classify_tab.operation_label.text() == "작업"
    assert window.classify_tab.operation_combo.itemText(
        window.classify_tab.operation_combo.findData("copy")
    ) == "복사"
    assert window.classify_tab.strategy_label.text() == "분류 기준"
    assert window.classify_tab.strategy_combo.itemText(
        window.classify_tab.strategy_combo.findData("name_similarity")
    ) == "파일명 유사도 기준"
    assert window.classify_tab.sensitivity_label.text() == "민감도"
    assert [
        window.classify_tab.sensitivity_combo.itemText(index)
        for index in range(window.classify_tab.sensitivity_combo.count())
    ] == ["느슨", "약간 느슨", "보통", "약간 엄격", "엄격"]
    assert [
        window.classify_tab.sensitivity_combo.itemData(index)
        for index in range(window.classify_tab.sensitivity_combo.count())
    ] == ["loose", "medium_loose", "normal", "medium_strict", "strict"]
    window.classify_tab.sensitivity_combo.setCurrentIndex(
        window.classify_tab.sensitivity_combo.findData("medium_loose")
    )

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert tab_labels(window) == [
        "Compression",
        "Rename",
        "Classify",
        "Dates",
        "Image Rotate",
        "Image Ratio",
        "PDF Tools",
        "Search",
    ]
    assert window.rename_tab.add_files_button.text() == "Add files"
    assert window.classify_tab.output_folder_button.text() == "Select output folder"
    assert window.classify_tab.operation_label.text() == "Operation"
    assert window.classify_tab.operation_combo.itemText(
        window.classify_tab.operation_combo.findData("copy")
    ) == "Copy"
    assert window.classify_tab.strategy_label.text() == "Classify by"
    assert window.classify_tab.strategy_combo.itemText(
        window.classify_tab.strategy_combo.findData("name_similarity")
    ) == "Similar file names"
    assert window.classify_tab.sensitivity_label.text() == "Sensitivity"
    assert [
        window.classify_tab.sensitivity_combo.itemText(index)
        for index in range(window.classify_tab.sensitivity_combo.count())
    ] == ["Loose", "Slightly loose", "Normal", "Slightly strict", "Strict"]
    assert window.classify_tab.sensitivity_combo.currentData() == "medium_loose"
    assert window.date_tab.add_files_button.text() == "Add files"
    assert window.image_rotate_tab.add_files_button.text() == "Add files"
    assert window.image_ratio_tab.add_files_button.text() == "Add files"


def test_rename_tab_previews_file_name_suffix_compact_date(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-preview")
    source = workdir / "2026.04.27_회의록.pdf"
    source.write_bytes(b"pdf")

    window.rename_tab.add_paths([source])
    assert window.rename_tab.date_format_combo.itemText(
        window.rename_tab.date_format_combo.findData("suffix_compact")
    ) == "파일명_YYYYMMDD"
    assert window.rename_tab.date_format_combo.itemText(
        window.rename_tab.date_format_combo.findData("suffix_short_compact")
    ) == "파일명_YYMMDD"
    assert window.rename_tab.date_format_combo.itemText(
        window.rename_tab.date_format_combo.findData("prefix_short_compact")
    ) == "YYMMDD_파일명"
    assert window.rename_tab.date_format_combo.itemText(
        window.rename_tab.date_format_combo.findData("prefix_underscore")
    ) == "YYYY_MM_DD_파일명"
    assert window.rename_tab.date_fallback_label.text() == "날짜 없을 때"
    assert window.rename_tab.date_fallback_combo.itemText(
        window.rename_tab.date_fallback_combo.findData("modified")
    ) == "수정일 사용"
    window.rename_tab.date_format_combo.setCurrentIndex(
        window.rename_tab.date_format_combo.findData("suffix_compact")
    )
    window.rename_tab.preview_changes()

    assert window.rename_tab.table.item(0, 0).text() == source.name
    assert window.rename_tab.table.item(0, 1).text() == "회의록_20260427.pdf"
    assert window.rename_tab.table.item(0, 2).text() == "준비"


def test_rename_tab_can_add_modified_date_when_name_has_no_date(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-fallback-modified")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    modified = datetime(2024, 7, 18, 9, 10, 11).timestamp()
    os.utime(source, (modified, modified))

    window.rename_tab.add_paths([source])
    window.rename_tab.date_format_combo.setCurrentIndex(
        window.rename_tab.date_format_combo.findData("prefix_underscore")
    )
    window.rename_tab.date_fallback_combo.setCurrentIndex(
        window.rename_tab.date_fallback_combo.findData("modified")
    )
    window.rename_tab.preview_changes()

    assert window.rename_tab.table.item(0, 1).text() == "2024_07_18_보고서.pdf"
    assert window.rename_tab.table.item(0, 2).text() == "준비"


def test_file_tool_tables_keep_horizontal_scroll_with_long_names(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-long-file-table")
    long_folder = workdir / ("프로젝트_" + "긴경로_" * 8)
    long_folder.mkdir()
    source = long_folder / ("아주_긴_파일명_" + "확인_" * 10 + ".pptx")
    source.write_bytes(b"pptx")

    window.rename_tab.add_paths([source])
    window.rename_tab.suffix_edit.setText("_변경")
    window.rename_tab.preview_changes()

    rename_header = window.rename_tab.table.horizontalHeader()
    assert rename_header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
    assert rename_header.sectionResizeMode(1) == QHeaderView.ResizeMode.Interactive
    assert rename_header.sectionResizeMode(3) == QHeaderView.ResizeMode.Interactive
    assert window.rename_tab.table.columnWidth(0) >= 260
    assert window.rename_tab.table.columnWidth(1) >= 260
    assert window.rename_tab.table.columnWidth(3) >= 520
    assert window.rename_tab.table.item(0, 0).toolTip() == source.name
    assert window.rename_tab.table.item(0, 3).toolTip() == str(source.parent)

    window.classify_tab.set_output_folder(workdir / "sorted")
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    classify_header = window.classify_tab.table.horizontalHeader()
    assert classify_header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
    assert classify_header.sectionResizeMode(2) == QHeaderView.ResizeMode.Interactive
    assert window.classify_tab.table.columnWidth(0) >= 260
    assert window.classify_tab.table.columnWidth(2) <= 360

    window.date_tab.add_paths([source])
    window.date_tab.preview_changes()
    date_header = window.date_tab.table.horizontalHeader()
    assert date_header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive
    assert date_header.sectionResizeMode(4) == QHeaderView.ResizeMode.Interactive
    assert window.date_tab.table.columnWidth(0) >= 260
    assert window.date_tab.table.columnWidth(4) >= 520


def test_rename_tab_apply_preserves_modified_time(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-apply")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    original_mtime = 1_700_000_000
    os.utime(source, (original_mtime, original_mtime))

    window.rename_tab.add_paths([source])
    window.rename_tab.suffix_edit.setText("_완료")
    window.rename_tab.preview_changes()
    window.rename_tab.apply_changes()

    target = workdir / "보고서_완료.pdf"
    assert target.exists()
    assert not source.exists()
    assert abs(target.stat().st_mtime - original_mtime) < 1
    assert window.rename_tab.table.item(0, 2).text() == "완료"


def test_classify_tab_previews_category_targets(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-preview")
    output_root = workdir / "sorted"
    pdf = workdir / "보고서.pdf"
    xlsx = workdir / "예산.xlsx"
    pdf.write_bytes(b"pdf")
    xlsx.write_bytes(b"xlsx")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([pdf, xlsx])
    window.classify_tab.preview_moves()

    assert window.classify_tab.output_folder_label.text() == f"출력 폴더: {output_root}"
    assert window.classify_tab.table.item(0, 0).text() == "보고서.pdf"
    assert window.classify_tab.table.item(0, 1).text() == "3 B"
    assert window.classify_tab.table.item(0, 2).text() == "PDF"
    assert window.classify_tab.table.item(0, 3).text() == "PDF"
    assert window.classify_tab.table.item(0, 3).toolTip() == str(output_root / "PDF" / "보고서.pdf")
    assert window.classify_tab.table.item(1, 2).text() == "Excel"


def test_classify_tab_skips_category_folder_for_single_file_by_default(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-single-file-no-folder")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()

    assert window.classify_tab.skip_single_file_folder_checkbox.text() == "단일 파일은 폴더 생성 안 함"
    assert window.classify_tab.skip_single_file_folder_checkbox.isChecked() is True
    assert window.classify_tab.table.item(0, 2).text() == "PDF"
    assert window.classify_tab.table.item(0, 3).text() == "sorted"
    assert window.classify_tab.table.item(0, 3).toolTip() == str(output_root / "보고서.pdf")


def test_classify_tab_can_keep_category_folder_for_single_file(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-single-file-folder-enabled")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.skip_single_file_folder_checkbox.setChecked(False)
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()

    assert window.classify_tab.table.item(0, 3).text() == "PDF"
    assert window.classify_tab.table.item(0, 3).toolTip() == str(output_root / "PDF" / "보고서.pdf")


def test_classify_tab_marks_existing_identical_output_as_duplicate(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-duplicate-existing")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    target = output_root / "보고서.pdf"
    target.parent.mkdir(parents=True)
    source.write_bytes(b"same")
    target.write_bytes(b"same")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    window.classify_tab.apply_moves()

    assert window.classify_tab.table.item(0, 3).toolTip() == str(target)
    assert window.classify_tab.table.item(0, 4).text() == "중복 파일"
    assert window.classify_tab.table.item(0, 4).toolTip() == (
        f"중복 발생\n원본: {source}\n기존 파일: {target}\n처리: 미삭제(기존 파일 유지)"
    )
    window.classify_tab.table.selectRow(0)
    assert window.classify_tab.detail_panel.value_text("status") == (
        f"중복 발생\n원본: {source}\n기존 파일: {target}\n처리: 미삭제(기존 파일 유지)"
    )
    assert source.exists()
    assert target.read_bytes() == b"same"
    assert not (output_root / "보고서_2.pdf").exists()


def test_classify_tab_can_delete_existing_identical_duplicate(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-duplicate-delete")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    target = output_root / "보고서.pdf"
    target.parent.mkdir(parents=True)
    source.write_bytes(b"same")
    target.write_bytes(b"same")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.duplicate_action_combo.setCurrentIndex(
        window.classify_tab.duplicate_action_combo.findData("delete")
    )
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    window.classify_tab.apply_moves()

    assert window.classify_tab.duplicate_action_label.text() == "중복 파일"
    assert window.classify_tab.duplicate_action_combo.currentText() == "삭제"
    assert window.classify_tab.table.item(0, 4).text() == "중복 삭제"
    assert window.classify_tab.table.item(0, 4).toolTip() == (
        f"중복 처리\n원본: {source}\n기존 파일: {target}\n처리: 삭제(원본 중복 파일 삭제)"
    )
    window.classify_tab.table.selectRow(0)
    assert window.classify_tab.detail_panel.value_text("status") == (
        f"중복 처리\n원본: {source}\n기존 파일: {target}\n처리: 삭제(원본 중복 파일 삭제)"
    )
    assert not source.exists()
    assert target.read_bytes() == b"same"
    assert not (output_root / "보고서_2.pdf").exists()


def test_classify_tab_shows_folder_summary_and_selected_target_folder(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-folder-summary")
    output_root = workdir / "sorted"
    pdf_a = workdir / "보고서.pdf"
    pdf_b = workdir / "검토.pdf"
    xlsx = workdir / "예산.xlsx"
    for source in (pdf_a, pdf_b, xlsx):
        source.write_bytes(b"file")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([pdf_a, pdf_b, xlsx])
    window.classify_tab.preview_moves()

    assert window.classify_tab.folder_summary_label.text() == "생성 폴더 2개 / 배치 파일 3개"
    assert window.classify_tab.folder_summary_table.rowCount() == 2
    assert {
        window.classify_tab.folder_summary_table.item(row, 0).text()
        for row in range(window.classify_tab.folder_summary_table.rowCount())
    } == {"PDF", "Excel"}
    assert {
        window.classify_tab.folder_summary_table.item(row, 0).toolTip()
        for row in range(window.classify_tab.folder_summary_table.rowCount())
    } == {str(output_root / "PDF"), str(output_root / "Excel")}
    assert {
        window.classify_tab.folder_summary_table.item(row, 1).text()
        for row in range(window.classify_tab.folder_summary_table.rowCount())
    } == {"2", "1"}

    window.classify_tab.table.selectRow(0)

    assert window.classify_tab.selected_target_folder_label.text() == f"선택 대상 폴더: {output_root / 'PDF'}"


def test_classify_tab_shows_files_when_summary_folder_is_clicked(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-folder-summary-files")
    output_root = workdir / "sorted"
    pdf_a = workdir / "보고서.pdf"
    pdf_b = workdir / "검토.pdf"
    xlsx = workdir / "예산.xlsx"
    for source in (pdf_a, pdf_b, xlsx):
        source.write_bytes(b"file")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([pdf_a, pdf_b, xlsx])
    window.classify_tab.preview_moves()
    pdf_row = next(
        row
        for row in range(window.classify_tab.folder_summary_table.rowCount())
        if window.classify_tab.folder_summary_table.item(row, 0).text() == "PDF"
    )

    window.classify_tab.folder_summary_table.selectRow(pdf_row)

    assert window.classify_tab.folder_summary_files_label.text() == "PDF 파일 2개"
    assert window.classify_tab.folder_summary_files_table.rowCount() == 2
    assert {
        window.classify_tab.folder_summary_files_table.item(row, 0).text()
        for row in range(window.classify_tab.folder_summary_files_table.rowCount())
    } == {"보고서.pdf", "검토.pdf"}
    assert {
        window.classify_tab.folder_summary_files_table.item(row, 1).toolTip()
        for row in range(window.classify_tab.folder_summary_files_table.rowCount())
    } == {str(output_root / "PDF" / "보고서.pdf"), str(output_root / "PDF" / "검토.pdf")}


def test_classify_summary_disambiguates_duplicate_folder_names(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-duplicate-summary-names")
    left = workdir / "왼쪽" / "유니투스 회의.pdf"
    right = workdir / "오른쪽" / "유니투스 회의.xlsx"
    left.parent.mkdir()
    right.parent.mkdir()
    left.write_bytes(b"pdf")
    right.write_bytes(b"xlsx")

    window.classify_tab.strategy_combo.setCurrentIndex(
        window.classify_tab.strategy_combo.findData("name_similarity")
    )
    window.classify_tab.add_paths([left, right])
    window.classify_tab.preview_moves()

    summary_names = [
        window.classify_tab.folder_summary_table.item(row, 0).text()
        for row in range(window.classify_tab.folder_summary_table.rowCount())
    ]

    assert len(summary_names) == 2
    assert len(set(summary_names)) == 2
    assert any("왼쪽" in name for name in summary_names)
    assert any("오른쪽" in name for name in summary_names)


def test_classify_tab_can_open_large_folder_summary(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-large-summary")
    output_root = workdir / "sorted"
    pdf = workdir / "보고서.pdf"
    xlsx = workdir / "예산.xlsx"
    pdf.write_bytes(b"pdf")
    xlsx.write_bytes(b"xlsx")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([pdf, xlsx])
    window.classify_tab.preview_moves()

    dialog = window.classify_tab.create_folder_summary_dialog()

    assert window.classify_tab.folder_summary_expand_button.text() == "크게 보기"
    assert dialog.windowTitle() == "분류 요약"
    assert dialog.summary_label.text() == "생성 폴더 2개 / 배치 파일 2개"
    assert dialog.table.rowCount() == 2
    assert dialog.minimumWidth() >= 700
    pdf_row = next(
        row
        for row in range(dialog.table.rowCount())
        if dialog.table.item(row, 0).text() == "PDF"
    )

    dialog.table.selectRow(pdf_row)

    assert dialog.files_label.text() == "PDF 파일 1개"
    assert dialog.files_table.rowCount() == 1
    assert dialog.files_table.item(0, 0).text() == "보고서.pdf"
    assert dialog.files_table.item(0, 1).toolTip() == str(output_root / "PDF" / "보고서.pdf")


def test_classify_tab_uses_auto_organized_folder_when_output_folder_missing(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-auto-output")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    (workdir / "정리").mkdir()

    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()

    target = workdir / "정리_1" / "보고서.pdf"
    assert window.classify_tab.output_folder_label.text() == "출력 폴더: 원본 폴더에 정리 폴더 자동 생성"
    assert window.classify_tab.plans[0].target == target
    assert window.classify_tab.table.item(0, 3).toolTip() == str(target)


def test_classify_tab_uses_selected_top_folder_for_auto_organized_output(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-auto-output-selected-root")
    root = workdir / "root"
    nested = root / "nested"
    deeper = nested / "deeper"
    deeper.mkdir(parents=True)
    pdf = nested / "보고서.pdf"
    xlsx = deeper / "예산.xlsx"
    pdf.write_bytes(b"pdf")
    xlsx.write_bytes(b"xlsx")

    class FakeFolderSelectionDialog:
        def __init__(self, folder, language, parent=None):
            self.folder = Path(folder)

        def exec(self):
            return QDialog.DialogCode.Accepted

        def selected_files(self):
            return [pdf, xlsx]

    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.QFileDialog.getExistingDirectory",
        lambda *args: str(root),
    )
    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.FolderSelectionDialog",
        FakeFolderSelectionDialog,
    )

    window.classify_tab.pick_folder()
    window.classify_tab.preview_moves()

    assert window.classify_tab.plans[0].target == root / "정리" / "PDF" / "보고서.pdf"
    assert window.classify_tab.plans[1].target == root / "정리" / "Excel" / "예산.xlsx"


def test_classify_tab_can_toggle_size_column(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-size-column")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.add_paths([source])

    assert window.classify_tab.table.horizontalHeaderItem(1).text() == "크기"
    assert window.classify_tab.table.item(0, 1).text() == "3 B"

    window.classify_tab.show_size_checkbox.setChecked(False)

    assert window.classify_tab.table.isColumnHidden(1) is True


def test_classify_tab_add_folder_can_exclude_subfolders(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-folder-filter")
    root = workdir / "root"
    keep = root / "keep"
    skip = root / "skip"
    keep.mkdir(parents=True)
    skip.mkdir()
    root_file = root / "root.xlsx"
    keep_file = keep / "keep.pdf"
    skip_file = skip / "skip.pdf"
    for source in (root_file, keep_file, skip_file):
        source.write_bytes(b"file")

    class FakeFolderSelectionDialog:
        def __init__(self, folder, language, parent=None):
            self.folder = folder
            self.language = language
            self.parent = parent

        def exec(self):
            return QDialog.DialogCode.Accepted

        def selected_files(self):
            return [root_file, keep_file]

    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.QFileDialog.getExistingDirectory",
        lambda *args: str(root),
    )
    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.FolderSelectionDialog",
        FakeFolderSelectionDialog,
    )

    window.classify_tab.pick_folder()

    assert window.classify_tab.paths == [root_file, keep_file]


def test_folder_selection_unchecking_child_keeps_ancestors_checked(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    workdir = case_dir("ui-folder-selection-child-only")
    root = workdir / "root"
    parent = root / "parent"
    common = parent / "common"
    production = parent / "production"
    quality = parent / "quality"
    for folder in (common, production, quality):
        folder.mkdir(parents=True)
    root_file = root / "root.xlsx"
    common_file = common / "common.pdf"
    production_file = production / "production.pdf"
    quality_file = quality / "quality.pdf"
    for source in (root_file, common_file, production_file, quality_file):
        source.write_bytes(b"file")

    dialog = FolderSelectionDialog(root, "ko")
    root_item = dialog.tree.topLevelItem(0)
    parent_item = _find_folder_item(root_item, parent)
    production_item = _find_folder_item(root_item, production)

    production_item.setCheckState(0, Qt.CheckState.Unchecked)

    assert root_item.checkState(0) == Qt.CheckState.Checked
    assert parent_item.checkState(0) == Qt.CheckState.Checked
    assert production_item.checkState(0) == Qt.CheckState.Unchecked
    assert set(dialog.selected_files()) == {root_file, common_file, quality_file}


def _find_folder_item(item, folder: Path):
    if Path(item.data(0, Qt.ItemDataRole.UserRole)) == folder:
        return item
    for index in range(item.childCount()):
        found = _find_folder_item(item.child(index), folder)
        if found is not None:
            return found
    return None


def test_classify_tab_uses_compact_grid_controls_for_small_windows(monkeypatch):
    window = make_window(monkeypatch)

    controls_layout = window.classify_tab.controls_group.layout()

    assert isinstance(controls_layout, QGridLayout)
    assert controls_layout.rowCount() >= 3
    assert window.classify_tab.output_folder_label.wordWrap() is True


def test_classify_tab_can_preview_similar_file_name_groups(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-name-similarity")
    output_root = workdir / "sorted"
    quote_pdf = workdir / "2026_견적서_ABC.pdf"
    quote_xlsx = workdir / "ABC 견적서 최종.xlsx"
    meeting_docx = workdir / "회의록_2026-05-01.docx"
    meeting_pdf = workdir / "회의록 2026.05.02.pdf"
    for source in (quote_pdf, quote_xlsx, meeting_docx, meeting_pdf):
        source.write_bytes(b"file")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.strategy_combo.setCurrentIndex(
        window.classify_tab.strategy_combo.findData("name_similarity")
    )
    window.classify_tab.add_paths([quote_pdf, quote_xlsx, meeting_docx, meeting_pdf])
    window.classify_tab.preview_moves()

    assert window.classify_tab.table.item(0, 2).text() == window.classify_tab.table.item(1, 2).text()
    assert window.classify_tab.table.item(2, 2).text() == window.classify_tab.table.item(3, 2).text()
    assert window.classify_tab.table.item(0, 2).text() != window.classify_tab.table.item(2, 2).text()
    assert "Excel" not in window.classify_tab.table.item(1, 2).text()


def test_classify_tab_prefers_existing_similar_output_folder(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-existing-similar-folder")
    output_root = workdir / "sorted"
    existing_folder = output_root / "유니투스 회의 파일"
    existing_folder.mkdir(parents=True)
    meeting_txt = workdir / "시간별 회의결과.txt"
    kickoff_pptx = workdir / "유니투스(주)킥오프 화상(0429).pptx"
    meeting_txt.write_bytes(b"meeting")
    kickoff_pptx.write_bytes(b"deck")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.strategy_combo.setCurrentIndex(
        window.classify_tab.strategy_combo.findData("name_similarity")
    )
    window.classify_tab.add_paths([meeting_txt, kickoff_pptx])
    window.classify_tab.preview_moves()

    assert window.classify_tab.prefer_existing_folders_checkbox.text() == "기존 유사 폴더 우선 사용"
    assert window.classify_tab.prefer_existing_folders_checkbox.isChecked() is True
    assert window.classify_tab.table.item(0, 2).text() == "유니투스 회의 파일"
    assert window.classify_tab.table.item(0, 3).text() == "유니투스 회의 파일"
    assert window.classify_tab.table.item(0, 3).toolTip() == str(existing_folder / "시간별 회의결과.txt")
    assert window.classify_tab.table.item(1, 3).toolTip() == str(existing_folder / "유니투스(주)킥오프 화상(0429).pptx")


def test_classify_tab_opens_popup_to_choose_ambiguous_existing_folder(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-ambiguous-existing-folder")
    output_root = workdir / "sorted"
    left = output_root / "오류 정리 문서"
    right = output_root / "오류 정리 자료"
    left.mkdir(parents=True)
    right.mkdir()
    source = workdir / "프로토타입 오류 정리_Ver.260513.pptx"
    source.write_bytes(b"deck")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.strategy_combo.setCurrentIndex(
        window.classify_tab.strategy_combo.findData("name_similarity")
    )
    window.classify_tab.skip_single_file_folder_checkbox.setChecked(False)
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()

    assert window.classify_tab.table.item(0, 4).text() == "선택 필요"
    assert window.classify_tab.table.item(0, 3).text() == "선택 필요"
    assert window.classify_tab.apply_button.isEnabled() is False
    assert not hasattr(window.classify_tab, "candidate_group")

    dialog = window.classify_tab.create_candidate_dialog(0)

    assert dialog.windowTitle() == "후보 폴더 선택"
    assert dialog.candidate_table.rowCount() == 3
    assert dialog.candidate_table.item(0, 0).text() == "오류 정리 문서"
    assert dialog.candidate_table.item(1, 0).text() == "오류 정리 자료"
    assert "새 폴더 생성" in dialog.candidate_table.item(2, 0).text()
    assert dialog.candidate_table.item(0, 0).toolTip() == str(left)
    assert dialog.candidate_table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert dialog.file_table.rowCount() == 1
    assert dialog.file_table.item(0, 0).checkState() == Qt.CheckState.Checked

    dialog.candidate_table.selectRow(1)
    window.classify_tab.apply_candidate_dialog_choice(dialog)

    assert window.classify_tab.table.item(0, 4).text() == "준비"
    assert window.classify_tab.table.item(0, 2).text() == "오류 정리 자료"
    assert window.classify_tab.table.item(0, 3).toolTip() == str(right / source.name)
    assert window.classify_tab.apply_button.isEnabled() is True


def test_classify_tab_candidate_popup_defaults_to_current_file_only(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-candidate-current-only")
    output_root = workdir / "sorted"
    left = output_root / "오류 정리 문서"
    right = output_root / "오류 정리 자료"
    left.mkdir(parents=True)
    right.mkdir()
    source_a = workdir / "프로토타입 오류 정리_A.pptx"
    source_b = workdir / "프로토타입 오류 정리_B.pdf"
    source_a.write_bytes(b"a")
    source_b.write_bytes(b"b")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.strategy_combo.setCurrentIndex(
        window.classify_tab.strategy_combo.findData("name_similarity")
    )
    window.classify_tab.add_paths([source_a, source_b])
    window.classify_tab.preview_moves()

    dialog = window.classify_tab.create_candidate_dialog(1)

    assert dialog.file_table.rowCount() == 2
    assert dialog.file_table.item(0, 0).checkState() == Qt.CheckState.Unchecked
    assert dialog.file_table.item(1, 0).checkState() == Qt.CheckState.Checked

    dialog.candidate_table.selectRow(1)
    window.classify_tab.apply_candidate_dialog_choice(dialog)

    assert window.classify_tab.plans[0].status == "needs_choice"
    assert window.classify_tab.plans[1].status == "ready"
    assert window.classify_tab.plans[1].target == right / source_b.name
    assert window.classify_tab.apply_button.isEnabled() is False


def test_classify_tab_copies_files_when_copy_operation_is_selected(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-copy")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.operation_combo.setCurrentIndex(
        window.classify_tab.operation_combo.findData("copy")
    )
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    window.classify_tab.apply_moves()

    target = output_root / "보고서.pdf"
    assert source.read_bytes() == b"pdf"
    assert target.read_bytes() == b"pdf"
    assert window.classify_tab.paths == [source]
    assert window.classify_tab.table.item(0, 4).text() == "완료"

    window.classify_tab.undo_last_action()

    assert source.read_bytes() == b"pdf"
    assert not target.exists()
    assert window.classify_tab.table.item(0, 4).text() == "되돌림"


def test_classify_tab_copy_single_file_skip_ignores_existing_category_folder(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-copy-single-skip-existing-folder")
    output_root = workdir / "sorted"
    existing_category_folder = output_root / "PDF"
    existing_category_folder.mkdir(parents=True)
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.operation_combo.setCurrentIndex(
        window.classify_tab.operation_combo.findData("copy")
    )
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    window.classify_tab.apply_moves()

    target = output_root / "보고서.pdf"
    assert window.classify_tab.skip_single_file_folder_checkbox.isChecked() is True
    assert target.read_bytes() == b"pdf"
    assert not (existing_category_folder / "보고서.pdf").exists()
    assert window.classify_tab.table.item(0, 3).toolTip() == str(target)


def test_rename_tab_accepts_dropped_files_and_folders(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-drop")
    source = workdir / "보고서.pdf"
    nested = workdir / "folder" / "nested.xlsx"
    nested.parent.mkdir()
    source.write_bytes(b"pdf")
    nested.write_bytes(b"xlsx")

    event = FakeDropEvent([source, nested.parent])
    assert window.rename_tab.table.acceptDrops() is True

    window.rename_tab.table.dropEvent(event)

    assert event.accepted is True
    assert window.rename_tab.paths == [source, nested]
    assert window.rename_tab.table.item(0, 0).text() == "보고서.pdf"
    assert window.rename_tab.table.item(1, 0).text() == "nested.xlsx"


def test_classify_tab_accepts_dropped_files_and_clears_preview(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-drop")
    output_root = workdir / "sorted"
    first = workdir / "first.pdf"
    second = workdir / "second.xlsx"
    first.write_bytes(b"pdf")
    second.write_bytes(b"xlsx")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([first])
    window.classify_tab.preview_moves()
    assert window.classify_tab.plans

    event = FakeDropEvent([second])
    assert window.classify_tab.table.acceptDrops() is True
    window.classify_tab.table.dropEvent(event)

    assert event.accepted is True
    assert window.classify_tab.paths == [first, second]
    assert window.classify_tab.plans == []
    assert window.classify_tab.table.item(1, 0).text() == "second.xlsx"


def test_rename_tab_detail_panel_shows_selected_file_and_plan(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-detail")
    source = workdir / "2026.04.27_회의록.pdf"
    source.write_bytes(b"pdf")

    window.rename_tab.add_paths([source])
    window.rename_tab.date_format_combo.setCurrentIndex(
        window.rename_tab.date_format_combo.findData("suffix_compact")
    )
    window.rename_tab.preview_changes()
    window.rename_tab.table.selectRow(0)

    assert window.rename_tab.detail_panel.value_text("file_name") == "2026.04.27_회의록.pdf"
    assert window.rename_tab.detail_panel.value_text("extension") == ".pdf"
    assert window.rename_tab.detail_panel.value_text("planned_path") == str(workdir / "회의록_20260427.pdf")
    assert window.rename_tab.detail_panel.value_text("status") == "준비"


def test_classify_tab_detail_panel_shows_selected_file_and_destination(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-detail")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    window.classify_tab.table.selectRow(0)

    assert window.classify_tab.detail_panel.value_text("file_name") == "보고서.pdf"
    assert window.classify_tab.detail_panel.value_text("extension") == ".pdf"
    assert window.classify_tab.detail_panel.value_text("planned_path") == str(output_root / "보고서.pdf")
    assert window.classify_tab.detail_panel.value_text("status") == "준비"


def test_rename_tab_undo_restores_last_applied_rename(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-undo")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.rename_tab.add_paths([source])
    window.rename_tab.suffix_edit.setText("_완료")
    window.rename_tab.preview_changes()
    window.rename_tab.apply_changes()
    target = workdir / "보고서_완료.pdf"

    assert target.exists()
    assert window.rename_tab.undo_button.isEnabled() is True

    window.rename_tab.undo_last_action()

    assert source.exists()
    assert not target.exists()
    assert window.rename_tab.table.item(0, 2).text() == "되돌림"
    assert window.rename_tab.undo_button.isEnabled() is False


def test_classify_tab_undo_restores_last_applied_move(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-classify-undo")
    output_root = workdir / "sorted"
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")

    window.classify_tab.set_output_folder(output_root)
    window.classify_tab.add_paths([source])
    window.classify_tab.preview_moves()
    window.classify_tab.apply_moves()
    target = output_root / "보고서.pdf"

    assert target.exists()
    assert window.classify_tab.undo_button.isEnabled() is True

    window.classify_tab.undo_last_action()

    assert source.exists()
    assert not target.exists()
    assert window.classify_tab.table.item(0, 4).text() == "되돌림"
    assert window.classify_tab.undo_button.isEnabled() is False


def test_date_tab_previews_manual_created_and_modified_dates(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-date-preview")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    created = datetime(2025, 5, 6, 7, 8, 9).timestamp()
    modified = datetime(2025, 6, 7, 8, 9, 10).timestamp()

    window.date_tab.add_paths([source])
    window.date_tab.set_manual_timestamps(created, modified)
    window.date_tab.preview_changes()

    assert window.date_tab.table.item(0, 0).text() == "보고서.pdf"
    assert window.date_tab.table.item(0, 1).text() == "2025-05-06 07:08:09"
    assert window.date_tab.table.item(0, 2).text() == "2025-06-07 08:09:10"
    assert window.date_tab.table.item(0, 3).text() == "준비"


def test_date_tab_can_use_date_extracted_from_file_name(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-date-filename")
    source = workdir / "회의록_20260427.pdf"
    source.write_bytes(b"pdf")

    window.date_tab.add_paths([source])
    window.date_tab.source_mode_combo.setCurrentIndex(
        window.date_tab.source_mode_combo.findData("filename")
    )
    window.date_tab.preview_changes()

    assert window.date_tab.table.item(0, 1).text() == "2026-04-27 00:00:00"
    assert window.date_tab.table.item(0, 2).text() == "2026-04-27 00:00:00"


def test_date_tab_apply_and_undo_restore_timestamps(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-date-apply-undo")
    source = workdir / "보고서.pdf"
    source.write_bytes(b"pdf")
    original_created = datetime(2023, 1, 1, 9, 0, 0).timestamp()
    original_modified = datetime(2023, 1, 2, 9, 0, 0).timestamp()
    set_file_timestamps(source, created=original_created, modified=original_modified)
    new_created = datetime(2025, 5, 6, 7, 8, 9).timestamp()
    new_modified = datetime(2025, 6, 7, 8, 9, 10).timestamp()

    window.date_tab.add_paths([source])
    window.date_tab.set_manual_timestamps(new_created, new_modified)
    window.date_tab.preview_changes()
    window.date_tab.apply_changes()

    changed = get_file_timestamps(source)
    assert abs(changed.created - new_created) < 2
    assert abs(changed.modified - new_modified) < 2
    assert window.date_tab.undo_button.isEnabled() is True

    window.date_tab.undo_last_action()

    restored = get_file_timestamps(source)
    assert abs(restored.created - original_created) < 2
    assert abs(restored.modified - original_modified) < 2
    assert window.date_tab.table.item(0, 3).text() == "되돌림"
    assert window.date_tab.undo_button.isEnabled() is False


def test_image_rotate_tab_previews_and_applies_png_rotation(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-rotate-png")
    source = workdir / "sample.png"
    Image.new("RGB", (4, 2), "red").save(source)

    window.image_rotate_tab.add_paths([source])
    window.image_rotate_tab.rotation_combo.setCurrentIndex(
        window.image_rotate_tab.rotation_combo.findData(90)
    )
    window.image_rotate_tab.preview_rotations()

    target = workdir / "sample_rotated.png"
    assert window.image_rotate_tab.table.item(0, 0).text() == "sample.png"
    assert window.image_rotate_tab.table.item(0, 1).text() == "오른쪽 90도"
    assert window.image_rotate_tab.table.item(0, 2).text() == "준비"
    assert window.image_rotate_tab.table.item(0, 3).text() == str(target)

    window.image_rotate_tab.apply_rotations()

    assert source.exists()
    assert target.exists()
    with Image.open(target) as rotated:
        assert rotated.size == (2, 4)
    assert window.image_rotate_tab.table.item(0, 2).text() == "완료"
    assert window.image_rotate_tab.status_label.text() == "처리 결과: 완료 1, 건너뜀 0, 실패 0"


def test_image_rotate_tab_skips_jpeg_when_lossless_tool_is_missing(monkeypatch):
    window = make_window(monkeypatch)
    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.detect_jpegtran",
        lambda: DependencyStatus(False),
    )
    workdir = case_dir("ui-image-rotate-jpeg-skip")
    source = workdir / "photo.jpg"
    Image.new("RGB", (8, 8), "blue").save(source, format="JPEG")

    window.image_rotate_tab.add_paths([source])
    window.image_rotate_tab.preview_rotations()

    assert window.image_rotate_tab.table.item(0, 2).text().startswith("건너뜀")
    assert not (workdir / "photo_rotated.jpg").exists()


def test_image_rotate_tab_shows_preview_for_first_image_without_selection(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-rotate-preview-panel")
    source = workdir / "sample.png"
    Image.new("RGB", (5, 3), "green").save(source)

    window.image_rotate_tab.add_paths([source])

    assert window.image_rotate_tab.preview_panel.image_label.pixmap() is not None
    assert window.image_rotate_tab.preview_panel.caption_label.text() == "sample.png | 오른쪽 90도"
    assert window.image_rotate_tab.detail_panel.value_text("file_name") == "sample.png"


def test_image_rotate_tab_direct_apply_shows_lossless_jpeg_skip(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-rotate-jpeg-imperfect")
    source = workdir / "photo.jpg"
    Image.new("RGB", (9, 9), "blue").save(source, format="JPEG")

    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.detect_jpegtran",
        lambda: DependencyStatus(True, "tools/jpegtran/jpegtran.exe"),
    )

    window.image_rotate_tab.add_paths([source])
    window.image_rotate_tab.apply_rotations()

    assert window.image_rotate_tab.table.item(0, 2).text() == "건너뜀: 무손실 회전 불가(원본 유지)"
    assert window.image_rotate_tab.status_label.text() == "처리 결과: 완료 0, 건너뜀 1, 실패 0"
    assert not (workdir / "photo_rotated.jpg").exists()


def test_image_rotate_tab_allows_lossy_jpeg_rotation_when_enabled(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-rotate-jpeg-lossy")
    source = workdir / "photo.jpg"
    Image.new("RGB", (9, 7), "blue").save(source, format="JPEG")

    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.detect_jpegtran",
        lambda: DependencyStatus(True, "tools/jpegtran/jpegtran.exe"),
    )

    window.image_rotate_tab.add_paths([source])
    assert window.image_rotate_tab.allow_lossy_jpeg_checkbox.isChecked() is False
    window.image_rotate_tab.allow_lossy_jpeg_checkbox.setChecked(True)
    window.image_rotate_tab.apply_rotations()

    target = workdir / "photo_rotated.jpg"
    assert target.exists()
    with Image.open(target) as rotated:
        assert rotated.size == (7, 9)
    assert window.image_rotate_tab.table.item(0, 2).text() == "완료: 손실 회전"


def test_image_ratio_tab_previews_reference_ratio_without_resolution_filter(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-reference")
    output_root = workdir / "sorted"
    reference = workdir / "reference.png"
    small_but_wider = workdir / "small-but-wider.png"
    same_shape = workdir / "same-shape.png"
    Image.new("RGB", (4000, 2000), "gray").save(reference)
    Image.new("RGB", (1000, 200), "blue").save(small_but_wider)
    Image.new("RGB", (2000, 1000), "green").save(same_shape)

    window.image_ratio_tab.set_output_folder(output_root)
    window.image_ratio_tab.set_reference_image(reference)
    window.image_ratio_tab.reference_multiplier_spin.setValue(1.2)
    window.image_ratio_tab.add_paths([small_but_wider, same_shape])
    window.image_ratio_tab.preview_classification()

    assert window.image_ratio_tab.reference_info_label.text() == (
        "기준 이미지: 4000 x 2000 / 기준 비율 2.00 / 현재 조건 2.40 이상"
    )
    assert window.image_ratio_tab.min_ratio_spin.isEnabled() is False
    assert window.image_ratio_tab.reference_base_ratio == 2.0
    assert window.image_ratio_tab.threshold_ratio == 2.4
    assert window.image_ratio_tab.example_widget.threshold_ratio == 2.4
    assert window.image_ratio_tab.example_widget.reference_ratio == 2.0
    assert "4000 x 2000" in window.image_ratio_tab.example_description_label.text()
    assert "가로 / 세로 >= 2.40" in window.image_ratio_tab.example_description_label.text()
    assert window.image_ratio_tab.table.item(0, 4).text() == "조건 일치"
    assert window.image_ratio_tab.table.item(1, 4).text() == "조건 미달"
    assert window.image_ratio_tab.table.item(0, 2).text() == "1000 x 200"
    assert window.image_ratio_tab.table.item(1, 2).text() == "2000 x 1000"


def test_image_ratio_tab_can_select_tall_direction(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-tall")
    tall = workdir / "tall.png"
    wide = workdir / "wide.png"
    Image.new("RGB", (200, 1000), "blue").save(tall)
    Image.new("RGB", (1000, 200), "green").save(wide)

    window.image_ratio_tab.direction_combo.setCurrentIndex(
        window.image_ratio_tab.direction_combo.findData("tall")
    )
    window.image_ratio_tab.min_ratio_spin.setValue(2.0)
    window.image_ratio_tab.add_paths([tall, wide])
    window.image_ratio_tab.preview_classification()

    assert window.image_ratio_tab.table.item(0, 4).text() == "조건 일치"
    assert window.image_ratio_tab.table.item(1, 4).text() == "조건 미달"
    assert window.image_ratio_tab.example_widget.direction == "tall"
    assert window.image_ratio_tab.example_widget.height() >= 150


def test_image_ratio_tab_add_folder_keeps_only_image_files(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-folder-images-only")
    image = workdir / "wide.png"
    log = workdir / "2026-03-04.log"
    deck = workdir / "보고서.pptx"
    Image.new("RGB", (1000, 200), "blue").save(image)
    log.write_text("log", encoding="utf-8")
    deck.write_bytes(b"pptx")

    window.image_ratio_tab.add_paths([workdir])

    assert window.image_ratio_tab.paths == [image]
    assert window.image_ratio_tab.table.rowCount() == 1
    assert window.image_ratio_tab.table.item(0, 0).text() == "wide.png"


def test_image_ratio_tab_pick_folder_keeps_only_image_files(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-pick-folder-images-only")
    image = workdir / "wide.png"
    log = workdir / "2026-03-04.log"
    Image.new("RGB", (1000, 200), "blue").save(image)
    log.write_text("log", encoding="utf-8")

    monkeypatch.setattr(
        "file_compressor_app.file_tools_ui.QFileDialog.getExistingDirectory",
        lambda *args: str(workdir),
    )

    window.image_ratio_tab.pick_folder()

    assert window.image_ratio_tab.paths == [image]
    assert window.image_ratio_tab.table.rowCount() == 1
    assert window.image_ratio_tab.table.item(0, 0).text() == "wide.png"


def test_image_ratio_tab_accepts_dropped_folder_anywhere(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-drop-folder-anywhere")
    image = workdir / "wide.png"
    log = workdir / "2026-03-04.log"
    deck = workdir / "보고서.pptx"
    Image.new("RGB", (1000, 200), "blue").save(image)
    log.write_text("log", encoding="utf-8")
    deck.write_bytes(b"pptx")

    event = FakeDropEvent([workdir])

    assert window.image_ratio_tab.acceptDrops() is True
    window.image_ratio_tab.dropEvent(event)

    assert event.accepted is True
    assert window.image_ratio_tab.paths == [image]
    assert window.image_ratio_tab.table.rowCount() == 1
    assert window.image_ratio_tab.table.item(0, 0).text() == "wide.png"


def test_image_ratio_reference_image_accepts_dropped_image(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-reference-drop")
    reference = workdir / "reference.png"
    Image.new("RGB", (1200, 300), "gray").save(reference)

    event = FakeDropEvent([reference])

    assert window.image_ratio_tab.reference_info_label.acceptDrops() is True
    window.image_ratio_tab.reference_info_label.dropEvent(event)

    assert event.accepted is True
    assert window.image_ratio_tab.reference_image == reference
    assert window.image_ratio_tab.reference_info_label.text() == (
        "기준 이미지: 1200 x 300 / 기준 비율 4.00 / 현재 조건 4.00 이상"
    )
    assert window.image_ratio_tab.min_ratio_spin.isEnabled() is False


def test_image_ratio_reference_button_accepts_dropped_image(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-image-ratio-reference-button-drop")
    reference = workdir / "reference.png"
    Image.new("RGB", (900, 300), "gray").save(reference)

    event = FakeDropEvent([reference])

    assert "드롭" in window.image_ratio_tab.reference_info_label.text()
    assert "드롭" in window.image_ratio_tab.reference_button.toolTip()
    assert window.image_ratio_tab.reference_button.acceptDrops() is True
    window.image_ratio_tab.reference_button.dropEvent(event)

    assert event.accepted is True
    assert window.image_ratio_tab.reference_image == reference
    assert window.image_ratio_tab.reference_info_label.text() == (
        "기준 이미지: 900 x 300 / 기준 비율 3.00 / 현재 조건 3.00 이상"
    )
    assert window.image_ratio_tab.min_ratio_spin.isEnabled() is False
