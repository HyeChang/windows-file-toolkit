from datetime import datetime
import os
from pathlib import Path
import shutil

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtWidgets import QApplication

from file_compressor.dependencies import DependencyStatus
from file_compressor.file_tools import get_file_timestamps, set_file_timestamps
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

    assert tab_labels(window) == ["문서 압축", "파일 이름 변경", "파일 자동 분류", "파일 날짜 변경"]

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert tab_labels(window) == ["Compression", "Rename", "Classify", "Dates"]
    assert window.rename_tab.add_files_button.text() == "Add files"
    assert window.classify_tab.output_folder_button.text() == "Select output folder"
    assert window.date_tab.add_files_button.text() == "Add files"


def test_rename_tab_previews_file_name_suffix_compact_date(monkeypatch):
    window = make_window(monkeypatch)
    workdir = case_dir("ui-rename-preview")
    source = workdir / "2026.04.27_회의록.pdf"
    source.write_bytes(b"pdf")

    window.rename_tab.add_paths([source])
    assert window.rename_tab.date_format_combo.itemText(
        window.rename_tab.date_format_combo.findData("suffix_compact")
    ) == "파일명_YYYYMMDD"
    window.rename_tab.date_format_combo.setCurrentIndex(
        window.rename_tab.date_format_combo.findData("suffix_compact")
    )
    window.rename_tab.preview_changes()

    assert window.rename_tab.table.item(0, 0).text() == source.name
    assert window.rename_tab.table.item(0, 1).text() == "회의록_20260427.pdf"
    assert window.rename_tab.table.item(0, 2).text() == "준비"


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
    assert window.classify_tab.table.item(0, 1).text() == "PDF"
    assert window.classify_tab.table.item(0, 2).text() == str(output_root / "PDF" / "보고서.pdf")
    assert window.classify_tab.table.item(1, 1).text() == "Excel"


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
    assert window.classify_tab.detail_panel.value_text("planned_path") == str(output_root / "PDF" / "보고서.pdf")
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
    target = output_root / "PDF" / "보고서.pdf"

    assert target.exists()
    assert window.classify_tab.undo_button.isEnabled() is True

    window.classify_tab.undo_last_action()

    assert source.exists()
    assert not target.exists()
    assert window.classify_tab.table.item(0, 3).text() == "되돌림"
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
