from pathlib import Path

from PySide6.QtWidgets import QApplication

from file_compressor.models import CompressionJob, CompressionOptions
from file_compressor_app.ui import MainWindow


def app() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication([])


def test_window_default_options_are_balanced(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()

    assert window.current_options() == CompressionOptions()


def test_window_builds_options_from_advanced_controls(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()

    window.image_dimension_combo.setCurrentIndex(window.image_dimension_combo.findData(800))
    window.jpeg_quality_combo.setCurrentIndex(window.jpeg_quality_combo.findData(50))
    window.pdf_preset_combo.setCurrentIndex(window.pdf_preset_combo.findData("prepress"))

    assert window.current_options() == CompressionOptions(
        max_image_dimension=800,
        jpeg_quality=50,
        pdf_preset="prepress",
    )


def test_compress_jobs_passes_selected_options(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    source = Path(".worktrees/file-compressor-impl/.test-output/ui-options/input.pdf")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"%PDF-1.4")
    window.add_files([source])
    window.jpeg_quality_combo.setCurrentIndex(window.jpeg_quality_combo.findData(65))
    calls = []

    def fake_compress_file(path, options):
        calls.append((path, options))
        from file_compressor.models import CompressionResult, JobStatus

        return CompressionResult(status=JobStatus.SKIPPED, source=path)

    monkeypatch.setattr("file_compressor_app.ui.compress_file", fake_compress_file)

    window.compress_jobs()

    assert calls == [(source, CompressionOptions(jpeg_quality=65))]


def table_headers(window: MainWindow) -> list[str]:
    return [
        window.table.horizontalHeaderItem(index).text()
        for index in range(window.table.columnCount())
    ]


def item_text_for_data(combo, data):
    return combo.itemText(combo.findData(data))


def test_window_defaults_to_korean_language(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()

    assert window.language_combo.currentData() == "ko"
    assert window.windowTitle() == "파일 압축기"
    assert window.add_button.text() == "파일 추가"
    assert window.add_folder_button.text() == "폴더 추가"
    assert window.start_button.text() == "압축 시작"
    assert window.settings_group.title() == "고급 설정"
    assert window.language_label.text() == "언어"
    assert window.image_size_label.text() == "이미지 크기"
    assert window.jpeg_quality_label.text() == "JPEG 품질"
    assert window.pdf_level_label.text() == "PDF 수준"
    assert table_headers(window) == ["파일", "형식", "원본", "상태", "압축 후", "출력"]
    assert item_text_for_data(window.image_dimension_combo, None) == "원본"
    assert item_text_for_data(window.pdf_preset_combo, "screen") == "화면용"
    assert window.status_label.text() == "파일을 추가하세요."


def test_window_switches_visible_text_to_english(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert window.windowTitle() == "File Compressor"
    assert window.add_button.text() == "Add files"
    assert window.add_folder_button.text() == "Add folder"
    assert window.start_button.text() == "Start compression"
    assert window.settings_group.title() == "Advanced settings"
    assert window.language_label.text() == "Language"
    assert window.image_size_label.text() == "Image size"
    assert window.jpeg_quality_label.text() == "JPEG quality"
    assert window.pdf_level_label.text() == "PDF level"
    assert table_headers(window) == ["File", "Type", "Original", "Status", "Compressed", "Output"]
    assert item_text_for_data(window.image_dimension_combo, None) == "Original"
    assert item_text_for_data(window.pdf_preset_combo, "screen") == "Screen"
    assert window.status_label.text() == "Add files to start."


def test_status_column_is_localized(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    source = Path(".worktrees/file-compressor-impl/.test-output/ui-language/input.pdf")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"%PDF-1.4")

    window.add_files([source])

    assert window.table.item(0, 3).text() == "대기"
    assert window.status_label.text() == "1개 파일 준비됨."

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert window.table.item(0, 3).text() == "Pending"
    assert window.status_label.text() == "1 file(s) ready."


def test_add_folder_adds_supported_files_with_planned_outputs(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    source_root = Path(".worktrees/file-compressor-impl/.test-output/ui-folder/source")
    nested = source_root / "nested"
    nested.mkdir(parents=True, exist_ok=True)
    top = source_root / "report.xlsx"
    child = nested / "slides.ppt"
    ignored = nested / "notes.txt"
    top.write_bytes(b"xlsx")
    child.write_bytes(b"ppt")
    ignored.write_text("ignore")

    window.add_folder(source_root)

    assert len(window.jobs) == 2
    assert all(isinstance(job.compression_job, CompressionJob) for job in window.jobs)
    assert window.jobs[0].output_path == source_root.parent / "source_압축됨" / "nested" / "slides.pptx"
    assert window.jobs[1].output_path == source_root.parent / "source_압축됨" / "report.xlsx"
    assert window.table.item(0, 5).text() == str(window.jobs[0].output_path)
    assert window.status_label.text() == "2개 파일 준비됨."


def test_compress_jobs_uses_folder_compression_jobs(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    source_root = Path(".worktrees/file-compressor-impl/.test-output/ui-folder-compress/source")
    source_root.mkdir(parents=True, exist_ok=True)
    source = source_root / "report.xlsx"
    source.write_bytes(b"xlsx")
    window.add_folder(source_root)
    calls = []

    def fake_compress_file(target, options):
        calls.append((target, options))
        from file_compressor.models import CompressionResult, JobStatus

        return CompressionResult(status=JobStatus.COMPLETED, source=target.source, output=target.output)

    monkeypatch.setattr("file_compressor_app.ui.compress_file", fake_compress_file)

    window.compress_jobs()

    assert len(calls) == 1
    assert isinstance(calls[0][0], CompressionJob)
    assert calls[0][0].source == source
    assert calls[0][0].output == source_root.parent / "source_압축됨" / "report.xlsx"
