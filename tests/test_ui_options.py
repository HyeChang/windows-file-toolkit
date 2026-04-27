from pathlib import Path

from PySide6.QtWidgets import QApplication

from file_compressor.dependencies import DependencyStatus
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
    monkeypatch.setattr(
        "file_compressor_app.ui.detect_ghostscript",
        lambda: DependencyStatus(False),
    )
    app()
    window = MainWindow()

    assert window.language_combo.currentData() == "ko"
    assert window.windowTitle() == "파일 압축기"
    assert window.add_button.text() == "파일 추가"
    assert window.add_folder_button.text() == "폴더 추가"
    assert window.output_folder_button.text() == "출력 폴더 선택"
    assert window.output_folder_label.text() == "출력 폴더: 기본 위치"
    assert window.start_button.text() == "압축 시작"
    assert window.settings_group.title() == "고급 설정"
    assert window.language_label.text() == "언어"
    assert window.image_size_label.text() == "이미지 크기"
    assert window.jpeg_quality_label.text() == "JPEG 품질"
    assert window.pdf_level_label.text() == "PDF 수준"
    assert window.tools_menu.title() == "도구"
    assert window.ghostscript_install_action.text() == "Ghostscript 설치"
    assert window.pdf_tool_status_label.text() == "PDF 압축 도구: 설치 필요"
    assert window.ghostscript_install_button.text() == "설치"
    assert window.ghostscript_install_button.isEnabled() is True
    assert window.cancel_button.text() == "취소"
    assert window.cancel_button.isEnabled() is False
    assert window.current_file_label.text() == "현재 파일: -"
    assert window.summary_label.text() == "요약: 완료 0, 건너뜀 0, 실패 0, 총 절감 - (-)"
    assert table_headers(window) == ["파일", "형식", "원본", "상태", "압축 후", "절감", "절감률", "출력"]
    assert item_text_for_data(window.image_dimension_combo, None) == "원본"
    assert item_text_for_data(window.pdf_preset_combo, "screen") == "화면용"
    assert window.status_label.text() == "파일을 추가하세요."


def test_window_switches_visible_text_to_english(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr(
        "file_compressor_app.ui.detect_ghostscript",
        lambda: DependencyStatus(False),
    )
    app()
    window = MainWindow()

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))

    assert window.windowTitle() == "File Compressor"
    assert window.add_button.text() == "Add files"
    assert window.add_folder_button.text() == "Add folder"
    assert window.output_folder_button.text() == "Select output folder"
    assert window.output_folder_label.text() == "Output folder: default location"
    assert window.start_button.text() == "Start compression"
    assert window.settings_group.title() == "Advanced settings"
    assert window.language_label.text() == "Language"
    assert window.image_size_label.text() == "Image size"
    assert window.jpeg_quality_label.text() == "JPEG quality"
    assert window.pdf_level_label.text() == "PDF level"
    assert window.tools_menu.title() == "Tools"
    assert window.ghostscript_install_action.text() == "Install Ghostscript"
    assert window.pdf_tool_status_label.text() == "PDF compression tool: install required"
    assert window.ghostscript_install_button.text() == "Install"
    assert window.cancel_button.text() == "Cancel"
    assert window.current_file_label.text() == "Current file: -"
    assert window.summary_label.text() == "Summary: completed 0, skipped 0, failed 0, saved - (-)"
    assert table_headers(window) == ["File", "Type", "Original", "Status", "Compressed", "Saved", "Rate", "Output"]
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


def test_pdf_tool_status_shows_available_when_ghostscript_exists(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr(
        "file_compressor_app.ui.detect_ghostscript",
        lambda: DependencyStatus(True, "C:/Tools/gswin64c.exe"),
    )
    app()
    window = MainWindow()

    assert window.pdf_tool_status_label.text() == "PDF 압축 도구: 사용 가능"
    assert window.ghostscript_install_button.text() == "설치됨"
    assert window.ghostscript_install_button.isEnabled() is False


def test_ghostscript_install_controls_open_download_page(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr(
        "file_compressor_app.ui.detect_ghostscript",
        lambda: DependencyStatus(False),
    )
    app()
    window = MainWindow()
    opened = []

    def fake_open_url(url):
        opened.append(url.toString())
        return True

    monkeypatch.setattr("file_compressor_app.ui.QDesktopServices.openUrl", fake_open_url)

    window.ghostscript_install_button.click()
    window.ghostscript_install_action.trigger()

    assert opened == [
        "https://ghostscript.com/releases/gsdnld.html",
        "https://ghostscript.com/releases/gsdnld.html",
    ]


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
    assert window.table.item(0, 7).text() == str(window.jobs[0].output_path)
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


def test_output_folder_plans_single_file_outputs(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    output_root = Path(".worktrees/file-compressor-impl/.test-output/ui-output-folder/out")
    output_root.mkdir(parents=True, exist_ok=True)
    source = Path(".worktrees/file-compressor-impl/.test-output/ui-output-folder/source/report.pdf")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"pdf")

    window.set_output_folder(output_root)
    window.add_files([source])

    assert window.output_folder_label.text() == f"출력 폴더: {output_root}"
    assert isinstance(window.jobs[0].compression_job, CompressionJob)
    assert window.jobs[0].output_path == output_root / "report_compressed.pdf"
    assert window.table.item(0, 7).text() == str(output_root / "report_compressed.pdf")


def test_output_folder_preserves_folder_structure(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    output_root = Path(".worktrees/file-compressor-impl/.test-output/ui-output-folder-batch/out")
    output_root.mkdir(parents=True, exist_ok=True)
    source_root = Path(".worktrees/file-compressor-impl/.test-output/ui-output-folder-batch/source")
    source = source_root / "nested" / "slides.ppt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"ppt")

    window.set_output_folder(output_root)
    window.add_folder(source_root)

    assert window.jobs[0].output_path == output_root / "nested" / "slides.pptx"


def test_output_folder_replans_pending_jobs(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    source = Path(".worktrees/file-compressor-impl/.test-output/ui-output-folder-replan/report.pdf")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"pdf")
    output_root = source.parent / "out"
    output_root.mkdir(exist_ok=True)
    window.add_files([source])

    window.set_output_folder(output_root)

    assert window.jobs[0].output_path == output_root / "report_compressed.pdf"


def test_compress_jobs_updates_progress_and_summary(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    first = Path(".worktrees/file-compressor-impl/.test-output/ui-summary/first.pdf")
    second = Path(".worktrees/file-compressor-impl/.test-output/ui-summary/second.pdf")
    first.parent.mkdir(parents=True, exist_ok=True)
    first.write_bytes(b"a" * 2000)
    second.write_bytes(b"b" * 2000)
    window.add_files([first, second])

    def fake_compress_file(path, options):
        from file_compressor.models import CompressionResult, JobStatus

        return CompressionResult(
            status=JobStatus.COMPLETED,
            source=path,
            output=path.with_name(f"{path.stem}_compressed{path.suffix}"),
            original_size=2000,
            compressed_size=1000,
        )

    monkeypatch.setattr("file_compressor_app.ui.compress_file", fake_compress_file)

    window.compress_jobs()

    assert window.progress_bar.maximum() == 2
    assert window.progress_bar.value() == 2
    assert window.current_file_label.text() == "현재 파일: -"
    assert window.table.item(0, 5).text() == "1000 B"
    assert window.table.item(0, 6).text() == "50.0%"
    assert window.summary_label.text() == "요약: 완료 2, 건너뜀 0, 실패 0, 총 절감 2.0 KB (50.0%)"


def test_cancel_button_stops_before_next_file(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app()
    window = MainWindow()
    files = []
    for index in range(3):
        source = Path(f".worktrees/file-compressor-impl/.test-output/ui-cancel/file-{index}.pdf")
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"pdf")
        files.append(source)
    window.add_files(files)
    calls = []

    def fake_compress_file(path, options):
        calls.append(path)
        window.cancel_compression()
        from file_compressor.models import CompressionResult, JobStatus

        return CompressionResult(
            status=JobStatus.COMPLETED,
            source=path,
            original_size=100,
            compressed_size=50,
        )

    monkeypatch.setattr("file_compressor_app.ui.compress_file", fake_compress_file)

    window.compress_jobs()

    assert calls == [files[0]]
    assert window.progress_bar.value() == 1
    assert window.jobs[1].status == "pending"
    assert window.status_label.text() == "압축 취소됨. 1/3개 처리됨."
