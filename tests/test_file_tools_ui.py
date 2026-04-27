import os
from pathlib import Path
import shutil

from PySide6.QtWidgets import QApplication

from file_compressor.dependencies import DependencyStatus
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


def test_main_window_separates_features_into_localized_tabs(monkeypatch):
    window = make_window(monkeypatch)

    assert tab_labels(window) == ["문서 압축", "파일 이름 변경", "파일 자동 분류"]

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert tab_labels(window) == ["Compression", "Rename", "Classify"]
    assert window.rename_tab.add_files_button.text() == "Add files"
    assert window.classify_tab.output_folder_button.text() == "Select output folder"


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
