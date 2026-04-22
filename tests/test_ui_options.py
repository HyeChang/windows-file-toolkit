from pathlib import Path

from PySide6.QtWidgets import QApplication

from file_compressor.models import CompressionOptions
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
